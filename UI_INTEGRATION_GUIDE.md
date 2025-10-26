# UI Integration Guide

## Frontend Dashboard Connection

### Overview
The **Next.js dashboard** at `http://localhost:3000` connects to **both webhook servers** via WebSocket at `ws://localhost:8000/ws`. Both servers use the same WebSocket protocol for compatibility.

### Webhook Server Versions

#### 1. **Original Server** (`webhook_server.py`)
- **Purpose**: Simple synchronous processing
- **Best For**: Development, testing, small workloads
- **Performance**: ~51 seconds per webhook, sequential processing
- **Features**:
  - Basic stats: `totalAnnotations`, `datasetVersion`, `lastSync`, `activeWebhooks`
  - Real-time step updates
  - Event logging

#### 2. **Optimized Server** (`webhook_server_optimized.py`)
- **Purpose**: High-performance async processing with task queuing
- **Best For**: Production, high-volume annotations
- **Performance**: <10ms webhook response, 3x throughput with parallel workers
- **Features**:
  - All original server features
  - **Additional Queue Statistics**:
    - `queue_size`: Pending tasks waiting to be processed
    - `total_tasks`: Total tasks submitted
    - `pending`: Tasks not yet started
    - `processing`: Tasks currently being processed
    - `completed`: Successfully completed tasks
    - `failed`: Failed tasks
    - `workers`: Number of concurrent worker coroutines

### UI Enhancements

The dashboard now **automatically detects** which server is running:

#### Default View (Both Servers)
```
┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ Total Annotations│  Dataset Version │    Last Sync     │ Active Webhooks  │
│       42         │      v1.2.3      │   10:30:45 AM    │        2         │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┘
```

#### Optimized Server View (Additional Section)
```
⚡ Optimized Server - Queue Statistics
┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│   Queue Size     │  Tasks Completed │   Tasks Failed   │  Active Workers  │
│        3         │     128/131      │        0         │      2/3         │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┘
```

### WebSocket Protocol

#### Messages Sent by Servers

**1. Initial State** (sent on connection)
```json
{
  "type": "initial_state",
  "data": {
    "stats": {
      "total_annotations": 42,
      "dataset_version": "v1.2.3",
      "last_sync": "2024-01-15T10:30:45",
      "active_webhooks": 2,
      "tasks_queued": 5,        // Optimized server only
      "tasks_completed": 128,    // Optimized server only
      "tasks_failed": 0          // Optimized server only
    },
    "current_step": {
      "step": "idle",
      "message": "Waiting for events...",
      "timestamp": null,
      "status": "idle"
    },
    "recent_events": [...],
    "queue_stats": {             // Optimized server only
      "queue_size": 3,
      "total_tasks": 131,
      "pending": 3,
      "processing": 2,
      "completed": 128,
      "failed": 0,
      "workers": 3,
      "running": true
    }
  }
}
```

**2. Step Update** (sent during processing)
```json
{
  "type": "step_update",
  "data": {
    "step": "fetching_annotations",
    "message": "Fetching annotations from Label Studio...",
    "timestamp": "2024-01-15T10:31:00",
    "status": "processing"
  }
}
```

**3. Stats Update** (sent after task completion)
```json
{
  "type": "stats_update",
  "data": {
    "total_annotations": 43,
    "dataset_version": "v1.2.4",
    "last_sync": "2024-01-15T10:31:30",
    "active_webhooks": 1,
    "tasks_queued": 6,
    "tasks_completed": 129,
    "tasks_failed": 0
  }
}
```

**4. Queue Stats Update** (optimized server only)
```json
{
  "type": "queue_stats_update",
  "data": {
    "queue_size": 2,
    "total_tasks": 132,
    "pending": 2,
    "processing": 1,
    "completed": 129,
    "failed": 0,
    "workers": 3,
    "running": true
  }
}
```

### UI Components

#### 1. **StatsPanel** (`frontend/components/StatsPanel.tsx`)
- Displays 4 main statistics cards
- **Conditionally renders** queue statistics section if optimized server detected
- Uses Framer Motion for animations
- Icons: `FileText`, `Package`, `Clock`, `Activity`, `ListChecks`, `XCircle`, `Zap`

#### 2. **RealtimeMonitor** (`frontend/components/RealtimeMonitor.tsx`)
- Shows current pipeline step with status indicator
- Lists recent events (up to 20)
- Expandable event cards with full JSON payloads
- Color-coded status: idle (gray), processing (blue), success (green), error (red)

#### 3. **PipelineFlow** (`frontend/components/PipelineFlow.tsx`)
- Visual pipeline diagram
- Shows flow: Label Studio → Webhook → ClearML → Dataset

