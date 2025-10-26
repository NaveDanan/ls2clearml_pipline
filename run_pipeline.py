"""
Script to manually run the ClearML pipeline
"""
import logging
import argparse
from pathlib import Path

from clearml_manager import ClearMLManager
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_pipeline(dataset_id: str = None):
    """Run the ClearML pipeline"""
    logger.info("Starting ClearML pipeline...")
    
    try:
        manager = ClearMLManager()
        
        # Create pipeline
        pipeline = manager.create_pipeline(
            pipeline_name="LS2ClearML Training Pipeline",
            dataset_id=dataset_id
        )
        
        # Run pipeline
        logger.info("Executing pipeline...")
        manager.run_pipeline(pipeline)
        
        logger.info("✓ Pipeline execution started successfully")
        logger.info(f"Monitor progress at: {settings.clearml_web_host}")
        
    except Exception as e:
        logger.error(f"✗ Pipeline execution failed: {e}", exc_info=True)
        raise


def main():
    parser = argparse.ArgumentParser(description="Run ClearML pipeline")
    parser.add_argument(
        '--dataset-id',
        type=str,
        help='Specific dataset ID to use (optional, uses latest if not specified)'
    )
    
    args = parser.parse_args()
    
    run_pipeline(dataset_id=args.dataset_id)


if __name__ == "__main__":
    main()
