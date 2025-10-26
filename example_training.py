"""
Example training script that can be integrated with the pipeline
This is a template that you can customize for your specific use case
"""
import logging
from pathlib import Path
import json
from typing import Dict, Any

from clearml import Task, Dataset
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_annotations(dataset_path: str) -> list:
    """Load annotations from dataset"""
    annotations = []
    dataset_dir = Path(dataset_path)
    
    for json_file in dataset_dir.glob("*.json"):
        with open(json_file) as f:
            data = json.load(f)
            if isinstance(data, list):
                annotations.extend(data)
            else:
                annotations.append(data)
    
    return annotations


def prepare_dataset(annotations: list) -> Dict[str, Any]:
    """Prepare dataset for training"""
    logger.info(f"Preparing dataset with {len(annotations)} annotations")
    
    # Count labels
    label_counts = {}
    total_objects = 0
    
    for ann in annotations:
        for annotation in ann.get('annotations', []):
            for result in annotation.get('result', []):
                if result.get('type') == 'rectanglelabels':
                    for label in result.get('value', {}).get('rectanglelabels', []):
                        label_counts[label] = label_counts.get(label, 0) + 1
                        total_objects += 1
    
    stats = {
        'num_images': len(annotations),
        'num_objects': total_objects,
        'label_distribution': label_counts
    }
    
    logger.info(f"Dataset statistics: {stats}")
    return stats


def train_model(dataset_stats: Dict[str, Any]):
    """
    Placeholder for actual training logic
    Replace this with your actual model training code
    """
    logger.info("Starting model training...")
    
    # This is where you would:
    # 1. Load your model architecture
    # 2. Load the training data
    # 3. Train the model
    # 4. Save checkpoints
    # 5. Log metrics to ClearML
    
    # Example: Log some dummy metrics
    task = Task.current_task()
    
    for epoch in range(10):
        # Dummy training metrics
        loss = 1.0 / (epoch + 1)
        accuracy = 0.5 + (epoch * 0.05)
        
        task.get_logger().report_scalar(
            title="Training",
            series="Loss",
            value=loss,
            iteration=epoch
        )
        
        task.get_logger().report_scalar(
            title="Training",
            series="Accuracy",
            value=accuracy,
            iteration=epoch
        )
    
    logger.info("Model training completed")


def main():
    """Main training function"""
    # Initialize ClearML task
    task = Task.init(
        project_name=settings.clearml_project_name,
        task_name="Image Training Example",
        task_type=Task.TaskTypes.training
    )
    
    # Get the latest dataset
    try:
        dataset = Dataset.get(
            dataset_project=settings.clearml_project_name,
            dataset_name=settings.clearml_dataset_name,
            only_completed=True
        )
        
        logger.info(f"Using dataset: {dataset.id}")
        dataset_path = dataset.get_local_copy()
        
        # Load and prepare data
        annotations = load_annotations(dataset_path)
        dataset_stats = prepare_dataset(annotations)
        
        # Log dataset stats
        task.connect(dataset_stats)
        
        # Train model
        train_model(dataset_stats)
        
        logger.info("Training completed successfully")
        
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
