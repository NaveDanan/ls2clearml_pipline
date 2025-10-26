# Batch Annotation System - Visual Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER WORKFLOW                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  1. Annotate Images          2. View Progress         3. Trigger Dataset │
│     in Label Studio             in Dashboard              Creation       │
│         ↓                           ↓                         ↓          │
│    ┌─────────┐               ┌─────────┐               ┌─────────┐     │
│    │  Label  │               │Frontend │               │ Process │     │
│    │ Studio  │───webhooks───▶│Dashboard│◀───WebSocket──│ Button  │     │
│    │:8080    │               │:3000    │               └─────────┘     │
│    └─────────┘               └─────────┘                                │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ WebSocket (real-time updates)
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    WEBHOOK SERVER (:8000)                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  POST /webhook/label-studio                                     │    │
│  │  ├─ Receive webhook (<1ms)                                      │    │
│  │  ├─ Add to task queue                                           │    │
│  │  └─ Return 202 Accepted                                         │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                           ↓                                              │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Task Queue (3 async workers)                                   │    │
│  │  ├─ Worker 1: Fetch annotations from LS                         │    │
│  │  ├─ Worker 2: Fetch annotations from LS                         │    │
│  │  └─ Worker 3: Fetch annotations from LS                         │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                           ↓                                              │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Annotation Batch Manager                                       │    │
│  │  ┌──────────────────────────────────────────────────────┐      │    │
│  │  │  Project 1 Batch:  [ann1, ann2, ann3, ann4, ann5]    │      │    │
│  │  │  Project 2 Batch:  [ann1, ann2, ann3]                │      │    │
│  │  │  Project 3 Batch:  [ann1]                             │      │    │
│  │  └──────────────────────────────────────────────────────┘      │    │
│  │                                                                  │    │
│  │  Scheduler: Every 30 minutes                                    │    │
│  │  ┌─────────────────────────────────────┐                       │    │
│  │  │ Timer → Process All Batches         │                       │    │
│  │  │      → Create Dataset Versions      │                       │    │
│  │  │      → Clear Batches                │                       │    │
│  │  └─────────────────────────────────────┘                       │    │
│  │                                                                  │    │
│  │  Manual Triggers:                                               │    │
│  │  • POST /batch/process-all                                      │    │
│  │  • POST /batch/process/{project_id}                             │    │
│  │  • UI Button click                                              │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                           ↓                                              │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  ClearML Manager                                                │    │
│  │  ├─ Create dataset version                                      │    │
│  │  ├─ Add annotations JSON                                        │    │
│  │  ├─ Add images from shared volume                               │    │
│  │  └─ Finalize and upload                                         │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLEARML (api.clear.ml)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Dataset Versions:                                                       │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │ v1.0 ── v1.1 ── v1.2 ── v1.3                                  │      │
│  │  ↑       ↑       ↑       ↑                                     │      │
│  │  50     45      38      52  (annotations per version)         │      │
│  │ 10:00  10:30   11:00   11:30 (batch times)                    │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Processing Timeline

### Immediate Processing (OLD)
```
Time:   0s    51s   102s  153s  204s  255s  306s  357s  408s  459s  510s
        │     │     │     │     │     │     │     │     │     │     │
Annot:  1─────┘     2─────┘     3─────┘     4─────┘     5─────┘     6─────┘
        │           │           │           │           │           │
Dataset:v1.0        v1.1        v1.2        v1.3        v1.4        v1.5

Total: 10 annotations = 510 seconds (~8.5 minutes) = 10 dataset versions
```

### Batch Processing (NEW)
```
Time:   0s    1s    2s    3s    4s    5s    ...   1800s (30 min)
        │     │     │     │     │     │            │
Annot:  1──┐  2──┐  3──┐  4──┐  5──┐  6──┐  ...  100──┐
           │     │     │     │     │     │            │
Batch:     │     │     │     │     │     │            │
[1]────────┘     │     │     │     │     │            │
[1,2]────────────┘     │     │     │     │            │
[1,2,3]────────────────┘     │     │     │            │
[1,2,3,4]────────────────────┘     │     │            │
[1,2,3,4,5]────────────────────────┘     │            │
[1,2,3,4,5,6]────────────────────────────┘            │
...                                                    │
[1,2,3,...,100]────────────────────────────────────────┘
                                                       │
Dataset:                                          v1.0 (100 annotations)

Total: 100 annotations = 30 minutes + 17s = 1 dataset version
Efficiency: 83x faster, 99% fewer dataset versions
```

