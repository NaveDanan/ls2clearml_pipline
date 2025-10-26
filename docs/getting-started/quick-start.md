# Quick Start Guide

Get the Label Studio to ClearML pipeline running in 3 commands!

## Prerequisites

- ✅ Python 3.11+ installed
- ✅ Docker Desktop running
- ✅ 8GB RAM available
- ✅ ClearML account (sign up at https://clear.ml)

## Start in 3 Commands

### 1. Start Label Studio & Database
```powershell
docker-compose up -d
```

Wait 30 seconds for services to initialize.

### 2. Start Webhook Server
```powershell
uv run .\main.py webhook
```

**Expected Output:**
```
INFO - Batch manager initialized: interval=30min, min_size=1, max_size=1000
INFO - Batch scheduler started (interval: 30 minutes)
INFO - Task queue started with 3 workers
INFO - Webhook server started on http://0.0.0.0:8000
```

### 3. Start Frontend Dashboard
```powershell
# In new terminal
cd frontend
pnpm run dev
```

**Expected Output:**
```
▲ Next.js 14.x.x
- Local:    http://localhost:3000
✓ Ready in XXXms
```

## Access the Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Dashboard** | http://localhost:3000 | Real-time monitoring |
| **Label Studio** | http://localhost:8090 | Annotation interface |
| **Webhook API** | http://localhost:8000 | Backend server |
| **ClearML** | https://app.clear.ml | Dataset management |

## First-Time Configuration

### Configure Label Studio (1 minute)

1. Open http://localhost:8090
2. Create an account
3. Generate API token: **Settings → Account → Access Token**
4. Update `.env`:
   ```env
   LABEL_STUDIO_API_KEY=your-token-here
   ```

### Configure ClearML (2 minutes)

1. Run: `clearml-init`
2. Follow prompts and paste credentials from https://app.clear.ml/settings/workspace-configuration
3. Verify connection: `python -c "from clearml import Task; print('✓ ClearML connected!')"`

## Test the Pipeline

### Step 1: Create Annotation
1. Go to Label Studio: http://localhost:8090
2. Create a new project or open existing
3. Annotate 1-2 images
4. Click **Submit**

### Step 2: Watch Real-Time Updates
1. Open Dashboard: http://localhost:3000
2. Observe:
   - ✅ **Pending Annotations** counter increases
   - ✅ Real-time step updates appear
   - ✅ Event log shows webhook received

### Step 3: Trigger Batch Processing
Click **"Process Batches Now"** button in dashboard

OR wait 30 minutes for automatic processing

### Step 4: Verify in ClearML
1. Go to https://app.clear.ml
2. Navigate to **ImageAnnotation** project
3. Check **Datasets** tab for new version
4. Verify annotations are included

## What You Should See

### Dashboard View
```
┌─────────────────────────────────────────────────────────────┐
│  Label Studio to ClearML Pipeline                           │
├─────────────────────────────────────────────────────────────┤
│  Total Annotations: 2    Dataset: v1.0    Last Sync: Now    │
│                                                              │
│  🔲 Batch Annotation System      [Process Batches Now]     │
│  Pending: 2    Created: 0    Next: 10:30 AM    Interval: 30min │
│                                                              │
│  📊 Real-time Monitor                                       │
│  🟢 batched - Annotations batched. Next creation scheduled  │
└─────────────────────────────────────────────────────────────┘
```

### Console Output (Server)
```
INFO - Received webhook: ANNOTATION_CREATED
INFO - Retrieved 1 annotations from Label Studio
INFO - Added annotation to batch for project 1. Total: 2
INFO - Broadcast: annotations_batched
```

## Performance Expectations

| Metric | Value |
|--------|-------|
| Webhook Response | <10 milliseconds |
| Dashboard Update | Real-time (<1 second) |
| Batch Processing | ~50 seconds per batch |
| Dataset Creation | Every 30 minutes or manual |

## Common First-Time Issues

### "Connection refused" to Label Studio
**Wait 1-2 minutes** after `docker-compose up` for services to start

### "WebSocket connection failed"
**Check** webhook server is running: `curl http://localhost:8000/health`

### "Invalid API key"
**Verify** `.env` file has correct `LABEL_STUDIO_API_KEY`

### Dashboard shows no data
**Create** an annotation in Label Studio to trigger the pipeline

## Next Steps

Now that you're up and running:

1. ✅ **Configure Shared Storage** - See [Shared Storage Guide](../deployment/shared-storage.md)
2. ✅ **Learn Batch Processing** - See [Batch Annotation Guide](../guides/batch-annotations.md)
3. ✅ **Explore Dashboard** - See [Dashboard Guide](../guides/dashboard.md)
4. ✅ **Understand Architecture** - See [System Architecture](../architecture/overview.md)

## Stopping the Services

```powershell
# Stop webhook server: Ctrl+C
# Stop frontend: Ctrl+C
# Stop Docker services:
docker-compose down
```

## CLI Commands Reference

```powershell
# Setup pipeline
uv run .\main.py setup

# Start webhook server
uv run .\main.py webhook

# Run ClearML pipeline
uv run .\main.py run

# Show help
uv run .\main.py --help
```

## Quick Reference Commands

```powershell
# Health check
curl http://localhost:8000/health

# Process batches manually
curl -X POST http://localhost:8000/batch/process-all

# View batch info
curl http://localhost:8000/batch/info

# View statistics
curl http://localhost:8000/stats
```

---

**Estimated Setup Time**: 10 minutes  
**Difficulty**: Easy  
**Next**: [Installation Guide](installation.md) for detailed setup
