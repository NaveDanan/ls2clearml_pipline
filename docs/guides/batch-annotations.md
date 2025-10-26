# Batch Annotations Guide

Complete guide to using the batch annotation system in the Label Studio to ClearML pipeline.

## Overview

The **Batch Annotation System** accumulates annotations and creates ClearML dataset versions in batches, rather than processing each annotation individually. This dramatically improves efficiency and reduces dataset version sprawl.

## Key Features

### 🔄 Automatic Processing
- **Scheduled batching**: Every 30 minutes (configurable)
- **Smart accumulation**: Collects all annotations between processing cycles
- **Auto-deduplication**: Ensures each task processed only once

### 🚀 Manual Control
- **UI trigger**: "Process Batches Now" button in dashboard
- **API trigger**: REST endpoint for programmatic control
- **Flexible scheduling**: 15min, 30min, 60min, or custom intervals

### 📊 Real-Time Visibility
- **Pending count**: See annotations waiting to be processed
- **Next scheduled**: Know exactly when processing will occur
- **Datasets created**: Track total versions created
- **Batch interval**: View current configuration

## Quick Start

### 1. Start the Server
```powershell
uv run .\main.py webhook
```

**Expected output:**
```
INFO - Batch manager initialized: interval=30min, min_size=1, max_size=1000
INFO - Batch scheduler started (interval: 30 minutes)
INFO - Next batch process scheduled at 10:30:00
```

### 2. Create Annotations
1. Open Label Studio: http://localhost:8090
2. Annotate 5-10 images
3. Click **Submit** for each

### 3. Monitor Progress
Open dashboard: http://localhost:3000

Watch **"Batch Annotation System"** section:
- Pending Annotations: 0 → 5 → 10
- Next Scheduled: Shows countdown
- Datasets Created: 0 (until processing)

### 4. Trigger Processing

**Option A: Wait** - Automatic processing every 30 minutes

**Option B: Manual** - Click "Process Batches Now" button

**Option C: API** - Call endpoint:
```powershell
curl -X POST http://localhost:8000/batch/process-all
```

## How It Works

### Processing Flow

```
┌──────────────────────────────────────────────────────┐
│  1. Annotation Created in Label Studio              │
└────────────┬─────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────┐
│  2. Webhook Sent to Server                          │
│     → Received in <10ms                              │
│     → Response: 202 Accepted                         │
└────────────┬─────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────┐
│  3. Annotations Fetched (Async)                     │
│     → Worker fetches from Label Studio API           │
│     → Completes in background                        │
└────────────┬─────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────┐
│  4. Added to Batch (In-Memory)                      │
│     → Stored per-project                             │
│     → Deduplicated by task ID                        │
│     → Dashboard updated                              │
└────────────┬─────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────┐
│  5. Wait for Trigger                                │
│     → Scheduled timer (30 min)                       │
│     → Manual button click                            │
│     → Auto-trigger (1000 annotations)                │
└────────────┬─────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────┐
│  6. Create Dataset Version                          │
│     → All batched annotations processed              │
│     → Single ClearML dataset created                 │
│     → Images added from shared storage               │
└────────────┬─────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────┐
│  7. Clear Batch                                     │
│     → Batch reset to empty                           │
│     → Stats updated                                  │
│     → Ready for next cycle                           │
└──────────────────────────────────────────────────────┘
```

### Comparison: Before vs After

**Before (Immediate Processing):**
```
Annotation 1 → 51 seconds → Dataset v1.0
Annotation 2 → 51 seconds → Dataset v1.1
Annotation 3 → 51 seconds → Dataset v1.2
...
100 annotations = 5100 seconds (85 min) = 100 versions
```

**After (Batch Processing):**
```
Annotations 1-50 → Batched → Wait 30 min → Dataset v1.0 (50 annotations)
Annotations 51-100 → Batched → Wait 30 min → Dataset v1.1 (50 annotations)
...
100 annotations = 60 minutes = 2 versions
```

**Savings:** 97% fewer versions, 30% faster total time

## Configuration

### Batch Interval

Edit `webhook_server_optimized.py`:

**Every 15 minutes:**
```python
batch_manager = AnnotationBatchManager(
    batch_interval_minutes=15
)
```