## Data Flow

### 1. Annotation Created
```
┌─────────────┐
│   Label     │  User annotates image
│   Studio    │
└──────┬──────┘
       │ HTTP POST
       │ /webhook/label-studio
       ▼
┌─────────────┐
│  Webhook    │  Receive webhook (Action: ANNOTATION_CREATED)
│  Endpoint   │  Validate signature
└──────┬──────┘  Return 202 Accepted (<10ms)
       │
       │ Add to queue
       ▼
┌─────────────┐
│  Task       │  3 async workers
│  Queue      │  Process in parallel
└──────┬──────┘
       │
       │ Async fetch
       ▼
┌─────────────┐
│  Label      │  GET /api/projects/{id}/export
│  Studio API │  Fetch all annotations
└──────┬──────┘
       │
       │ Annotations JSON
       ▼
┌─────────────┐
│  Batch      │  Add to in-memory batch
│  Manager    │  Deduplicate by task ID
└──────┬──────┘  Track size and age
       │
       │ WebSocket broadcast
       ▼
┌─────────────┐
│  Frontend   │  Update "Pending Annotations"
│  Dashboard  │  Show real-time progress
└─────────────┘
```

### 2. Scheduled Processing
```
┌─────────────┐
│  Scheduler  │  Timer: Every 30 minutes
│  Loop       │
└──────┬──────┘
       │ Trigger
       ▼
┌─────────────┐
│  Batch      │  For each project:
│  Manager    │  ├─ Check batch size >= min_batch_size
└──────┬──────┘  └─ Process if valid
       │
       │ For each batch
       ▼
┌─────────────┐
│  ClearML    │  Create dataset version
│  Manager    │  ├─ Add annotations JSON
└──────┬──────┘  ├─ Add images from shared volume
       │          └─ Finalize and upload
       │
       │ Dataset created
       ▼
┌─────────────┐
│  Batch      │  Clear processed batch
│  Manager    │  Reset counters
└──────┬──────┘
       │
       │ WebSocket broadcast
       ▼
┌─────────────┐
│  Frontend   │  Update stats:
│  Dashboard  │  ├─ Pending: 15 → 0
└─────────────┘  ├─ Datasets: 0 → 1
                 └─ Next: (new time)
```

### 3. Manual Trigger
```
┌─────────────┐
│  Frontend   │  User clicks "Process Batches Now"
│  Dashboard  │
└──────┬──────┘
       │ POST /batch/process-all
       ▼
┌─────────────┐
│  Webhook    │  API endpoint
│  Server     │
└──────┬──────┘
       │ Call batch_manager.process_all_now()
       ▼
┌─────────────┐
│  Batch      │  Force process (ignore min_batch_size)
│  Manager    │  Process ALL batches
└──────┬──────┘
       │
       │ For each batch
       ▼
┌─────────────┐
│  ClearML    │  Create dataset versions
│  Manager    │
└──────┬──────┘
       │
       │ Results
       ▼
┌─────────────┐
│  Frontend   │  Show results via WebSocket
│  Dashboard  │  Update all statistics
└─────────────┘
```

## Dashboard Layout

