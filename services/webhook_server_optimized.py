"""
Optimized webhook server with async processing and task queuing
"""
import logging
import asyncio
from typing import Dict, Any, Set
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import hmac
import hashlib
from datetime import datetime
import json
from pathlib import Path

from core.config import settings
from clients.async_label_studio_client import AsyncLabelStudioClient
from clients.clearml_manager import ClearMLManager
from services.task_queue import get_task_queue, TaskQueueManager
from services.annotation_batch_manager import AnnotationBatchManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Label Studio to ClearML Webhook - Optimized")

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global stats and events
stats = {
    "total_annotations": 0,
    "dataset_version": "0.0.0",
    "last_sync": None,
    "active_webhooks": 0,
    "tasks_queued": 0,
    "tasks_completed": 0,
    "tasks_failed": 0,
}

# Store recent events
recent_events = []
max_events = 100

# WebSocket connections
active_connections: Set[WebSocket] = set()

# Current pipeline step
current_step = {
    "step": "idle",
    "message": "Waiting for events...",
    "timestamp": None,
    "status": "idle"
}

# Task queue
task_queue: TaskQueueManager = None

# Batch annotation manager
batch_manager: AnnotationBatchManager = None

# Initialize ClearML manager
clearml_manager = ClearMLManager()


async def broadcast_event(event: Dict[str, Any]):
    """Broadcast event to all connected WebSocket clients"""
    message = json.dumps(event)
    disconnected = set()
    
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            logger.error(f"Error broadcasting to client: {e}")
            disconnected.add(connection)
    
    # Remove disconnected clients
    active_connections.difference_update(disconnected)


async def update_step(step: str, message: str, status: str = "processing"):
    """Update current pipeline step and broadcast to clients"""
    current_step["step"] = step
    current_step["message"] = message
    current_step["timestamp"] = datetime.now().isoformat()
    current_step["status"] = status
    
    event = {
        "type": "step_update",
        "data": current_step.copy()
    }
    
    await broadcast_event(event)
    logger.info(f"Step: {step} - {message}")


async def log_event(event_type: str, data: Dict[str, Any]):
    """Log event and broadcast to clients"""
    event = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add to recent events
    recent_events.insert(0, event)
    if len(recent_events) > max_events:
        recent_events.pop()
    
    # Broadcast to WebSocket clients
    await broadcast_event(event)


async def update_stats_broadcast():
    """Broadcast stats update to clients"""
    event = {
        "type": "stats_update",
        "data": stats.copy()
    }
    await broadcast_event(event)
    
    # Also broadcast queue stats (for optimized server)
    if task_queue:
        queue_stats = await task_queue.get_stats()  # Add await here!
        queue_event = {
            "type": "queue_stats_update",
            "data": queue_stats
        }
        await broadcast_event(queue_event)
    
    # Also broadcast batch stats
    if batch_manager:
        batch_stats = batch_manager.get_stats()
        batch_event = {
            "type": "batch_stats_update",
            "data": batch_stats
        }
        await broadcast_event(batch_event)