**Every hour:**
```python
batch_manager = AnnotationBatchManager(
    batch_interval_minutes=60
)
```

**Every 2 hours:**
```python
batch_manager = AnnotationBatchManager(
    batch_interval_minutes=120
)
```

### Minimum Batch Size

Only process batches with at least N annotations:

```python
batch_manager = AnnotationBatchManager(
    batch_interval_minutes=30,
    min_batch_size=10  # Require 10+ annotations
)
```

**Use cases:**
- `min_batch_size=1` - Process all batches (default)
- `min_batch_size=10` - Small projects
- `min_batch_size=50` - Medium projects
- `min_batch_size=100` - Large projects

### Auto-Trigger Threshold

Process immediately when batch reaches size:

```python
batch_manager = AnnotationBatchManager(
    batch_interval_minutes=30,
    max_batch_size=500  # Auto-trigger at 500
)
```

**Use cases:**
- `max_batch_size=100` - Frequent processing
- `max_batch_size=1000` - Balanced (default)
- `max_batch_size=5000` - Large batches

## API Reference

### Process All Batches

Process all pending batches immediately:

```bash
curl -X POST http://localhost:8000/batch/process-all
```

**Response:**
```json
{
  "status": "success",
  "message": "All batches processed",
  "results": [
    {
      "status": "success",
      "project_id": 1,
      "dataset_id": "abc123...",
      "annotations_count": 15,
      "timestamp": "2025-10-26T10:30:00"
    }
  ],
  "timestamp": "2025-10-26T10:30:00"
}
```

### Process Specific Project

Process batch for one project only:

```bash
curl -X POST http://localhost:8000/batch/process/1
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "status": "success",
    "project_id": 1,
    "dataset_id": "abc123...",
    "annotations_count": 15,
    "timestamp": "2025-10-26T10:30:00"
  },
  "timestamp": "2025-10-26T10:30:00"
}
```

### Get Batch Information

View current batch status:

```bash
# All projects
curl http://localhost:8000/batch/info

# Specific project
curl http://localhost:8000/batch/info?project_id=1
```

**Response:**
```json
{
  "status": "success",
  "info": {
    "batches": {
      "1": {
        "size": 15,
        "created_at": "2025-10-26T10:00:00",
        "last_updated": "2025-10-26T10:25:00",
        "age_seconds": 1500,
        "is_processing": false
      }
    },
    "total_batches": 1,
    "total_annotations": 15
  },
  "timestamp": "2025-10-26T10:30:00"
}
```

### Get Statistics

Comprehensive stats including batch info:

```bash
curl http://localhost:8000/stats
```

**Response includes:**
```json
{
  "batch_stats": {
    "total_annotations_batched": 150,
    "total_datasets_created": 5,
    "last_batch_process": "2025-10-26T10:00:00",
    "next_scheduled_process": "2025-10-26T10:30:00",
    "batch_interval_minutes": 30,
    "min_batch_size": 1,
    "max_batch_size": 1000,
    "active_batches": 2,
    "total_pending_annotations": 18
  }
}
```

## Dashboard Integration

### Batch Statistics Panel

The dashboard displays a dedicated section:

```
┌───────────────────────────────────────────────────────┐
│  🔲 Batch Annotation System    [Process Batches Now] │
├──────────────┬──────────────┬──────────────┬─────────┤
│ Pending Ann. │  Datasets    │ Next         │ Interval│
│      18      │  Created: 5  │ 10:30 AM     │ 30 min  │
└──────────────┴──────────────┴──────────────┴─────────┘
```

**Metrics explained:**
- **Pending Annotations**: Total across all projects waiting
- **Datasets Created**: Cumulative count since server start
- **Next Scheduled**: Time of next automatic processing
- **Interval**: Current batch processing frequency

### Manual Trigger Button

Click **"Process Batches Now"** to:
- Immediately process all pending batches
- Create dataset versions in ClearML
- Bypass waiting for scheduled time
- See results in real-time

## Use Cases

### High-Volume Annotation

**Scenario:** Team of 5 annotators, 1000 images/day

**Configuration:**
```python
batch_interval_minutes=60  # Hourly datasets
max_batch_size=200        # Auto-process if >200
```

**Result:** ~8 dataset versions/day instead of 1000

### End-of-Day Processing