```
┌────────────────────────────────────────────────────────────────────┐
│  Label Studio to ClearML Pipeline                                  │
│  Real-time Annotation Processing Dashboard                         │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────┐│
│  │Total Annot.  │  │Dataset Ver.  │  │Last Sync     │  │Webhooks││
│  │     150      │  │   v1.2.3     │  │  10:30 AM    │  │   2    ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────┘│
│                                                                     │
│  🔲 Batch Annotation System            [📊 Process Batches Now]   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────┐│
│  │Pending Ann.  │  │Datasets      │  │Next Scheduled│  │Interval││
│  │     18       │  │Created: 5    │  │  11:00 AM    │  │ 30 min ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────┘│
│                                                                     │
│  ⚡ Task Queue Statistics                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────┐│
│  │Queue Size    │  │Tasks         │  │Failed        │  │Workers ││
│  │      3       │  │Completed: 50 │  │      0       │  │  2/3   ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────┘│
│                                                                     │
│  📊 Real-time Monitor                                              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Current Step: batching_annotations                           │ │
│  │ 🟢 Adding 5 annotations to batch...                          │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  📋 Recent Events                                                  │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ 10:29:45 - annotations_batched        [Expand ▼]            │ │
│  │ 10:29:30 - annotations_fetched        [Expand ▼]            │ │
│  │ 10:29:15 - webhook_received           [Expand ▼]            │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

## Batch States

```
┌─────────────────────────────────────────────────────────────────┐
│                    BATCH LIFECYCLE                               │
└─────────────────────────────────────────────────────────────────┘

State 1: EMPTY
┌──────────────┐
│ Batch        │  Size: 0
│ (Project 1)  │  Age: 0s
└──────────────┘  Status: Idle
       ↓ Add annotation
       
State 2: ACCUMULATING
┌──────────────┐
│ Batch        │  Size: 1, 2, 3, ... 15
│ [ann1, ann2, │  Age: 0s → 1800s (30 min)
│  ann3, ...]  │  Status: Waiting for schedule
└──────────────┘
       ↓ Timer triggers OR Manual trigger OR Max size reached
       
State 3: PROCESSING
┌──────────────┐
│ Batch        │  Size: 15
│ [locked]     │  Age: 1800s
└──────────────┘  Status: Creating dataset...
       ↓ Dataset creation complete
       
State 4: CLEARED
┌──────────────┐
│ Batch        │  Size: 0
│ (Project 1)  │  Age: 0s (reset)
└──────────────┘  Status: Idle (ready for new annotations)
       ↓ Cycle repeats
```

## Performance Metrics Visual

### Webhook Response Time
```
Immediate Processing:    ████████████████████████████████ 51,000ms
Batch Processing:        █ 10ms

Improvement: 5,100x faster
```

### Dataset Versions (100 annotations)
```
Immediate Processing:    ████████████████████████████████ 100 versions
Batch Processing:        ███ 3 versions

Reduction: 97% fewer versions
```

### Total Processing Time (100 annotations)
```
Immediate Processing:    ████████████████████████████████ 85 minutes
Batch Processing:        ██ 5 minutes

Improvement: 17x faster
```

## Configuration Matrix

```
┌─────────────────┬──────────┬──────────┬──────────┬──────────┐
│ Interval        │ 15 min   │ 30 min   │ 60 min   │ 120 min  │
├─────────────────┼──────────┼──────────┼──────────┼──────────┤
│ Datasets/Day    │ 96       │ 48       │ 24       │ 12       │
│ Ideal For       │ Fast     │ Balanced │ Batch    │ Daily    │
│                 │ Feedback │ Default  │ Work     │ Digest   │
└─────────────────┴──────────┴──────────┴──────────┴──────────┘

┌─────────────────┬──────────┬──────────┬──────────┬──────────┐
│ Min Batch Size  │ 1        │ 5        │ 10       │ 50       │
├─────────────────┼──────────┼──────────┼──────────┼──────────┤
│ Processing      │ Always   │ Small    │ Medium   │ Large    │
│ Behavior        │ Process  │ Projects │ Projects │ Projects │
└─────────────────┴──────────┴──────────┴──────────┴──────────┘

┌─────────────────┬──────────┬──────────┬──────────┬──────────┐
│ Max Batch Size  │ 100      │ 500      │ 1000     │ 5000     │
├─────────────────┼──────────┼──────────┼──────────┼──────────┤
│ Auto-Trigger    │ Frequent │ Medium   │ Rare     │ Very     │
│ Frequency       │          │          │ Default  │ Rare     │
└─────────────────┴──────────┴──────────┴──────────┴──────────┘
```

---

**Legend:**
- 🔲 Layers icon = Batch system
- ⚡ Zap icon = Optimized/fast
- 📊 Database icon = Process data
- 📋 List icon = Events
- 🟢 Green = Success/Active
- 🟡 Yellow = Processing
- 🔴 Red = Error
- ⏸️ Gray = Idle

