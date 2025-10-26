# Troubleshooting Guide

Common issues and their solutions for the Label Studio to ClearML pipeline.

## Table of Contents
- [Installation Issues](#installation-issues)
- [Docker Issues](#docker-issues)
- [Connection Issues](#connection-issues)
- [Batch Processing Issues](#batch-processing-issues)
- [Dashboard Issues](#dashboard-issues)
- [Performance Issues](#performance-issues)
- [Data Issues](#data-issues)

## Installation Issues

### Python Version Too Old

**Symptom:** `Python 3.11 or higher required`

**Solution:**
```powershell
# Download Python 3.11+ from python.org
# Or use pyenv
pyenv install 3.11.6
pyenv global 3.11.6
```

### Package Installation Fails

**Symptom:** `ERROR: Could not find a version that satisfies the requirement...`

**Solution:**
```powershell
# Update pip
python -m pip install --upgrade pip

# Clear cache and reinstall
pip cache purge
pip install -e . --force-reinstall
```

### Permission Denied

**Symptom:** `PermissionError: [Errno 13] Permission denied`

**Solution:**
```powershell
# Windows: Run as Administrator
# OR use virtual environment
python -m venv venv
.\venv\Scripts\activate
pip install -e .
```

## Docker Issues

### Docker Not Running

**Symptom:** `Cannot connect to the Docker daemon`

**Solution:**
1. Open Docker Desktop
2. Wait for it to fully start (whale icon should be steady, not animated)
3. Verify: `docker ps`

### Port Already in Use

**Symptom:** `port is already allocated`

**Find what's using the port:**
```powershell
# Windows
netstat -ano | findstr :8090

# Kill process (replace PID)
taskkill /PID <PID> /F
```

**Or change the port** in `docker-compose.yml`:
```yaml
ports:
  - "8091:8080"  # Changed from 8090
```

### Out of Memory

**Symptom:** `Elasticsearch` or services crash unexpectedly

**Solution:**
1. Open Docker Desktop
2. Settings → Resources
3. Increase Memory to 12 GB
4. Click Apply & Restart

### Volume Mount Fails

**Symptom:** `Error response from daemon: invalid mount config`

**Solution:**
```powershell
# Ensure directory exists
New-Item -ItemType Directory -Force -Path .\shared-data

# Restart Docker
docker-compose down
docker-compose up -d
```

## Connection Issues

### Label Studio 502 Bad Gateway

**Symptom:** Browser shows "502 Bad Gateway"

**Solution:**
```powershell
# Wait 60-90 seconds after docker-compose up
# Check logs
docker-compose logs label-studio

# If still failing, restart
docker-compose restart label-studio
```

### ClearML 401 Unauthorized

**Symptom:** `401 Unauthorized` when accessing ClearML API

**Solution:**
```powershell
# Delete old configuration
Remove-Item ~/.clearml.conf

# Reinitialize with fresh credentials
clearml-init

# Get new credentials from https://app.clear.ml/settings/workspace-configuration
```

### Webhook Server Connection Refused

**Symptom:** Label Studio can't reach webhook

**Solution:**
```powershell
# Check webhook server is running
curl http://localhost:8000/health

# Verify URL in Label Studio webhook settings
# Should be: http://host.docker.internal:8000/webhook/label-studio

# Windows firewall may block it - add exception
```

### WebSocket Connection Failed

**Symptom:** Dashboard shows "WebSocket connection failed"

**Solution:**
```powershell
# Ensure webhook server is running
python webhook_server_optimized.py

# Check if port 8000 is accessible
curl http://localhost:8000/health

# Browser may block WS - try different browser
# Check browser console for specific error
```

## Batch Processing Issues

### Batches Not Processing

**Symptom:** Annotations accumulate but dataset never created

**Check batch info:**
```powershell
curl http://localhost:8000/batch/info
```

**Solutions:**
1. **Wait for scheduled time** - Check "next_scheduled_process" in stats
2. **Manual trigger** - Click "Process Batches Now" or:
   ```powershell
   curl -X POST http://localhost:8000/batch/process-all
   ```
3. **Check min_batch_size** - Batch may be too small:
   ```python
   # In webhook_server_optimized.py
   min_batch_size=1  # Lower threshold
   ```

### Batches Processing Too Frequently

**Symptom:** Datasets created more often than expected

**Cause:** Batch reaching `max_batch_size` (1000 by default)

**Solution:**
```python
# In webhook_server_optimized.py
batch_manager = AnnotationBatchManager(
    batch_interval_minutes=30,
    max_batch_size=5000  # Increase threshold
)
```

### Scheduler Not Running

**Symptom:** No "Batch scheduler started" message in logs

**Solution:**
```powershell
# Ensure using optimized server
python webhook_server_optimized.py

# Check logs for errors
# Verify asyncio is working
python -c "import asyncio; print(asyncio.run(asyncio.sleep(0)))"
```

### Duplicate Annotations

**Symptom:** Same annotation processed multiple times

**Note:** System auto-deduplicates by task ID - this shouldn't happen

**Check:** Review logs for "avoid duplicates" messages

**If persisting:**
```powershell
# Clear batch manually
curl -X POST http://localhost:8000/batch/process-all

# Restart server
# Ctrl+C then python webhook_server_optimized.py
```

## Dashboard Issues

### Dashboard Not Loading

**Symptom:** Blank page or loading forever

**Solution:**
```powershell
# Check if frontend is running
curl http://localhost:3000

# Restart frontend
cd frontend
pnpm run dev

# Check browser console for errors (F12)
# Try incognito mode to rule out cache
```

### No Real-Time Updates

**Symptom:** Dashboard doesn't update when annotations created

**Solutions:**
1. **Check WebSocket** - Browser console should show `WebSocket connected`
2. **Verify webhook server** - Should be running on port 8000
3. **Create annotation** - System needs events to process
4. **Refresh page** - Hard refresh: Ctrl+Shift+R

### Batch Stats Not Showing

**Symptom:** "Batch Annotation System" section missing

**Cause:** Running original server instead of optimized

**Solution:**
```powershell
# Stop current server (Ctrl+C)
# Start webhook server via CLI
uv run .\main.py webhook
```

### Stats Showing Wrong Values

**Symptom:** Numbers don't match actual data

**Solution:**
```powershell
# Restart webhook server to reset stats
# Refresh dashboard (F5)

# Manually query stats
curl http://localhost:8000/stats
```

## Performance Issues

### Slow Webhook Response

**Symptom:** Webhooks taking >1 second to respond

**Expected:** <10ms with optimized server

**Solutions:**
1. **Use optimized server:**
   ```powershell
   python webhook_server_optimized.py
   ```
2. **Increase workers:**
   ```python
   # In webhook_server_optimized.py
   await task_queue.start(num_workers=5)
   ```
3. **Enable Redis** for distributed queue

### High Memory Usage

**Symptom:** Server consuming >2GB RAM

**Solutions:**
```python
# Reduce max_events
max_events = 50  # Default 100

# Process batches more frequently
batch_interval_minutes=15  # Default 30

# Limit queue size
# Enable Redis for persistence
```

### Slow Dataset Creation

**Symptom:** Dataset creation takes >2 minutes

**Causes & Solutions:**
1. **Large images** - Compress before upload
2. **Many annotations** - Increase batch size to process in larger chunks
3. **Network latency** - Use ClearML self-hosted
4. **Shared storage not configured** - See [Shared Storage Guide](../deployment/shared-storage.md)

## Data Issues

### Images Not Uploading to ClearML

**Symptom:** Dataset contains annotations but no images

**Most Common:** Shared storage not configured

**Solutions:**
1. **Configure shared storage** - See [Shared Storage Guide](../deployment/shared-storage.md)
2. **Check file paths** in annotations JSON
3. **Verify files exist:**
   ```powershell
   ls shared-data\upload\ -Recurse
   ```
4. **Check server logs** for "Adding local image" messages

### Annotations Missing

**Symptom:** Some annotations not in ClearML dataset

**Causes:**
1. **Batch not processed yet** - Wait for scheduled processing or trigger manually
2. **Annotation created after batch** - Will be in next batch
3. **Failed to fetch** - Check webhook server logs for errors

**Verify:**
```powershell
# Check batch info
curl http://localhost:8000/batch/info

# Check pending annotations
# Should show current batch sizes
```

### Dataset Version Conflicts

**Symptom:** ClearML shows multiple versions unexpectedly

**Cause:** Using immediate processing (old system) instead of batching

**Solution:**
- Use `webhook_server_optimized.py`
- Batching creates fewer versions

### Corrupted Dataset

**Symptom:** Dataset won't open or shows errors

**Solution:**
```powershell
# Create new dataset version
curl -X POST http://localhost:8000/batch/process/1

# Or finalize in ClearML UI
# Go to dataset → Actions → Finalize
```

## Advanced Troubleshooting

### Enable Debug Logging

**For detailed logs:**
```python
# In webhook_server_optimized.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Component Health

```powershell
# Label Studio
docker-compose ps
docker-compose logs label-studio

# Webhook Server
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000

# ClearML
python -c "from clearml import Task; print('OK')"
```

### Reset Everything

**Nuclear option** - complete reset:
```powershell
# Stop all services
docker-compose down -v
Ctrl+C  # Stop webhook server
Ctrl+C  # Stop frontend

# Remove data
Remove-Item -Recurse -Force shared-data

# Restart
docker-compose up -d
python webhook_server_optimized.py
cd frontend && pnpm run dev
```

## Getting More Help

### Check Logs

**Webhook Server:**
- Console output shows all processing
- Look for ERROR or WARNING messages

**Docker Services:**
```powershell
docker-compose logs -f label-studio
docker-compose logs -f labelstudio-postgres
```

**Frontend:**
- Browser console (F12)
- Network tab for failed requests

### Community Support

- **GitHub Issues**: Report bugs
- **GitHub Discussions**: Ask questions
- **ClearML Slack**: MLOps help
- **Label Studio Slack**: Annotation help

### Diagnostic Information

When reporting issues, include:
```powershell
# System info
python --version
docker --version
node --version

# Service status
docker-compose ps
curl http://localhost:8000/health
curl http://localhost:8000/stats

# Logs (last 50 lines)
docker-compose logs --tail=50 label-studio

# Environment (redact secrets!)
cat .env
```

---

**Last Updated**: October 26, 2025  
**Difficulty**: Varies  
**Related**: [Quick Start](../getting-started/quick-start.md), [Installation](../getting-started/installation.md)
