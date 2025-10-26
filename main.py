"""
Main entry point for Label Studio to ClearML Pipeline
"""
import argparse
import logging

from services.webhook_server_optimized import main as run_server
from pipelines.setup_pipeline import main as setup_main
from pipelines.run_pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point with CLI"""
    parser = argparse.ArgumentParser(
        description="Label Studio to ClearML Pipeline Manager"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    subparsers.add_parser('setup', help='Setup the pipeline')
    
    # Webhook server command
    subparsers.add_parser('webhook', help='Start the webhook server')
    
    # Run pipeline command
    run_parser = subparsers.add_parser('run', help='Run the ClearML pipeline')
    run_parser.add_argument(
        '--dataset-id',
        type=str,
        help='Specific dataset ID to use'
    )
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        setup_main()
    elif args.command == 'webhook':
        run_server()
    elif args.command == 'run':
        run_pipeline(dataset_id=args.dataset_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