**Scenario:** Annotate throughout day, dataset at EOD

**Configuration:**
```python
batch_interval_minutes=480  # 8 hours
min_batch_size=1
```

**Workflow:**
1. Team annotates all day
2. Manual trigger at 5 PM
3. Single dataset with all day's work

### Continuous Integration

**Scenario:** CI/CD pipeline triggers on new dataset

**Configuration:**
```python
batch_interval_minutes=30  # Regular schedule
max_batch_size=100        # Also auto-trigger
```

**Integration:**
```python
# Watch for new datasets
from clearml import Dataset

def on_new_dataset(dataset_id):
    # Trigger training pipeline
    Task.create(...)
```

## Performance Metrics

### Webhook Response Time
- **Before**: 51 seconds per annotation
- **After**: <10 milliseconds
- **Improvement**: 5000x faster

### Dataset Versions
- **Before**: 1 per annotation
- **After**: 1 per batch (e.g., 48/day at 30min intervals)
- **Reduction**: ~95%

### Total Processing Time (1000 annotations)
- **Before**: ~14 hours (sequential)
- **After**: ~30 minutes (with batching)
- **Speedup**: 28x

### Storage Efficiency
- **Before**: Duplicate images in multiple versions
- **After**: Efficient versioning with lineage
- **Savings**: Significant (depends on image sizes)

## Best Practices

### 1. Choose Appropriate Interval

| Interval | Use Case | Datasets/Day |
|----------|----------|--------------|
| 15 min | Fast feedback, small team | 96 |
| 30 min | Balanced (default) | 48 |
| 60 min | Batch work, multiple projects | 24 |
| 120 min | Large annotations, slow pace | 12 |

### 2. Set Minimum Batch Size

Prevent tiny batches:
```python
min_batch_size=5  # Require at least 5 annotations
```

### 3. Monitor Pending Count

Check dashboard regularly:
- **Growing**: Team is productive
- **Stable**: Matches annotation rate
- **Zero**: All processed

### 4. Use Manual Triggers

For important milestones:
- End of annotation sprint
- Before training run
- Quality check points

### 5. Adjust Auto-Trigger

For burst annotation sessions:
```python
max_batch_size=50  # Process more frequently during bursts
```

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md#batch-processing-issues) for detailed solutions.

### Quick Fixes

**Batch not processing?**
```bash
# Check next scheduled time
curl http://localhost:8000/stats | jq .batch_stats.next_scheduled_process

# Manual trigger
curl -X POST http://localhost:8000/batch/process-all
```

**Pending count not updating?**
```bash
# Verify webhook server running
curl http://localhost:8000/health

# Check Label Studio webhook configured
# Should point to: http://host.docker.internal:8000/webhook/label-studio
```

**Processing too frequent?**
```python
# Increase max_batch_size
max_batch_size=5000  # from 1000
```

## Migration from Immediate Processing

If currently using `webhook_server.py`:

1. **Stop old server** (Ctrl+C)
2. **Start optimized server:**
   ```powershell
   python webhook_server_optimized.py
   ```
3. **No data loss** - All new annotations batched automatically
4. **Existing datasets** - Remain unchanged in ClearML

## Advanced Topics

### Redis Backend (Optional)

For distributed deployment:
```python
# In webhook_server_optimized.py
use_redis = True

# Install Redis
docker run -d -p 6379:6379 redis:alpine
```

**Benefits:**
- Batch survives server restart
- Multiple servers can share queue
- Better monitoring

### Custom Batch Logic

Override batch manager methods:
```python
class CustomBatchManager(AnnotationBatchManager):
    async def should_process_batch(self, project_id):
        # Custom logic
        batch = self.batches.get(project_id)
        return batch.size >= 10 and is_business_hours()
```

### WebSocket Events

Subscribe to batch events in frontend:
```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'batch_stats_update') {
    updateBatchDisplay(data.data);
  }
};
```

---

**Related Guides:**
- [Quick Start](../getting-started/quick-start.md)
- [Dashboard Guide](dashboard.md)
- [Performance Architecture](../architecture/performance.md)
- [Troubleshooting](troubleshooting.md)

**Last Updated**: October 26, 2025  
**Difficulty**: Intermediate  
**Time to Read**: 15 minutes
