"""
ClearML manager for dataset versioning and experiment management
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from clearml import Dataset, Task, PipelineController
from config import settings

logger = logging.getLogger(__name__)


class ClearMLManager:
    """Manager for ClearML operations"""
    
    def __init__(self, project_name: str = None, dataset_name: str = None):
        self.project_name = project_name or settings.clearml_project_name
        self.dataset_name = dataset_name or settings.clearml_dataset_name
    
    def create_or_update_dataset(
        self, 
        annotations: List[Dict[str, Any]], 
        parent_dataset_id: Optional[str] = None
    ) -> Dataset:
        """Create or update dataset with new annotations"""
        
        # Get latest dataset version if parent not specified
        if parent_dataset_id is None:
            try:
                parent_dataset = Dataset.get(
                    dataset_project=self.project_name,
                    dataset_name=self.dataset_name,
                    only_completed=True
                )
                parent_dataset_id = parent_dataset.id
                logger.info(f"Found existing dataset version: {parent_dataset_id}")
            except Exception as e:
                logger.info(f"No existing dataset found, creating new one: {e}")
        
        # Create new dataset version
        dataset = Dataset.create(
            dataset_project=self.project_name,
            dataset_name=self.dataset_name,
            parent_datasets=[parent_dataset_id] if parent_dataset_id else None
        )
        
        logger.info(f"Created dataset version: {dataset.id}")
        
        # Save annotations to temporary file
        temp_annotations_file = settings.temp_dir / f"annotations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(temp_annotations_file, 'w') as f:
            json.dump(annotations, f, indent=2)
        
        # Add annotations file to dataset
        dataset.add_files(str(temp_annotations_file))
        
        # Download and add images
        for annotation in annotations:
            try:
                image_url = annotation.get('data', {}).get('image')
                if image_url:
                    # Add external files (images) to dataset
                    dataset.add_external_files(
                        source_url=image_url,
                        dataset_path=f"images/{Path(image_url).name}"
                    )
            except Exception as e:
                logger.error(f"Error adding image {image_url}: {e}")
        
        # Add metadata
        dataset.get_logger().report_text(
            f"Dataset updated with {len(annotations)} annotations from Label Studio"
        )
        
        # Finalize dataset
        dataset.upload()
        dataset.finalize()
        
        logger.info(f"Dataset finalized: {dataset.id}")
        return dataset
    
    def create_training_task(
        self, 
        dataset_id: str, 
        task_name: str = "Image Training Task",
        script_path: Optional[str] = None
    ) -> Task:
        """Create a training task using the dataset"""
        
        task = Task.init(
            project_name=self.project_name,
            task_name=task_name,
            task_type=Task.TaskTypes.training
        )
        
        # Connect the dataset to the task
        dataset = Dataset.get(dataset_id=dataset_id)
        task.connect_dataset(dataset)
        
        logger.info(f"Created training task: {task.id}")
        return task
    
    def create_pipeline(
        self, 
        pipeline_name: str = "LS2ClearML Pipeline",
        dataset_id: Optional[str] = None
    ) -> PipelineController:
        """Create a ClearML pipeline"""
        
        pipe = PipelineController(
            name=pipeline_name,
            project=self.project_name,
            version="1.0.0",
            add_pipeline_tags=True
        )
        
        pipe.set_default_execution_queue('default')
        
        # Step 1: Data preparation
        pipe.add_function_step(
            name='data_preparation',
            function=self._prepare_data_step,
            function_kwargs={'dataset_id': dataset_id},
            function_return=['dataset_path', 'num_samples'],
            cache_executed_step=True
        )
        
        # Step 2: Training
        pipe.add_function_step(
            name='training',
            function=self._training_step,
            function_kwargs={},
            parents=['data_preparation'],
            cache_executed_step=True
        )
        
        # Step 3: Evaluation
        pipe.add_function_step(
            name='evaluation',
            function=self._evaluation_step,
            function_kwargs={},
            parents=['training'],
            cache_executed_step=True
        )
        
        logger.info(f"Created pipeline: {pipeline_name}")
        return pipe
    
    @staticmethod
    def _prepare_data_step(dataset_id: str = None):
        """Data preparation step"""
        from clearml import Dataset
        
        if dataset_id:
            dataset = Dataset.get(dataset_id=dataset_id)
        else:
            dataset = Dataset.get(
                dataset_project=settings.clearml_project_name,
                dataset_name=settings.clearml_dataset_name
            )
        
        dataset_path = dataset.get_local_copy()
        
        # Count samples
        import json
        annotations_files = list(Path(dataset_path).glob('*.json'))
        num_samples = 0
        for ann_file in annotations_files:
            with open(ann_file) as f:
                data = json.load(f)
                num_samples += len(data) if isinstance(data, list) else 1
        
        return dataset_path, num_samples
    
    @staticmethod
    def _training_step():
        """Training step placeholder"""
        from clearml import Task
        
        task = Task.current_task()
        task.get_logger().report_text("Training step executed")
        
        # Placeholder for actual training logic
        # This is where you would add your model training code
        
        return "training_complete"
    
    @staticmethod
    def _evaluation_step():
        """Evaluation step placeholder"""
        from clearml import Task
        
        task = Task.current_task()
        task.get_logger().report_text("Evaluation step executed")
        
        # Placeholder for actual evaluation logic
        
        return "evaluation_complete"
    
    def run_pipeline(self, pipeline: PipelineController):
        """Execute the pipeline"""
        pipeline.start()
        logger.info("Pipeline started")
        return pipeline