# Task handlers
async def process_annotation_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process annotation update asynchronously - adds to batch"""
    project_id = payload.get("project_id")
    action = payload.get("action")
    
    try:
        await update_step("webhook_received", f"Processing {action} for project {project_id}", "processing")
        
        logger.info(f"Processing annotation update for project {project_id}, action: {action}")
        
        # Step 1: Fetch annotations using async client
        await update_step("fetching_annotations", "Fetching annotations from Label Studio...", "processing")
        
        async with AsyncLabelStudioClient() as ls_client:
            # Fetch annotations concurrently with project info
            annotations_task = ls_client.export_annotations(project_id)
            project_task = ls_client.get_project(project_id)
            
            # Wait for both in parallel
            annotations, project_info = await asyncio.gather(
                annotations_task,
                project_task,
                return_exceptions=True
            )
            
            if isinstance(annotations, Exception):
                raise annotations
            if isinstance(project_info, Exception):
                logger.warning(f"Failed to fetch project info: {project_info}")
                project_info = {}
        
        await log_event("annotations_fetched", {
            "project_id": project_id,
            "count": len(annotations),
            "action": action
        })
        
        logger.info(f"Retrieved {len(annotations)} annotations from Label Studio")
        
        # Update global stats
        stats["total_annotations"] += len(annotations)
        stats["last_sync"] = datetime.now().isoformat()
        
        # Step 2: Add annotations to batch (instead of immediate dataset creation)
        await update_step("batching_annotations", f"Adding {len(annotations)} annotations to batch...", "processing")
        
        # Add each annotation to the batch
        for annotation in annotations:
            batch_manager.add_annotation(project_id, annotation)
        
        # Get batch info
        batch_info = batch_manager.get_batch_info(project_id)
        
        await log_event("annotations_batched", {
            "project_id": project_id,
            "annotations_added": len(annotations),
            "batch_size": batch_info.get("size", 0),
            "action": action
        })
        
        logger.info(
            f"Added {len(annotations)} annotations to batch for project {project_id}. "
            f"Current batch size: {batch_info.get('size', 0)}"
        )
        
        # Update stats
        stats["active_webhooks"] = max(0, stats.get("active_webhooks", 1) - 1)
        stats["tasks_completed"] = stats.get("tasks_completed", 0) + 1
        
        await update_stats_broadcast()
        await update_step(
            "batched", 
            f"Annotations batched. Batch size: {batch_info.get('size', 0)}. "
            f"Next dataset creation scheduled.",
            "success"
        )
        
        # Wait a bit then reset to idle
        await asyncio.sleep(2)
        await update_step("idle", "Waiting for events...", "idle")
        
        return {
            "status": "success",
            "annotations_batched": len(annotations),
            "batch_size": batch_info.get("size", 0),
            "project_id": project_id
        }
        
    except Exception as e:
        error_msg = f"Error processing annotation update: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        stats["active_webhooks"] = max(0, stats.get("active_webhooks", 1) - 1)
        stats["tasks_failed"] = stats.get("tasks_failed", 0) + 1
        
        await log_event("processing_error", {
            "error": str(e),
            "project_id": project_id,
            "action": action
        })
        
        await update_step("error", f"Pipeline failed: {str(e)}", "error")
        await update_stats_broadcast()
        
        # Wait a bit then reset to idle
        await asyncio.sleep(3)
        await update_step("idle", "Waiting for events...", "idle")
        
        raise


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature if secret is configured"""
    # Skip validation if secret is not set or is a placeholder
    if not settings.webhook_secret or settings.webhook_secret == "your_webhook_secret_here":
        logger.info("Webhook signature validation disabled (no secret configured)")
        return True
    
    # Skip validation if no signature provided
    if not signature:
        logger.warning("No webhook signature provided, but secret is configured. Allowing anyway.")
        return True
    
    expected_signature = hmac.new(
        settings.webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    is_valid = hmac.compare_digest(signature, expected_signature)
    if not is_valid:
        logger.warning(f"Invalid signature. Expected: {expected_signature[:10]}..., Got: {signature[:10]}...")
    
    return is_valid


@app.on_event("startup")
async def startup_event():
    """Initialize task queue and batch manager on startup"""
    global task_queue, batch_manager
    
    # Initialize batch manager (30-minute intervals, min 1 annotation)
    batch_manager = AnnotationBatchManager(
        batch_interval_minutes=30,  # Create datasets every 30 minutes
        min_batch_size=1,            # Process even single annotations
        max_batch_size=1000          # Auto-process if batch reaches 1000
    )
    await batch_manager.start()
    
    # Check if Redis is available and configured
    redis_url = settings.webhook_secret if hasattr(settings, 'redis_url') else None
    use_redis = False  # Set to True if you want to use Redis
    
    task_queue = get_task_queue(use_redis=use_redis, redis_url=redis_url)
    
    # Register task handlers
    task_queue.register_handler("process_annotation", process_annotation_task)
    
    # Start workers (3 concurrent workers for parallel processing)
    await task_queue.start(num_workers=3)
    
    logger.info(
        "Webhook server started with optimized async processing and batch annotation system "
        f"(interval: {batch_manager.batch_interval_minutes} minutes)"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global task_queue, batch_manager
    
    # Stop batch manager (will process remaining batches)
    if batch_manager:
        await batch_manager.stop()
    
    if task_queue:
        await task_queue.stop()
    
    logger.info("Webhook server shutdown complete")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    queue_stats = await task_queue.get_stats() if task_queue else {}
    batch_stats = batch_manager.get_stats() if batch_manager else {}
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "stats": stats,
        "queue": queue_stats,
        "batch": batch_stats,
        "websocket_connections": len(active_connections)
    }


@app.get("/stats")
async def get_stats():
    """Get current statistics"""
    queue_stats = await task_queue.get_stats() if task_queue else {}
    batch_stats = batch_manager.get_stats() if batch_manager else {}
    batch_info = batch_manager.get_batch_info() if batch_manager else {}
    
    return {
        "pipeline_stats": stats,
        "batch_stats": batch_stats,
        "batch_info": batch_info,
        "queue_stats": queue_stats,
        "websocket_connections": len(active_connections),
        "recent_events_count": len(recent_events)
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"WebSocket client connected. Total connections: {len(active_connections)}")
    
    try:
        # Send initial state
        queue_stats = await task_queue.get_stats() if task_queue else {}
        batch_stats = batch_manager.get_stats() if batch_manager else {}
        initial_data = {
            "type": "initial_state",
            "data": {
                "stats": stats,
                "current_step": current_step,
                "recent_events": recent_events[:20],
                "queue_stats": queue_stats,
                "batch_stats": batch_stats
            }
        }
        await websocket.send_text(json.dumps(initial_data))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                # Handle ping/pong or other client messages if needed
                logger.debug(f"Received from client: {data}")
            except WebSocketDisconnect:
                break
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(active_connections)}")


