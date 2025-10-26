# Project Structure

This document describes the organized folder structure of the Label Studio to ClearML Pipeline project.

## Directory Layout

```
ls2clearml_pipline/
├── documents/              # All documentation files
│   ├── BATCH_ANNOTATION_GUIDE.md
│   ├── BATCH_SYSTEM_SUMMARY.md
│   ├── BATCH_SYSTEM_VISUAL.md
│   ├── CLEARML_INTEGRATION_COMPLETE.md
│   ├── CLEARML_SERVER_SETUP.md
│   ├── DASHBOARD.md
│   ├── DOCKER_COMPOSE_GUIDE.md
│   ├── IMPLEMENTATION_COMPLETE.md
│   ├── LABEL_STUDIO_STORAGE_CONFIG.md
│   ├── OPTIMIZATION_SUMMARY.md
│   ├── PERFORMANCE_OPTIMIZATION.md
│   ├── QUICK_START_BATCH.md
│   ├── SETUP_COMPLETE.md
│   ├── SETUP_GUIDE.md
│   ├── SHARED_STORAGE_SETUP.md
│   ├── STATUS.md
│   └── UI_INTEGRATION_GUIDE.md
│
├── docker/                 # Docker Compose configurations
│   ├── docker-compose.yml             # Label Studio + PostgreSQL
│   ├── docker-compose.clearml.yml     # ClearML server only
│   └── docker-compose.full.yml        # Complete stack
│
├── setup/                  # Setup and deployment scripts
│   └── start-full-stack.ps1           # Full stack startup script
│
├── core/                   # Core configuration
│   ├── __init__.py
│   └── config.py                      # Settings and environment config
│
├── clients/                # API clients for external services
│   ├── __init__.py
│   ├── label_studio_client.py         # Sync Label Studio API client
│   ├── async_label_studio_client.py   # Async Label Studio client
│   └── clearml_manager.py             # ClearML dataset & pipeline manager
│
├── services/               # Business logic services
│   ├── __init__.py
│   ├── webhook_server.py              # Original webhook server
│   ├── webhook_server_optimized.py    # Optimized webhook with batch processing
│   ├── task_queue.py                  # Async task queue manager
│   └── annotation_batch_manager.py    # Batch annotation system
│
├── pipelines/              # Pipeline setup and execution
│   ├── __init__.py
│   ├── setup_pipeline.py              # Initial pipeline setup
│   └── run_pipeline.py                # Manual pipeline execution
│
├── examples/               # Example scripts and templates
│   ├── __init__.py
│   └── example_training.py            # Example training script template
│
├── frontend/               # Next.js dashboard
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
│
├── main.py                 # Main CLI entry point (ONLY .py file in root)
├── .env.example            # Environment variables template
├── .gitignore             # Git ignore rules
├── pyproject.toml         # Python project configuration
├── README.md              # Main project documentation
└── PROJECT_STRUCTURE.md   # This file
```

## Folder Descriptions

### `/core`
Core configuration and settings management.

**Files:**
- `config.py` - Application settings using Pydantic, environment variable management

### `/clients`
API clients for external services (Label Studio and ClearML).

**Files:**
- `label_studio_client.py` - Synchronous Label Studio API client
- `async_label_studio_client.py` - Asynchronous Label Studio client for high-performance operations
- `clearml_manager.py` - ClearML dataset management and pipeline orchestration

### `/services`
Business logic and service layer components.

**Files:**
- `webhook_server.py` - Original webhook server (synchronous processing)
- `webhook_server_optimized.py` - Optimized webhook server with batch processing and async queue (5000x faster)
- `task_queue.py` - Async task queue manager with Redis support
- `annotation_batch_manager.py` - Batch annotation system with 30-minute scheduling

### `/pipelines`
Pipeline setup and execution scripts.

**Files:**
- `setup_pipeline.py` - Initial pipeline setup, project creation, webhook configuration
- `run_pipeline.py` - Manual pipeline execution for training and evaluation

### `/examples`
Example scripts and templates for customization.

**Files:**
- `example_training.py` - Template training script showing how to integrate custom ML models

### `/documents`
Contains all project documentation including guides, setup instructions, and architecture diagrams.

