# Label Studio to ClearML Pipeline

A complete pipeline for image annotation using Label Studio with PostgreSQL, integrated with ClearML for dataset versioning, experiment management, and automated ML pipeline execution.

## Architecture

```
┌─────────────────┐
│  Label Studio   │
│  (with PostgreSQL)
└────────┬────────┘
         │ Webhook
         ▼
┌─────────────────┐
│ Webhook Server  │
│   (FastAPI)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│    ClearML      │◄─────┤   Dataset    │
│  Dataset API    │      │  Versioning  │
└────────┬────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐
│ ClearML Pipeline│
│  - Data Prep    │
│  - Training     │
│  - Evaluation   │
└─────────────────┘
```

## Features

- 🏷️ **Image Annotation**: Label Studio with PostgreSQL for robust annotation storage
- 🔄 **Automatic Sync**: Webhook-based automatic synchronization to ClearML datasets
- 📦 **Dataset Versioning**: Automatic versioning of annotated datasets in ClearML
- 🚀 **ML Pipeline**: Automated pipeline for training and evaluation
- 🔌 **Easy Integration**: Simple setup with Docker Compose

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- ClearML account (free tier available at https://clear.ml)

## Quick Start

### 1. Clone and Install Dependencies

```powershell
# Install dependencies
pip install -e .
```

### 2. Configure Environment

```powershell
# Copy the example environment file
Copy-Item .env.example .env

# Edit .env and fill in your configuration
notepad .env
```

### 3. Start Label Studio and PostgreSQL

```powershell
# Start services with Docker Compose
docker-compose up -d

# Wait for services to be ready
docker-compose ps
```

Access Label Studio at http://localhost:8080 and:
1. Create an account
2. Generate an API token (Settings → Account → Access Token)
3. Add the token to your `.env` file as `LABEL_STUDIO_API_KEY`

### 4. Configure ClearML

```powershell
# Initialize ClearML (this will prompt for credentials)
clearml-init
```

Get your ClearML credentials from: https://app.clear.ml/settings/workspace-configuration

### 5. Setup the Pipeline

```powershell
# Run the setup script
python setup_pipeline.py
```

This will:
- Verify ClearML configuration
- Create a Label Studio project for image annotation
- Setup webhook integration
- Create necessary directories

### 6. Start the Webhook Server

```powershell
# Start the webhook server
python webhook_server.py
```

Or using the main script:
```powershell
python main.py webhook
```

## Usage

### Using the CLI

The main script provides a convenient CLI interface:

```powershell
# Setup the pipeline
python main.py setup

# Start webhook server
python main.py webhook

# Run the pipeline manually
python main.py run

# Run with specific dataset
python main.py run --dataset-id <dataset-id>
```

### Annotation Workflow

1. **Upload Images**: Import images to your Label Studio project
2. **Annotate**: Create annotations using Label Studio's interface
3. **Auto-Sync**: Annotations automatically sync to ClearML via webhook
4. **Train**: Run the training pipeline with the latest dataset version

### Manual Pipeline Execution

```powershell
# Run the pipeline with the latest dataset
python run_pipeline.py

# Run with a specific dataset version
python run_pipeline.py --dataset-id <dataset-id>
```

### Example Training Script

An example training script is provided in `example_training.py`:

```powershell
python example_training.py
```

## Project Structure

```
ls2clearml_pipline/
├── main.py                  # Main CLI entry point
├── config.py                # Configuration management
├── label_studio_client.py   # Label Studio API client
├── clearml_manager.py       # ClearML dataset and pipeline manager
├── webhook_server.py        # FastAPI webhook server
├── setup_pipeline.py        # Pipeline setup script
├── run_pipeline.py          # Manual pipeline runner
├── example_training.py      # Example training script
├── docker-compose.yml       # Docker services configuration
├── .env.example             # Example environment variables
├── pyproject.toml           # Project dependencies
└── README.md                # This file
```

## Configuration

### Environment Variables

All configuration is managed through environment variables in `.env`:

#### Label Studio
- `LABEL_STUDIO_HOST`: Label Studio URL (default: http://localhost:8080)
- `LABEL_STUDIO_API_KEY`: Your Label Studio API token

#### PostgreSQL
- `POSTGRES_HOST`: Database host (default: localhost)
- `POSTGRES_PORT`: Database port (default: 5432)
- `POSTGRES_DB`: Database name (default: labelstudio)
- `POSTGRES_USER`: Database user (default: labelstudio)
- `POSTGRES_PASSWORD`: Database password

#### Webhook Server
- `WEBHOOK_HOST`: Server host (default: 0.0.0.0)
- `WEBHOOK_PORT`: Server port (default: 8000)
- `WEBHOOK_SECRET`: Optional webhook signature verification secret

#### ClearML
- `CLEARML_API_HOST`: ClearML API host
- `CLEARML_WEB_HOST`: ClearML web interface host
- `CLEARML_FILES_HOST`: ClearML files host
- `CLEARML_API_ACCESS_KEY`: Your ClearML access key
- `CLEARML_API_SECRET_KEY`: Your ClearML secret key
- `CLEARML_PROJECT_NAME`: Project name in ClearML (default: ImageAnnotation)
- `CLEARML_DATASET_NAME`: Dataset name in ClearML (default: AnnotatedImages)

## Webhook Events

The webhook server responds to these Label Studio events:

- `ANNOTATION_CREATED`: New annotation created
- `ANNOTATION_UPDATED`: Annotation modified
- `ANNOTATIONS_CREATED`: Bulk annotations created

When these events occur:
1. Webhook server receives the event
2. Exports all annotations from Label Studio
3. Creates a new dataset version in ClearML
4. Optionally triggers the training pipeline

## ClearML Pipeline Steps

The default pipeline includes three steps:

1. **Data Preparation**: 
   - Downloads dataset from ClearML
   - Counts and validates samples
   - Prepares data for training

2. **Training**:
   - Loads the prepared dataset
   - Trains the model (customize in `example_training.py`)
   - Logs metrics to ClearML

3. **Evaluation**:
   - Evaluates model performance
   - Logs evaluation metrics

## Customization

### Custom Label Configuration

Edit the label configuration in `label_studio_client.py`:

```python
def create_image_annotation_project(self, project_name: str):
    label_config = """
    <View>
      <Image name="image" value="$image"/>
      <RectangleLabels name="label" toName="image">
        <Label value="YourLabel1" background="green"/>
        <Label value="YourLabel2" background="blue"/>
      </RectangleLabels>
    </View>
    """
```

### Custom Training Logic

Replace the placeholder training code in `example_training.py` with your actual model training logic.

### Custom Pipeline Steps

Modify the pipeline steps in `clearml_manager.py`:

```python
def create_pipeline(self, ...):
    # Add custom steps
    pipe.add_function_step(
        name='your_custom_step',
        function=your_custom_function,
        parents=['previous_step']
    )
```

## Troubleshooting

### Label Studio Connection Issues

```powershell
# Check if Label Studio is running
docker-compose ps

# View Label Studio logs
docker-compose logs label-studio

# Restart services
docker-compose restart
```

### ClearML Configuration Issues

```powershell
# Reconfigure ClearML
clearml-init

# Verify configuration
python -c "from clearml import Task; Task.init(project_name='test', task_name='test')"
```

### Webhook Not Receiving Events

1. Check webhook server is running
2. Verify webhook URL in Label Studio project settings
3. Check firewall settings
4. For Docker: use `http://host.docker.internal:8000` as webhook URL

## Monitoring

### ClearML Dashboard
Monitor your experiments at: https://app.clear.ml

### Webhook Server Logs
```powershell
# View webhook server output
python webhook_server.py
```

### Dataset Versions
View dataset versions in ClearML web interface under your project.

## Docker Commands

```powershell
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart label-studio

# Remove all data (⚠️ destructive)
docker-compose down -v
```

## License

MIT License

## Support

For issues and questions:
- ClearML: https://github.com/allegroai/clearml
- Label Studio: https://github.com/heartexlabs/label-studio
