# CLI Reference

Command-line interface for the Label Studio to ClearML pipeline.

## Overview

The pipeline provides a unified CLI via `uv run .\main.py` with three main commands:

```
usage: main.py [-h] {setup,webhook,run} ...

Label Studio to ClearML Pipeline Manager

positional arguments:
  {setup,webhook,run}  Available commands
    setup              Setup the pipeline
    webhook            Start the webhook server
    run                Run the ClearML pipeline

options:
  -h, --help           show this help message and exit
```

## Commands

### setup - Setup the Pipeline

Initializes the complete pipeline including Label Studio project and webhooks.

**Usage:**
```powershell
uv run .\main.py setup
```

**What it does:**
1. Verifies environment configuration (.env file)
2. Checks ClearML connection
3. Creates Label Studio project (if not exists)
4. Configures webhook to connect Label Studio → Webhook Server
5. Displays setup summary

**Expected Output:**
```
============================================================
Label Studio to ClearML Pipeline Setup
============================================================
INFO - Verifying environment configuration...
INFO - ✓ Environment configuration OK
INFO - Setting up ClearML configuration...
INFO - ✓ ClearML configuration successful
INFO - Setting up Label Studio project...
INFO - ✓ Created new project: ImageAnnotation (ID: 1)
INFO - Setting up webhook...
INFO - ✓ Webhook created: http://host.docker.internal:8000/webhook/label-studio

============================================================
Setup Summary
============================================================
INFO - ClearML: ✓ OK
INFO - Label Studio: ✓ OK
INFO - Webhook: ✓ OK

✓ Pipeline setup complete!

Next steps:
1. Start the webhook server: uv run .\main.py webhook
2. Start annotating in Label Studio
3. Annotations will automatically sync to ClearML
```

**Prerequisites:**
- Docker running with Label Studio
- `.env` file configured
- ClearML credentials set up

**Options:**
- None (interactive setup)

---

### webhook - Start the Webhook Server

Starts the optimized webhook server with batch processing and real-time monitoring.

**Usage:**
```powershell
uv run .\main.py webhook
```

**What it does:**
1. Initializes batch annotation manager
2. Starts task queue with async workers
3. Starts scheduler for automatic batch processing
4. Launches FastAPI server on port 8000
5. Enables WebSocket for real-time dashboard updates

**Expected Output:**
```
INFO - Batch manager initialized: interval=30min, min_size=1, max_size=1000
INFO - Batch scheduler started (interval: 30 minutes)
INFO - Next batch process scheduled at 10:30:00
INFO - Task queue started with 3 workers
INFO - Webhook server started with optimized async processing and batch annotation system
INFO - Application startup complete.
INFO - Uvicorn running on http://0.0.0.0:8000
```

**Features Enabled:**
- ✅ Batch annotation processing (30-minute intervals)
- ✅ Manual batch triggers via API
- ✅ Real-time WebSocket updates
- ✅ Async task queue (3 workers)
- ✅ Auto-processing at 1000 annotations

**Endpoints Available:**
- `GET /health` - Health check
- `GET /stats` - Statistics
- `POST /webhook/label-studio` - Label Studio webhook
- `POST /batch/process-all` - Process all batches
- `POST /batch/process/{project_id}` - Process specific project
- `GET /batch/info` - Batch information
- `WS /ws` - WebSocket connection

**Stop Server:**
```powershell
Ctrl+C
```

**Options:**
- None (uses configuration from `.env`)

---

### run - Run the ClearML Pipeline

Executes the ClearML ML pipeline with data preparation, training, and evaluation.

**Usage:**
```powershell
uv run .\main.py run
```

**What it does:**
1. Creates ClearML pipeline task
2. Adds pipeline steps:
   - Data Preparation
   - Model Training
   - Model Evaluation
3. Executes pipeline in ClearML
4. Monitors execution

