"""
Annotation Batch Manager
Accumulates annotations and creates dataset versions in batches
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set
from pathlib import Path
import json
from collections import defaultdict

from core.config import settings
from clients.clearml_manager import ClearMLManager

logger = logging.getLogger(__name__)


class AnnotationBatch:
    """Represents a batch of annotations for a project"""
    
    def __init__(self, project_id: int):
        self.project_id = project_id
        self.annotations: List[Dict[str, Any]] = []
        self.task_ids: Set[int] = set()
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.is_processing = False
    
    def add_annotation(self, annotation_data: Dict[str, Any]):
        """Add annotation to batch"""
        task_id = annotation_data.get('task', {}).get('id') or annotation_data.get('id')
        
        # Avoid duplicates
        if task_id not in self.task_ids:
            self.annotations.append(annotation_data)
            self.task_ids.add(task_id)
            self.last_updated = datetime.now()
            logger.info(f"Added annotation (task {task_id}) to batch for project {self.project_id}. Total: {len(self.annotations)}")
    
    def get_annotations(self) -> List[Dict[str, Any]]:
        """Get all annotations in batch"""
        return self.annotations.copy()
    
    def clear(self):
        """Clear the batch after processing"""
        count = len(self.annotations)
        self.annotations.clear()
        self.task_ids.clear()
        self.created_at = datetime.now()
        logger.info(f"Cleared batch for project {self.project_id}. Processed {count} annotations")
    
    def size(self) -> int:
        """Get number of annotations in batch"""
        return len(self.annotations)
    
    def age_seconds(self) -> float:
        """Get age of batch in seconds"""
        return (datetime.now() - self.created_at).total_seconds()


class AnnotationBatchManager:
    """Manages annotation batches and scheduled dataset creation"""
    
    def __init__(
        self, 
        batch_interval_minutes: int = 30,
        min_batch_size: int = 1,
        max_batch_size: int = 1000
    ):
        self.batch_interval_minutes = batch_interval_minutes
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        
        # Store batches per project
        self.batches: Dict[int, AnnotationBatch] = {}
        
        # ClearML manager
        self.clearml_manager = ClearMLManager()
        
        # Scheduler task
        self.scheduler_task: asyncio.Task = None
        self.is_running = False
        
        # Statistics
        self.stats = {
            "total_annotations_batched": 0,
            "total_datasets_created": 0,
            "last_batch_process": None,
            "next_scheduled_process": None,
            "batches_by_project": {},
        }
        
        logger.info(
            f"Batch manager initialized: interval={batch_interval_minutes}min, "
            f"min_size={min_batch_size}, max_size={max_batch_size}"
        )
    
    async def start(self):
        """Start the batch scheduler"""
        if self.is_running:
            logger.warning("Batch manager already running")
            return
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info(f"Batch scheduler started (interval: {self.batch_interval_minutes} minutes)")
    
    async def stop(self):
        """Stop the batch scheduler"""
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Process remaining batches before stopping
        await self._process_all_batches(force=True)
        
        logger.info("Batch scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop - processes batches every interval"""
        interval_seconds = self.batch_interval_minutes * 60
        
        while self.is_running:
            try:
                # Calculate next process time
                next_process = datetime.now() + timedelta(seconds=interval_seconds)
                self.stats["next_scheduled_process"] = next_process.isoformat()
                
                logger.info(f"Next batch process scheduled at {next_process.strftime('%H:%M:%S')}")
                
                # Wait for interval
                await asyncio.sleep(interval_seconds)
                
                # Process all batches
                if self.is_running:
                    await self._process_all_batches()
                    
            except asyncio.CancelledError:
                logger.info("Scheduler loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                # Continue running even on error
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    def add_annotation(self, project_id: int, annotation_data: Dict[str, Any]):
        """Add annotation to batch"""
        # Create batch if doesn't exist
        if project_id not in self.batches:
            self.batches[project_id] = AnnotationBatch(project_id)
        
        batch = self.batches[project_id]
        batch.add_annotation(annotation_data)
        
        # Update stats
        self.stats["total_annotations_batched"] += 1
        self.stats["batches_by_project"][str(project_id)] = {
            "count": batch.size(),
            "created_at": batch.created_at.isoformat(),
            "last_updated": batch.last_updated.isoformat()
        }
        
        # Auto-process if batch reaches max size
        if batch.size() >= self.max_batch_size:
            logger.info(f"Batch for project {project_id} reached max size ({self.max_batch_size}). Processing now.")
            asyncio.create_task(self.process_batch(project_id))
    
    async def process_batch(
        self, 
        project_id: int, 
        force: bool = False
    ) -> Dict[str, Any]:
        """Process a single batch and create dataset version"""
        if project_id not in self.batches:
            logger.warning(f"No batch found for project {project_id}")
            return {"status": "error", "message": "No batch found"}
        
        batch = self.batches[project_id]
        
        # Check if batch is already being processed
        if batch.is_processing:
            logger.warning(f"Batch for project {project_id} is already being processed")
            return {"status": "error", "message": "Batch already processing"}
        
        # Check if batch meets minimum size (unless forced)
        if not force and batch.size() < self.min_batch_size:
            logger.info(
                f"Batch for project {project_id} has only {batch.size()} annotations "
                f"(min: {self.min_batch_size}). Skipping."
            )
            return {"status": "skipped", "message": "Batch too small", "size": batch.size()}
        
        # Skip empty batches
        if batch.size() == 0:
            logger.info(f"Batch for project {project_id} is empty. Skipping.")
            return {"status": "skipped", "message": "Batch is empty"}
        
        try:
            batch.is_processing = True
            logger.info(f"Processing batch for project {project_id} with {batch.size()} annotations")
            
            # Get all annotations
            annotations = batch.get_annotations()
            
            # Create dataset in ClearML (run in executor to avoid blocking)
            loop = asyncio.get_event_loop()
            dataset = await loop.run_in_executor(
                None,
                self.clearml_manager.create_or_update_dataset,
                annotations,
                None
            )
            
            # Clear batch after successful processing
            batch.clear()
            
            # Update stats
            self.stats["total_datasets_created"] += 1
            self.stats["last_batch_process"] = datetime.now().isoformat()
            self.stats["batches_by_project"][str(project_id)] = {
                "count": 0,
                "created_at": batch.created_at.isoformat(),
                "last_updated": batch.last_updated.isoformat()
            }
            
            logger.info(
                f"Successfully processed batch for project {project_id}. "
                f"Dataset: {dataset.id}, Annotations: {len(annotations)}"
            )
            
            return {
                "status": "success",
                "project_id": project_id,
                "dataset_id": dataset.id,
                "annotations_count": len(annotations),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing batch for project {project_id}: {e}", exc_info=True)
            return {
                "status": "error",
                "project_id": project_id,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        finally:
            batch.is_processing = False
    
    async def _process_all_batches(self, force: bool = False):
        """Process all batches"""
        logger.info(f"Processing all batches (force={force})")
        
        if not self.batches:
            logger.info("No batches to process")
            return
        
        results = []
        for project_id in list(self.batches.keys()):
            try:
                result = await self.process_batch(project_id, force=force)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing batch for project {project_id}: {e}")
        
        # Log summary
        success_count = sum(1 for r in results if r.get("status") == "success")
        skipped_count = sum(1 for r in results if r.get("status") == "skipped")
        error_count = sum(1 for r in results if r.get("status") == "error")
        
        logger.info(
            f"Batch processing complete: {success_count} success, "
            f"{skipped_count} skipped, {error_count} errors"
        )
        
        return results
    
    async def process_all_now(self) -> List[Dict[str, Any]]:
        """Manually trigger processing of all batches (user request)"""
        logger.info("Manual batch processing triggered by user")
        return await self._process_all_batches(force=True)
    
    async def process_project_now(self, project_id: int) -> Dict[str, Any]:
        """Manually trigger processing of a specific project batch (user request)"""
        logger.info(f"Manual batch processing triggered for project {project_id}")
        return await self.process_batch(project_id, force=True)
    
    def get_batch_info(self, project_id: int = None) -> Dict[str, Any]:
        """Get information about batches"""
        if project_id is not None:
            if project_id in self.batches:
                batch = self.batches[project_id]
                return {
                    "project_id": project_id,
                    "size": batch.size(),
                    "created_at": batch.created_at.isoformat(),
                    "last_updated": batch.last_updated.isoformat(),
                    "age_seconds": batch.age_seconds(),
                    "is_processing": batch.is_processing
                }
            else:
                return {"project_id": project_id, "size": 0, "exists": False}
        else:
            # Return all batches
            return {
                "batches": {
                    pid: {
                        "size": batch.size(),
                        "created_at": batch.created_at.isoformat(),
                        "last_updated": batch.last_updated.isoformat(),
                        "age_seconds": batch.age_seconds(),
                        "is_processing": batch.is_processing
                    }
                    for pid, batch in self.batches.items()
                },
                "total_batches": len(self.batches),
                "total_annotations": sum(b.size() for b in self.batches.values())
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batch manager statistics"""
        return {
            **self.stats,
            "batch_interval_minutes": self.batch_interval_minutes,
            "min_batch_size": self.min_batch_size,
            "max_batch_size": self.max_batch_size,
            "is_running": self.is_running,
            "active_batches": len(self.batches),
            "total_pending_annotations": sum(b.size() for b in self.batches.values())
        }
