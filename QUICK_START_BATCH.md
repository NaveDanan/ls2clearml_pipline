# Quick Start Guide - Batch Annotation System

## Start the System (3 Commands)

### 1. Start Optimized Webhook Server
```powershell
# In project root directory
python webhook_server_optimized.py
```

**Expected Output:**
```
INFO - Batch manager initialized: interval=30min, min_size=1, max_size=1000
INFO - Batch scheduler started (interval: 30 minutes)
INFO - Next batch process scheduled at XX:XX:XX
INFO - Task queue started with 3 workers
INFO - Webhook server started with optimized async processing and batch annotation system (interval: 30 minutes)
INFO - Application startup complete.
INFO - Uvicorn running on http://0.0.0.0:8000
```

### 2. Start Frontend Dashboard
```powershell
# In new terminal
cd frontend
pnpm run dev
# or: npm run dev
```

**Expected Output:**
```
  ▲ Next.js 14.x.x
  - Local:        http://localhost:3000
  - Network:      http://192.168.x.x:3000

 ✓ Ready in XXXms
```

### 3. Start Label Studio (if not running)
```powershell
# In new terminal
cd ..  # back to project root
docker-compose up
```

## Test the Batch System

### Step 1: Open Dashboard
Open browser: **http://localhost:3000**

You should see:
- **Main stats** (4 cards)
- **Batch Annotation System** section with:
  - Pending Annotations: 0
  - Datasets Created: 0
  - Next Scheduled: (30 min from now)
  - Batch Interval: 30 min
  - **[Process Batches Now]** button
- **Task Queue Statistics** (if optimized server)
- **Real-time Monitor**

### Step 2: Create Annotations
1. Go to **Label Studio**: http://localhost:8080
2. Open your project
3. **Annotate 5-10 images** (or create/update any annotations)

### Step 3: Watch the Dashboard
After each annotation:
- ✅ **Pending Annotations** count increases
- ✅ **Real-time Monitor** shows "batching_annotations" step
- ✅ Webhook response: **< 10ms** (vs 51 seconds before!)
- ✅ **Next Scheduled** shows when dataset will be created

### Step 4: Test Manual Trigger
**Option A: Use UI Button**
- Click **"Process Batches Now"** button
- Watch real-time updates

**Option B: Use API**
```powershell
curl -X POST http://localhost:8000/batch/process-all
```

### Step 5: Verify Results
Check **ClearML**:
- Go to: https://app.clear.ml
- Navigate to your project
- See new dataset version with batched annotations

## What You Should See

### Console Output (Server)

**When annotations are created:**
```
INFO - Received webhook: ANNOTATION_CREATED
INFO - Submitted task abc123 to queue (priority: 5)
INFO - Processing annotation update for project 1, action: ANNOTATION_CREATED
INFO - Retrieved 1 annotations from Label Studio
INFO - Added annotation (task 1) to batch for project 1. Total: 1
INFO - Added 1 annotations to batch for project 1. Current batch size: 1
```

**Every 30 minutes (automatic):**
```
INFO - Next batch process scheduled at 10:30:00
INFO - Processing all batches (force=False)
INFO - Processing batch for project 1 with 5 annotations
INFO - Successfully processed batch for project 1. Dataset: abc123..., Annotations: 5
INFO - Cleared batch for project 1. Processed 5 annotations
INFO - Batch processing complete: 1 success, 0 skipped, 0 errors
```

**When you click "Process Batches Now":**
```
INFO - Manual batch processing triggered via API for all projects
INFO - Processing all batches (force=True)
INFO - Processing batch for project 1 with 5 annotations
INFO - Successfully processed batch. Dataset: xyz789, Annotations: 5
```

### Dashboard Updates (Frontend)

**Real-time step updates:**
```
1. webhook_received → "Processing ANNOTATION_CREATED for project 1"
2. fetching_annotations → "Fetching annotations from Label Studio..."
3. batching_annotations → "Adding 1 annotations to batch..."
4. batched → "Annotations batched. Batch size: 5. Next dataset creation scheduled."
5. idle → "Waiting for events..."
```

**Statistics updates:**
```
Pending Annotations: 0 → 1 → 2 → 3 → 4 → 5
Datasets Created: 0 (until manual trigger or 30 min)
Datasets Created: 0 → 1 (after processing)
Pending Annotations: 5 → 0 (after processing)
```

## Common Scenarios

