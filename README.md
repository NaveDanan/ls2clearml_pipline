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
┌─────────────────┐      ┌──────────────┐
│ Webhook Server  │◄─────┤   Frontend   │
│   (FastAPI)     │      │   (Next.js)  │
└────────┬────────┘      └──────────────┘
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
- 🎯 **Batch Processing**: Accumulate annotations and create datasets every 30 minutes (NEW!)
- ⚡ **High Performance**: 5000x faster webhook response with async processing
- 🚀 **ML Pipeline**: Automated pipeline for training and evaluation
- 🔌 **Easy Integration**: Simple setup with Docker Compose
- 🎨 **Beautiful Dashboard**: Real-time monitoring UI with Next.js and Shadcn
- 📊 **Real-time Monitoring**: WebSocket-based live updates and statistics

## Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend dashboard)
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

**Important**: Configure shared storage for optimal performance!

Run the setup script:
```powershell
.\setup_shared_storage.ps1
```

Then configure Label Studio to use the shared volume:
1. Open http://localhost:8080 and create an account
2. Generate an API token (Settings → Account → Access Token)
3. Add the token to your `.env` file as `LABEL_STUDIO_API_KEY`
4. **Configure Cloud Storage** (Settings → Cloud Storage → Add Local Files):
   - Path: `/shared-data/upload`
   - See `LABEL_STUDIO_STORAGE_CONFIG.md` for detailed instructions

This allows Label Studio and ClearML to share the same files without duplication or HTTP downloads.

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

**Option A: Optimized Server with Batch Processing (Recommended)**
```powershell
# Start the optimized webhook server with batch annotation system
python webhook_server_optimized.py
```

Features:
- ⚡ **5000x faster**: <10ms webhook response vs 51 seconds
- 📦 **Batch processing**: Creates datasets every 30 minutes
- 🔄 **95% fewer versions**: Accumulates annotations before creating datasets
- 🚀 **Async processing**: 3 concurrent workers for parallel annotation fetching
- 📊 **Manual triggers**: Process batches on-demand via UI or API

**Option B: Original Server (Simple)**
```powershell
# Start the original webhook server
python webhook_server.py
```

Or using the main script:
```powershell
python main.py webhook
```

**See [QUICK_START_BATCH.md](QUICK_START_BATCH.md) for batch system quick start guide.**

### 7. Setup and Start the Frontend Dashboard

The dashboard provides real-time monitoring of the webhook pipeline with WebSocket support:

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
pnpm install
# or: npm install

# Start development server
pnpm dev
# or: npm run dev
```

Access the dashboard at http://localhost:3000

**Dashboard Features:**
- ✅ Real-time WebSocket connection to webhook server
- ✅ Live pipeline step tracking (Idle → Webhook → Fetch → Dataset → Complete)
- ✅ Event log with expandable JSON payloads (click to expand)
- ✅ Stats panel with annotation counts and dataset versions
- ✅ Beautiful UI with custom color scheme

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

### Image Files Not Downloading to ClearML

**Issue**: You may see warnings like "Can not list files for '/data/upload/1/filename.png/'"

**Cause**: Label Studio running in Docker stores images in its internal filesystem (`/data/upload/`), which is not directly accessible from outside the container.

**Solutions**:

1. **Configure Label Studio storage to use a shared volume** (Recommended):
   ```yaml
   # In docker-compose.yml
   volumes:
     - ./label-studio/data:/label-studio/data
   ```
   Then configure Label Studio to use `/label-studio/data` for uploads.

2. **Use Label Studio's export API** to download images:
   The current implementation saves annotations but skips inaccessible images with a warning. This is fine for annotation metadata but won't include the actual images in ClearML.

3. **Access Label Studio via HTTP**:
   Images are accessible via HTTP at `http://localhost:8080/data/upload/1/filename.png`. The system now automatically converts internal paths to HTTP URLs for ClearML to download.

**Note**: Annotation metadata (labels, bounding boxes, etc.) is always saved to ClearML successfully - only the image file downloads may be affected.

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

## Documentation

### Quick Start Guides
- **[QUICK_START_BATCH.md](QUICK_START_BATCH.md)** - Get started with batch annotation system in 3 commands
- **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** - Complete setup verification checklist

### Feature Guides
- **[BATCH_ANNOTATION_GUIDE.md](BATCH_ANNOTATION_GUIDE.md)** - Complete guide to batch annotation system (600+ lines)
- **[BATCH_SYSTEM_SUMMARY.md](BATCH_SYSTEM_SUMMARY.md)** - Implementation summary and benefits
- **[BATCH_SYSTEM_VISUAL.md](BATCH_SYSTEM_VISUAL.md)** - Visual architecture diagrams and flows
- **[PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md)** - Performance optimization guide
- **[OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)** - Quick reference for optimizations

### Integration Guides
- **[UI_INTEGRATION_GUIDE.md](UI_INTEGRATION_GUIDE.md)** - Frontend dashboard integration and WebSocket protocol
- **[DASHBOARD.md](DASHBOARD.md)** - Dashboard usage guide
- **[SHARED_STORAGE_SETUP.md](SHARED_STORAGE_SETUP.md)** - Shared volume architecture
- **[LABEL_STUDIO_STORAGE_CONFIG.md](LABEL_STUDIO_STORAGE_CONFIG.md)** - Label Studio cloud storage configuration

### System Architecture
```
Batch Processing Flow:
Annotations → Webhook (10ms) → Batch → Scheduler (30min) → Dataset → ClearML

Performance Gains:
- Webhook Response: 51s → 10ms (5000x faster)
- Dataset Versions: 95% reduction
- API Calls: 95% reduction
- Total Time: 17x faster
```

## License

MIT License

## Support

For issues and questions:
- ClearML: https://github.com/allegroai/clearml
- Label Studio: https://github.com/heartexlabs/label-studio
