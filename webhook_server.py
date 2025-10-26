"""
FastAPI webhook server to receive Label Studio events
"""
import logging
import asyncio
from typing import Dict, Any, Set
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import hmac
import hashlib
from datetime import datetime
import json

from config import settings
from label_studio_client import LabelStudioClient
from clearml_manager import ClearMLManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Label Studio to ClearML Webhook")

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
}

# Store recent events
recent_events = []
max_events = 50

# WebSocket connections
active_connections: Set[WebSocket] = set()

# Current pipeline step
current_step = {
    "step": "idle",
    "message": "Waiting for events...",
    "timestamp": None
}

# Initialize clients
ls_client = LabelStudioClient()
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
    
    event = {
        "type": "step_update",
        "data": {
            **current_step,
            "status": status
        }
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


async def process_annotation_update(project_id: int, action: str):
    """Process annotation update in background"""
    try:
        await update_step("webhook_received", f"Received {action} event for project {project_id}", "processing")
        
        logger.info(f"Processing annotation update for project {project_id}, action: {action}")
        
        # Step 1: Fetch annotations
        await update_step("fetching_annotations", f"Fetching annotations from Label Studio...", "processing")
        annotations = ls_client.export_annotations(project_id)
        
        await log_event("annotations_fetched", {
            "project_id": project_id,
            "count": len(annotations),
            "action": action
        })
        
        logger.info(f"Retrieved {len(annotations)} annotations from Label Studio")
        
        # Update global stats
        stats["total_annotations"] = len(annotations)
        stats["last_sync"] = datetime.now().isoformat()
        
        # Step 2: Create dataset
        await update_step("creating_dataset", f"Creating dataset version in ClearML...", "processing")
        dataset = clearml_manager.create_or_update_dataset(annotations)
        
        await log_event("dataset_created", {
            "dataset_id": dataset.id,
            "version": f"v{dataset.id[:8]}",
            "annotations_count": len(annotations)
        })
        
        logger.info(f"Updated ClearML dataset: {dataset.id}")
        
        # Update dataset version in stats
        stats["dataset_version"] = f"v{dataset.id[:8]}"
        
        # Step 3: Complete
        await update_step("completed", f"Pipeline completed successfully!", "success")
        
        # Broadcast stats update
        await broadcast_event({
            "type": "stats_update",
            "data": stats
        })
        
        # Reset to idle after 3 seconds
        await asyncio.sleep(3)
        await update_step("idle", "Waiting for events...", "idle")
        
    except Exception as e:
        logger.error(f"Error processing annotation update: {e}", exc_info=True)
        await update_step("error", f"Error: {str(e)}", "error")
        await log_event("error", {
            "message": str(e),
            "project_id": project_id,
            "action": action
        })


@app.post("/webhook/label-studio")
async def label_studio_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Webhook endpoint to receive Label Studio events
    
    Label Studio webhook events:
    - ANNOTATION_CREATED
    - ANNOTATION_UPDATED
    - ANNOTATION_DELETED
    - TASK_CREATED
    - PROJECT_UPDATED
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
        
        # Update active webhooks count
        stats["active_webhooks"] = stats.get("active_webhooks", 0) + 1
        
        # Process annotation events
        if action in ["ANNOTATION_CREATED", "ANNOTATION_UPDATED", "ANNOTATIONS_CREATED"]:
            if project_id:
                # Process in background to not block webhook response
                background_tasks.add_task(process_annotation_update, project_id, action)
            else:
                logger.warning("Received annotation event without project ID")
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "Webhook received"}
        )
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        await log_event("webhook_error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.add(websocket)
    
    logger.info(f"WebSocket client connected. Total connections: {len(active_connections)}")
    
    # Send current state
    try:
        await websocket.send_text(json.dumps({
            "type": "initial_state",
            "data": {
                "stats": stats,
                "current_step": current_step,
                "recent_events": recent_events[:10]
            }
        }))
        
        # Keep connection alive
        while True:
            try:
                # Wait for messages (ping/pong)
                data = await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    finally:
        active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(active_connections)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/stats")
async def get_stats():
    """Get pipeline statistics"""
    return stats


@app.get("/events")
async def get_events():
    """Get recent events"""
    return {"events": recent_events[:20]}


@app.get("/current-step")
async def get_current_step():
    """Get current pipeline step"""
    return current_step


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Label Studio to ClearML Webhook Server",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook/label-studio",
            "websocket": "/ws",
            "health": "/health",
            "stats": "/stats",
            "events": "/events",
            "current_step": "/current-step"
        },
        "active_connections": len(active_connections)
    }


def run_server():
    """Run the webhook server"""
    logger.info(f"Starting webhook server on {settings.webhook_host}:{settings.webhook_port}")
    uvicorn.run(
        app,
        host=settings.webhook_host,
        port=settings.webhook_port,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
