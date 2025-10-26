"""
Setup script to initialize the Label Studio to ClearML pipeline
"""
import logging
import sys
from pathlib import Path

from core.config import settings
from clients.label_studio_client import LabelStudioClient
from clients.clearml_manager import ClearMLManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_clearml():
    """Initialize ClearML configuration"""
    logger.info("Setting up ClearML configuration...")
    
    try:
        from clearml import Task
        
        # Try to create a test task to verify configuration
        task = Task.init(
            project_name=settings.clearml_project_name,
            task_name="Pipeline Setup Test",
            task_type=Task.TaskTypes.data_processing
        )
        task.close()
        logger.info("✓ ClearML configuration successful")
        return True
    except Exception as e:
        logger.error(f"✗ ClearML configuration failed: {e}")
        logger.info("\nPlease run 'clearml-init' to configure ClearML credentials")
        return False


def setup_label_studio_project():
    """Create or verify Label Studio project"""
    logger.info("Setting up Label Studio project...")
    
    try:
        ls_client = LabelStudioClient()
        
        # Check if project exists
        projects = ls_client.get_projects()
        
        # Debug: Check what we got back
        if isinstance(projects, str):
            logger.error(f"✗ Label Studio returned a string instead of JSON: {projects[:200]}")
            logger.info("\nThis usually means Label Studio is not running or not properly configured.")
            return None
        
        if not isinstance(projects, list):
            logger.error(f"✗ Unexpected response type: {type(projects)}")
            return None
        
        project = None
        for proj in projects:
            if proj['title'] == settings.clearml_project_name:
                project = proj
                logger.info(f"✓ Found existing project: {proj['title']} (ID: {proj['id']})")
                break
        
        # Create project if not exists
        if not project:
            project = ls_client.create_image_annotation_project(settings.clearml_project_name)
            logger.info(f"✓ Created new project: {project['title']} (ID: {project['id']})")
        
        return project
    except Exception as e:
        logger.error(f"✗ Label Studio setup failed: {e}", exc_info=True)
        logger.info("\nPlease ensure:")
        logger.info("1. Label Studio is running (docker-compose up -d)")
        logger.info("2. LABEL_STUDIO_API_KEY is set in .env file")
        return None


def setup_webhook(project_id: int):
    """Setup webhook for Label Studio project"""
    logger.info("Setting up webhook...")
    
    try:
        ls_client = LabelStudioClient()
        
        # Construct webhook URL
        webhook_url = f"http://host.docker.internal:{settings.webhook_port}/webhook/label-studio"
        
        # Check existing webhooks
        webhooks = ls_client.get_webhooks(project_id)
        webhook_exists = any(wh['url'] == webhook_url for wh in webhooks)
        
        if webhook_exists:
            logger.info(f"✓ Webhook already exists: {webhook_url}")
        else:
            webhook = ls_client.setup_webhook(project_id, webhook_url)
            logger.info(f"✓ Webhook created: {webhook_url}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Webhook setup failed: {e}")
        return False


def verify_environment():
    """Verify environment configuration"""
    logger.info("Verifying environment configuration...")
    
    issues = []
    
    # Check ClearML credentials
    if not settings.clearml_api_access_key or not settings.clearml_api_secret_key:
        issues.append("ClearML API credentials not set (run clearml-init)")
    
    # Check Label Studio API key
    if not settings.label_studio_api_key:
        issues.append("Label Studio API key not set in .env file")
    
    # Check directories
    if not settings.data_dir.exists():
        settings.data_dir.mkdir(parents=True, exist_ok=True)
    
    if not settings.temp_dir.exists():
        settings.temp_dir.mkdir(parents=True, exist_ok=True)
    
    if issues:
        logger.warning("⚠ Configuration issues found:")
        for issue in issues:
            logger.warning(f"  - {issue}")
        return False
    
    logger.info("✓ Environment configuration OK")
    return True


def main():
    """Main setup function"""
    logger.info("=" * 60)
    logger.info("Label Studio to ClearML Pipeline Setup")
    logger.info("=" * 60)
    
    # Verify environment
    if not verify_environment():
        logger.warning("\nPlease fix configuration issues and run setup again")
    
    # Setup ClearML
    clearml_ok = setup_clearml()
    
    # Setup Label Studio project
    project = setup_label_studio_project()
    
    # Setup webhook if project exists
    if project:
        setup_webhook(project['id'])
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Setup Summary")
    logger.info("=" * 60)
    logger.info(f"ClearML: {'✓ OK' if clearml_ok else '✗ Failed'}")
    logger.info(f"Label Studio: {'✓ OK' if project else '✗ Failed'}")
    logger.info(f"Webhook: {'✓ OK' if project else '✗ Failed'}")
    
    if clearml_ok and project:
        logger.info("\n✓ Pipeline setup complete!")
        logger.info("\nNext steps:")
        logger.info("1. Start the webhook server: python webhook_server.py")
        logger.info("2. Start annotating in Label Studio")
        logger.info("3. Annotations will automatically sync to ClearML")
    else:
        logger.info("\n✗ Pipeline setup incomplete")
        logger.info("Please fix the issues above and run setup again")
        sys.exit(1)


if __name__ == "__main__":
    main()
