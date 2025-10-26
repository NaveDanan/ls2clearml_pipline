"""
FastAPI webhook server to receive Label Studio events
"""
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import hmac
import hashlib

from config import settings
from label_studio_client import LabelStudioClient
from clearml_manager import ClearMLManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Label Studio to ClearML Webhook")

# Initialize clients
ls_client = LabelStudioClient()
clearml_manager = ClearMLManager()


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature if secret is configured"""
    if not settings.webhook_secret:
        return True
    
    expected_signature = hmac.new(
        settings.webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


async def process_annotation_update(project_id: int, action: str):
    """Process annotation update in background"""
    try:
        logger.info(f"Processing annotation update for project {project_id}, action: {action}")
        
        # Get all annotations from Label Studio
        annotations = ls_client.export_annotations(project_id)
        
        logger.info(f"Retrieved {len(annotations)} annotations from Label Studio")
        
        # Update ClearML dataset
        dataset = clearml_manager.create_or_update_dataset(annotations)
        
        logger.info(f"Updated ClearML dataset: {dataset.id}")
        
        # Optionally trigger pipeline execution
        # pipeline = clearml_manager.create_pipeline(dataset_id=dataset.id)
        # clearml_manager.run_pipeline(pipeline)
        
    except Exception as e:
        logger.error(f"Error processing annotation update: {e}", exc_info=True)


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
        
        # Verify signature if configured
        signature = request.headers.get("X-Label-Studio-Signature", "")
        if not verify_webhook_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse JSON payload
        payload = await request.json()
        
        logger.info(f"Received webhook: {payload.get('action', 'UNKNOWN')}")
        
        # Extract event details
        action = payload.get("action")
        project_id = payload.get("project", {}).get("id")
        
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
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Label Studio to ClearML Webhook Server",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook/label-studio",
            "health": "/health"
        }
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