### Running the Servers

#### Original Server
```bash
python webhook_server.py
```

#### Optimized Server
```bash
python webhook_server_optimized.py
```

**Note**: Run only ONE server at a time since both use port 8000.

### Frontend Development Server
```bash
cd frontend
npm run dev
```

Then open `http://localhost:3000` in your browser.

### Configuration

Both servers read from the same environment variables:
```env
# Label Studio
LABEL_STUDIO_URL=http://localhost:8080
LABEL_STUDIO_API_KEY=your-api-key-here

# ClearML
CLEARML_API_HOST=https://api.clear.ml
CLEARML_WEB_HOST=https://app.clear.ml
CLEARML_FILES_HOST=https://files.clear.ml
CLEARML_API_ACCESS_KEY=your-access-key
CLEARML_API_SECRET_KEY=your-secret-key

# Webhook
WEBHOOK_SECRET=your-webhook-secret

# Storage
SHARED_DATA_DIR=./shared-data
```

### Testing

1. **Start the server** (choose one):
   ```bash
   python webhook_server.py           # Original
   # OR
   python webhook_server_optimized.py # Optimized
   ```

2. **Start the frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Create annotations** in Label Studio (http://localhost:8080)

4. **Watch the dashboard** update in real-time at http://localhost:3000

### Performance Comparison

| Metric                    | Original Server | Optimized Server |
|---------------------------|-----------------|------------------|
| Webhook Response Time     | ~51 seconds     | <10 milliseconds |
| Processing Mode           | Synchronous     | Async + Queue    |
| Concurrent Tasks          | 1               | 3 (configurable) |
| Throughput (tasks/min)    | ~1.2            | ~3.5 (3x faster) |
| Label Studio API Calls    | Sequential      | Parallel         |
| UI Queue Metrics          | ❌              | ✅               |
| Redis Support             | ❌              | ✅ (optional)    |

### Troubleshooting

#### Dashboard Shows No Queue Stats
- **Cause**: Running original server, not optimized server
- **Solution**: Switch to `webhook_server_optimized.py` or ignore (queue stats are optional)

#### WebSocket Connection Failed
- **Cause**: Server not running on port 8000
- **Solution**: Start webhook server with `python webhook_server.py` or `python webhook_server_optimized.py`

#### Stats Not Updating
- **Cause**: No annotations being created in Label Studio
- **Solution**: Create/update annotations in Label Studio UI

#### Queue Size Always 0
- **Cause**: Tasks processing faster than they're created (good performance!)
- **Solution**: Create multiple annotations rapidly to see queuing in action

### Next Steps

1. **Test both servers** to compare performance
2. **Configure Label Studio storage** to use shared volume (see `LABEL_STUDIO_STORAGE_CONFIG.md`)
3. **Tune worker count** in optimized server (currently 3)
4. **Enable Redis** for distributed task queue (optional)
5. **Add more metrics** to dashboard as needed

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Dashboard                        │
│                     (Next.js @ localhost:3000)                   │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  StatsPanel  │  │   Pipeline   │  │  Realtime Monitor    │  │
│  │              │  │     Flow     │  │                      │  │
│  │ • Basic Stats│  │              │  │ • Current Step       │  │
│  │ • Queue Stats│  │              │  │ • Recent Events      │  │
│  │   (opt.)     │  │              │  │ • Expandable JSON    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ WebSocket (ws://localhost:8000/ws)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Webhook Server (FastAPI)                    │
│                                                                   │
│  ┌──────────────────────┐      ┌──────────────────────────┐    │
│  │  webhook_server.py   │  OR  │webhook_server_optimized.py│    │
│  │  (Original)          │      │(Async + Queue)            │    │
│  ├──────────────────────┤      ├──────────────────────────┤    │
│  │ • Synchronous        │      │ • Task Queue (3 workers) │    │
│  │ • ~51s per webhook   │      │ • <10ms response         │    │
│  │ • Sequential         │      │ • Parallel processing    │    │
│  │ • Basic stats        │      │ • Enhanced stats         │    │
│  └──────────────────────┘      └──────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│    Label Studio         │   │      ClearML            │
│  (localhost:8080)       │   │  (api.clear.ml)         │
│                         │   │                         │
│  PostgreSQL Backend     │   │  Dataset Versioning     │
│  Shared Volume:         │   │  Pipeline Management    │
│  ./shared-data          │   │  Shared Volume:         │
│                         │   │  ./shared-data          │
└─────────────────────────┘   └─────────────────────────┘
```

---

**Created**: 2024-01-15  
**Last Updated**: 2024-01-15  
**Author**: ClearML Pipeline Team