@app.post("/webhook/label-studio")
async def label_studio_webhook(request: Request):
    """
    Webhook endpoint to receive Label Studio events - Optimized with task queuing
    """
    try:
        # Get request body
        body = await request.body()
        
        # Log request details for debugging
        logger.info(f"Webhook received - Headers: {dict(request.headers)}")
        
        # Verify signature if configured
        signature = request.headers.get("X-Label-Studio-Signature", "")
        if not verify_webhook_signature(body, signature):
            error_msg = "Invalid webhook signature"
            logger.error(error_msg)
            await log_event("webhook_error", {"error": f"401: {error_msg}"})
            raise HTTPException(status_code=401, detail=error_msg)
        
        # Parse JSON payload
        payload = await request.json()
        
        logger.info(f"Received webhook: {payload.get('action', 'UNKNOWN')}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Log webhook received
        await log_event("webhook_received", {
            "action": payload.get("action"),
            "project_id": payload.get("project", {}).get("id")
        })
        
        # Extract event details
        action = payload.get("action")
        project_id = payload.get("project", {}).get("id")
        
        # Process annotation events asynchronously via task queue
        if action in ["ANNOTATION_CREATED", "ANNOTATION_UPDATED", "ANNOTATIONS_CREATED"]:
            if project_id:
                # Submit task to queue for async processing
                task_id = await task_queue.submit_task(
                    task_type="process_annotation",
                    payload={
                        "project_id": project_id,
                        "action": action,
                        "full_payload": payload
                    },
                    priority=5  # Higher priority for annotation events
                )
                
                stats["active_webhooks"] = stats.get("active_webhooks", 0) + 1
                stats["tasks_queued"] = stats.get("tasks_queued", 0) + 1
                
                logger.info(f"Submitted task {task_id} to queue (priority: 5)")
                
                return JSONResponse(
                    content={
                        "status": "accepted",
                        "message": "Webhook received and queued for processing",
                        "task_id": task_id
                    },
                    status_code=202
                )
            else:
                logger.warning("Received annotation event without project ID")
                return JSONResponse(
                    content={"status": "ignored", "message": "No project ID provided"},
                    status_code=200
                )
        
        return JSONResponse(
            content={"status": "received", "action": action},
            status_code=200
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        await log_event("webhook_error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/batch/process-all")
async def process_all_batches():
    """Manually trigger processing of all annotation batches"""
    if not batch_manager:
        raise HTTPException(status_code=503, detail="Batch manager not initialized")
    
    try:
        logger.info("Manual batch processing triggered via API for all projects")
        results = await batch_manager.process_all_now()
        
        return {
            "status": "success",
            "message": "All batches processed",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing batches: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch/process/{project_id}")
async def process_project_batch(project_id: int):
    """Manually trigger processing of a specific project's annotation batch"""
    if not batch_manager:
        raise HTTPException(status_code=503, detail="Batch manager not initialized")
    
    try:
        logger.info(f"Manual batch processing triggered via API for project {project_id}")
        result = await batch_manager.process_project_now(project_id)
        
        return {
            "status": "success",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing batch for project {project_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/batch/info")
async def get_batch_info(project_id: int = None):
    """Get information about annotation batches"""
    if not batch_manager:
        raise HTTPException(status_code=503, detail="Batch manager not initialized")
    
    try:
        info = batch_manager.get_batch_info(project_id)
        return {
            "status": "success",
            "info": info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting batch info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error processing webhook: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        await log_event("webhook_error", {"error": f"500: {error_msg}"})
        
        raise HTTPException(status_code=500, detail=error_msg)


def main():
    """Run the webhook server"""
    logger.info(f"Starting optimized webhook server on {settings.webhook_host}:{settings.webhook_port}")
    uvicorn.run(
        app,
        host=settings.webhook_host,
        port=settings.webhook_port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