### Scenario 1: High-Volume Annotation (1000+ images)
```
Annotate 1000 images rapidly
    ↓
Batch reaches 1000 (max_batch_size)
    ↓
AUTO-TRIGGERED processing (before 30 minutes)
    ↓
Dataset created immediately
    ↓
Batch cleared, continues accumulating
```

### Scenario 2: End-of-Day Processing
```
Team annotates throughout the day
    ↓
End of day: 150 annotations pending
    ↓
Click "Process Batches Now"
    ↓
Single dataset version with all 150 annotations
    ↓
Clean start next day
```

### Scenario 3: Regular Schedule
```
Annotations created continuously
    ↓
Every 30 minutes: automatic processing
    ↓
Datasets: 10:00, 10:30, 11:00, 11:30, etc.
    ↓
Predictable versioning schedule
```

## API Quick Reference

### Process All Batches (Manual Trigger)
```powershell
curl -X POST http://localhost:8000/batch/process-all
```

### Process Specific Project
```powershell
curl -X POST http://localhost:8000/batch/process/1
```

### Get Batch Info (All Projects)
```powershell
curl http://localhost:8000/batch/info
```

### Get Batch Info (Specific Project)
```powershell
curl "http://localhost:8000/batch/info?project_id=1"
```

### Get Full Statistics
```powershell
curl http://localhost:8000/stats
```

### Health Check
```powershell
curl http://localhost:8000/health
```

## Configuration Changes

To change batch interval (in `webhook_server_optimized.py`):

```python
# Find this in startup_event():
batch_manager = AnnotationBatchManager(
    batch_interval_minutes=30,   # Change this (15, 60, 120, etc.)
    min_batch_size=1,             # Minimum annotations to process
    max_batch_size=1000           # Auto-trigger threshold
)
```

**Common configurations:**

**Every 15 minutes:**
```python
batch_interval_minutes=15
```

**Every hour:**
```python
batch_interval_minutes=60
```

**Every 2 hours:**
```python
batch_interval_minutes=120
```

**Require at least 10 annotations:**
```python
min_batch_size=10
```

**Auto-process at 500 annotations:**
```python
max_batch_size=500
```

## Verification Checklist

After starting the system, verify:

- [ ] Server running on http://localhost:8000
- [ ] Frontend running on http://localhost:3000
- [ ] Label Studio running on http://localhost:8080
- [ ] Dashboard shows "Batch Annotation System" section
- [ ] Console shows "Batch scheduler started"
- [ ] "Next Scheduled" time is ~30 minutes from now
- [ ] Creating annotation updates "Pending Annotations"
- [ ] Webhook response < 100ms (check console logs)
- [ ] "Process Batches Now" button visible and clickable

## Troubleshooting

### Server won't start
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process if needed (replace PID)
taskkill /PID <PID> /F

# Restart server
python webhook_server_optimized.py
```

### Frontend won't connect
```powershell
# Check if server is running
curl http://localhost:8000/health

# Restart frontend
cd frontend
pnpm run dev
```

### Batch not processing
1. Check console for "Next batch process scheduled at..."
2. Wait for scheduled time OR
3. Click "Process Batches Now" button OR
4. Call API: `curl -X POST http://localhost:8000/batch/process-all`

### No "Batch Annotation System" section
- Verify you're running `webhook_server_optimized.py` (not `webhook_server.py`)
- Check browser console for errors
- Refresh page (Ctrl+F5)

## Performance Expectations

### Webhook Response Time
- **Before**: ~51 seconds per annotation
- **After**: <10 milliseconds
- **Improvement**: 5000x faster

### Dataset Creation
- **Before**: 1 version per annotation (100 annotations = 100 versions)
- **After**: 1 version per batch (100 annotations = 1-3 versions)
- **Improvement**: 95% reduction

### Total Processing Time (1000 annotations)
- **Before**: ~14 hours (sequential)
- **After**: ~30 minutes (scheduled batches)
- **Improvement**: 28x faster

## Next Steps

1. ✅ Test with real Label Studio project
2. ✅ Adjust batch interval if needed
3. ✅ Monitor dashboard statistics
4. ✅ Set up regular annotation workflow
5. ✅ Review ClearML datasets for batched versions

## Support

See full documentation:
- **BATCH_ANNOTATION_GUIDE.md** - Complete guide
- **BATCH_SYSTEM_SUMMARY.md** - Implementation details
- **UI_INTEGRATION_GUIDE.md** - Dashboard integration

---

**Ready to Start!** 🚀

Run the 3 commands above and open http://localhost:3000 to see your batch annotation system in action!