**Key Files:**
- `QUICK_START_BATCH.md` - Quick start guide for batch annotation system
- `CLEARML_SERVER_SETUP.md` - Complete ClearML self-hosted setup guide (700+ lines)
- `DOCKER_COMPOSE_GUIDE.md` - Docker deployment reference (300+ lines)
- `BATCH_ANNOTATION_GUIDE.md` - Comprehensive batch system guide (600+ lines)
- `SHARED_STORAGE_SETUP.md` - Shared volume architecture documentation

### `/docker`
All Docker Compose configuration files for different deployment scenarios.

**Files:**
- `docker-compose.yml` - Label Studio + PostgreSQL only (for use with ClearML Cloud)
- `docker-compose.clearml.yml` - ClearML server stack only (6 services)
- `docker-compose.full.yml` - Complete stack with both systems (11 services)

**Usage:**
```powershell
# Label Studio only
docker-compose -f docker/docker-compose.yml up -d

# ClearML only
docker-compose -f docker/docker-compose.clearml.yml up -d

# Full stack
docker-compose -f docker/docker-compose.full.yml up -d
```

### `/setup`
Setup and deployment automation scripts.

**Files:**
- `start-full-stack.ps1` - One-command startup for complete stack

**Usage:**
```powershell
.\setup\start-full-stack.ps1
```

### `/frontend`
Next.js 14 dashboard application with TypeScript and Shadcn UI.

**Features:**
- Real-time WebSocket connection
- Live pipeline status tracking
- Batch annotation statistics
- Event logging with expandable JSON

**Commands:**
```powershell
cd frontend
pnpm install
pnpm dev
```

### `/main.py` (Root)
**The only Python file in the root directory** - Main CLI entry point for the entire application.

**Usage:**
```powershell
# Setup the pipeline
python main.py setup

# Start webhook server
python main.py webhook

# Run pipeline manually
python main.py run --dataset-id <id>
```

## Python Module Organization

All Python code is now organized into logical modules:

```python
# Core configuration
from core.config import settings

# API Clients
from clients import LabelStudioClient, AsyncLabelStudioClient, ClearMLManager

# Services
from services import TaskQueueManager, get_task_queue, AnnotationBatchManager

# Pipelines
from pipelines import setup_pipeline, run_pipeline
```

**Benefits:**
- ✅ Clear separation of concerns
- ✅ Easy to find and maintain code
- ✅ Logical grouping by functionality
- ✅ Single entry point in root (`main.py`)
- ✅ Proper Python package structure with `__init__.py`

## Quick Navigation

### Getting Started
1. **First-time setup**: Read `README.md`
2. **Docker deployment**: See `documents/DOCKER_COMPOSE_GUIDE.md`
3. **ClearML self-hosted**: See `documents/CLEARML_SERVER_SETUP.md`
4. **Batch system**: See `documents/QUICK_START_BATCH.md`

### Running the Stack

**Cloud ClearML + Local Label Studio:**
```powershell
docker-compose -f docker/docker-compose.yml up -d
```

**Full Self-Hosted:**
```powershell
.\setup\start-full-stack.ps1
```

**Frontend Dashboard:**
```powershell
cd frontend
pnpm dev
```

**Webhook Server:**
```powershell
python -m services.webhook_server_optimized
# Or using main.py
python main.py webhook
```

## File Organization Benefits

✅ **Clear separation** - Code, docs, configs in dedicated folders  
✅ **Easy navigation** - Find files by purpose quickly  
✅ **Scalable structure** - Easy to add new components  
✅ **Professional layout** - Industry-standard organization  
✅ **Better Git management** - Easier to track changes by category  

## Related Documentation

- **Main README**: [README.md](../README.md)
- **Docker Guide**: [documents/DOCKER_COMPOSE_GUIDE.md](documents/DOCKER_COMPOSE_GUIDE.md)
- **Setup Guide**: [documents/CLEARML_SERVER_SETUP.md](documents/CLEARML_SERVER_SETUP.md)
- **All Docs**: See [documents/](documents/) folder

---

**Last Updated**: October 26, 2025  
**Organization Version**: 2.0
