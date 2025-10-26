# Real-Time Dashboard Guide

## Overview

The Label Studio to ClearML pipeline includes a beautiful real-time monitoring dashboard built with Next.js, TypeScript, and WebSockets.

![Dashboard Preview](https://img.shields.io/badge/Status-Live-success)
![WebSocket](https://img.shields.io/badge/WebSocket-Connected-blue)

## Features

### 🎯 Real-Time Monitoring

The dashboard connects to the webhook server via WebSocket and displays live updates:

- **Pipeline Status**: Visual step-by-step progress tracking
- **Event Log**: Real-time feed of all webhook events
- **Statistics**: Live counters for annotations, dataset versions, and webhooks
- **Connection Status**: Visual indicators for Label Studio, ClearML, and webhook server

### 📊 Pipeline Visualization

Watch your pipeline execute in real-time through 5 distinct stages:

1. **Idle** - Waiting for webhook events
2. **Webhook Received** - Label Studio sends annotation update
3. **Fetching Annotations** - Retrieving data from Label Studio API
4. **Creating Dataset** - Updating ClearML dataset version
5. **Completed** - Pipeline finished successfully

Each step is color-coded:
- 🔵 **Verdigris/Cyan**: Active processing
- ✅ **Green**: Completed successfully
- ❌ **Red**: Error occurred
- ⚪ **Gray**: Not started

### 📋 Interactive Event Log

The event log shows all webhook activity with:

- **Event Types**: Categorized by action (webhook_received, annotations_fetched, dataset_created, etc.)
- **Timestamps**: Precise timing for each event
- **Expandable JSON**: Click any event to see the full payload
- **Auto-scroll**: Latest events appear at the top
- **Color Coding**: Errors in red, success in cyan

#### Expanding Events

Click on any event card to expand and view the complete JSON payload:

```json
{
  "type": "webhook_received",
  "data": {
    "action": "ANNOTATION_CREATED",
    "project_id": 1,
    "annotation": {
      "id": 123,
      "task": {...},
      "result": [...]
    }
  },
  "timestamp": "2025-10-26T21:11:47.493000"
}
```

### 📈 Statistics Panel

Live metrics updated in real-time:

- **Total Annotations**: Count of all annotations in Label Studio
- **Dataset Version**: Current ClearML dataset ID
- **Last Sync**: Timestamp of most recent sync
- **Active Webhooks**: Number of webhooks currently being processed

### 🎨 Custom Color Scheme

The dashboard uses a carefully crafted color palette:

- **Charcoal** (#3B4149): Primary background
- **Platinum** (#E8E8E9): Text and foreground
- **Verdigris** (#05ABB3): Primary accent and active states
- **Dark Cyan** (#26949C): Secondary accent and highlights

## Getting Started

### Prerequisites

- Node.js 18+ or Bun
- pnpm (or npm/yarn)
- Webhook server running on port 8000

### Installation

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

### Configuration

The dashboard automatically connects to:
- **Webhook Server**: `ws://localhost:8000/ws` (WebSocket)
- **Health Check**: `http://localhost:8000/health` (REST API)

To change these URLs, edit `frontend/app/page.tsx`:

```typescript
const websocket = new WebSocket('ws://your-server:8000/ws')
```

## Architecture

### Technology Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Shadcn UI
- **Animation**: Framer Motion
- **State Management**: React Hooks (useState, useEffect, useCallback)
- **Real-time**: Native WebSocket API

### Component Structure

```
frontend/
├── app/
│   ├── page.tsx           # Main dashboard page
│   ├── layout.tsx         # Root layout
│   └── globals.css        # Global styles with custom colors
├── components/
│   ├── PipelineFlow.tsx   # Pipeline visualization
│   ├── StatsPanel.tsx     # Statistics cards
│   ├── RealtimeMonitor.tsx # Event log and step tracker
│   └── ui/                # Shadcn UI components
│       ├── card.tsx
│       ├── button.tsx
│       └── skeleton.tsx
└── lib/
    └── utils.ts           # Utility functions
```

### WebSocket Protocol

The dashboard communicates with the webhook server using JSON messages:

#### Client → Server
No explicit messages sent (receive-only)

#### Server → Client

**Initial State**:
```json
{
  "type": "initial_state",
  "data": {
    "stats": {
      "total_annotations": 10,
      "dataset_version": "abc123",
      "last_sync": "2025-10-26T21:00:00",
      "active_webhooks": 0
    },
    "current_step": {
      "step": "idle",
      "message": "Waiting for events...",
      "timestamp": null,
      "status": "idle"
    },
    "recent_events": []
  }
}
```

**Step Updates**:
```json
{
  "type": "step_update",
  "data": {
    "step": "webhook_received",
    "message": "Received ANNOTATION_CREATED event for project 1",
    "timestamp": "2025-10-26T21:11:47.494000",
    "status": "processing"
  }
}
```

**Stats Updates**:
```json
{
  "type": "stats_update",
  "data": {
    "total_annotations": 15,
    "dataset_version": "def456",
    "last_sync": "2025-10-26T21:15:00",
    "active_webhooks": 1
  }
}
```

**Other Events**:
```json
{
  "type": "webhook_received",
  "data": {
    "action": "ANNOTATION_CREATED",
    "project_id": 1
  },
  "timestamp": "2025-10-26T21:11:47.493000"
}
```

## Customization

### Changing Colors

Edit `frontend/app/globals.css`:

```css
:root {
  --charcoal: 212 9% 25%;      /* #3B4149 */
  --platinum: 240 3% 91%;      /* #E8E8E9 */
  --verdigris: 183 95% 36%;    /* #05ABB3 */
  --dark-cyan: 182 59% 38%;    /* #26949C */
}
```

### Adding New Stats

Update `frontend/components/StatsPanel.tsx`:

```typescript
<Card>
  <CardHeader>
    <CardTitle>Your Custom Metric</CardTitle>
  </CardHeader>
  <CardContent>
    <p className="text-3xl font-bold">{stats.yourMetric}</p>
  </CardContent>
</Card>
```

### Modifying Pipeline Steps

Edit the `steps` array in `frontend/components/RealtimeMonitor.tsx`:

```typescript
const steps = [
  { id: 'idle', label: 'Idle' },
  { id: 'your_step', label: 'Your Custom Step' },
  // ... more steps
]
```

## Development

### Running in Development

```powershell
pnpm dev
# Dashboard: http://localhost:3000
```

### Building for Production

```powershell
pnpm build
pnpm start
```

### Type Checking

```powershell
pnpm tsc --noEmit
```

## Troubleshooting

### WebSocket Connection Failed

**Symptom**: "WebSocket connection to 'ws://localhost:8000/ws' failed"

**Solutions**:
1. Ensure webhook server is running: `python webhook_server.py`
2. Check that uvicorn has WebSocket support: `uv pip install "uvicorn[standard]"`
3. Verify port 8000 is not blocked by firewall
4. Check server logs for errors

### Dashboard Not Updating

**Symptom**: Events not appearing in real-time

**Solutions**:
1. Check browser console for WebSocket errors
2. Verify webhook server is receiving events (check server logs)
3. Ensure WebSocket connection shows "connected" in dashboard
4. Try refreshing the page (Ctrl+R)

### TypeScript Errors

**Symptom**: Type errors during development

**Solutions**:
1. Run `pnpm install` to ensure all types are installed
2. Check that all imports have proper type definitions
3. Verify status literals match expected values

## Performance

The dashboard is optimized for real-time performance:

- **Lazy Loading**: Components loaded on demand
- **Debounced Updates**: Prevents UI thrashing during rapid events
- **Efficient Rendering**: React memoization and keys
- **Limited History**: Event log capped at 20-50 events
- **WebSocket Reconnect**: Automatic reconnection on disconnect

## Best Practices

1. **Keep WebSocket server running** for real-time updates
2. **Monitor browser console** for connection issues
3. **Click events to inspect** full webhook payloads
4. **Watch pipeline steps** to understand flow
5. **Check stats panel** for high-level metrics

## Future Enhancements

Potential features for future versions:

- [ ] Historical event search
- [ ] Export event logs to CSV
- [ ] Configurable alert notifications
- [ ] Dark/light theme toggle
- [ ] Multiple project monitoring
- [ ] Performance metrics graphs
- [ ] Annotation preview thumbnails
- [ ] Dataset comparison tool

## Support

For dashboard-specific issues:
- Check browser developer console (F12)
- Review Next.js logs in terminal
- Verify WebSocket connection in Network tab

For backend issues:
- See main README.md
- Check webhook server logs
- Verify Label Studio and ClearML connectivity