**Expected Output:**
```
INFO - Starting ClearML pipeline...
INFO - Created pipeline: ImageAnnotation Pipeline
INFO - Added step: Data Preparation
INFO - Added step: Model Training
INFO - Added step: Model Evaluation
INFO - Pipeline execution started
INFO - Monitor at: https://app.clear.ml/projects/xxx/experiments/yyy
```

**Prerequisites:**
- ClearML configured and connected
- Dataset exists in ClearML
- Training code implemented

**Options:**
- None (uses default pipeline configuration)

---

## Common Workflows

### Initial Setup
```powershell
# 1. Start Docker services
docker-compose up -d

# 2. Setup pipeline
uv run .\main.py setup

# 3. Start webhook server
uv run .\main.py webhook

# 4. Start frontend (in new terminal)
cd frontend
pnpm run dev
```

### Daily Use
```powershell
# Start webhook server
uv run .\main.py webhook

# Create annotations in Label Studio
# Monitor in dashboard at http://localhost:3000

# Manually process batches if needed
curl -X POST http://localhost:8000/batch/process-all
```

### Training Workflow
```powershell
# 1. Ensure annotations are processed
curl -X POST http://localhost:8000/batch/process-all

# 2. Run training pipeline
uv run .\main.py run

# 3. Monitor in ClearML
# Open https://app.clear.ml
```

### Troubleshooting
```powershell
# Check setup status
uv run .\main.py setup

# Restart webhook server
# Ctrl+C to stop, then:
uv run .\main.py webhook

# Check webhook health
curl http://localhost:8000/health
```

## Environment Variables

The CLI reads configuration from `.env` file:

```env
# Label Studio
LABEL_STUDIO_URL=http://localhost:8090
LABEL_STUDIO_API_KEY=your-api-key

# ClearML
CLEARML_API_HOST=https://api.clear.ml
CLEARML_WEB_HOST=https://app.clear.ml
CLEARML_FILES_HOST=https://files.clear.ml
CLEARML_API_ACCESS_KEY=your-access-key
CLEARML_API_SECRET_KEY=your-secret-key
CLEARML_PROJECT_NAME=ImageAnnotation
CLEARML_DATASET_NAME=AnnotatedImages

# Webhook
WEBHOOK_SECRET=your-webhook-secret

# Storage
SHARED_DATA_DIR=./shared-data
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (check logs) |
| 2 | Configuration error |
| 130 | Interrupted (Ctrl+C) |

## Logging

All commands output logs to console:
- **INFO**: Normal operations
- **WARNING**: Non-critical issues
- **ERROR**: Failures requiring attention

To increase verbosity (for debugging):
```powershell
# Edit respective Python files to set DEBUG level
# Or check console output for detailed errors
```

## Tips

### Run in Background (Windows)
```powershell
# Start webhook server in background
Start-Process powershell -ArgumentList "uv run .\main.py webhook" -WindowStyle Hidden

# View running processes
Get-Process powershell
```

### Use with Docker Compose
```powershell
# Combined startup script
docker-compose up -d && uv run .\main.py webhook
```

### Quick Health Check
```powershell
# One-liner to verify all services
docker ps && curl http://localhost:8000/health && curl http://localhost:3000
```

## Advanced Usage

### Custom Configuration

Edit configuration files:
- `webhook_server_optimized.py` - Webhook server settings
- `setup_pipeline.py` - Setup configuration
- `run_pipeline.py` - Pipeline parameters

### Batch Processing Configuration

The webhook server uses these defaults:
```python
batch_interval_minutes=30   # Process every 30 minutes
min_batch_size=1            # Minimum annotations to process
max_batch_size=1000         # Auto-trigger threshold
```

Modify in `webhook_server_optimized.py` to customize.

## Related Documentation

- [Quick Start Guide](getting-started/quick-start.md) - Get running fast
- [Installation Guide](getting-started/installation.md) - Detailed setup
- [Batch Annotations](guides/batch-annotations.md) - Batch processing
- [Troubleshooting](guides/troubleshooting.md) - Problem solving

---

**Last Updated**: October 26, 2025  
**CLI Version**: 2.0
