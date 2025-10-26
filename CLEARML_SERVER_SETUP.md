# ClearML Self-Hosted Server Setup

This guide explains how to run ClearML Server locally using Docker Compose, with shared storage access to Label Studio.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Shared Volume: ./shared-data                  │
│                  (Accessible by both systems)                    │
└────────────┬──────────────────────────────┬─────────────────────┘
             │                              │
             ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│   Label Studio Stack    │    │    ClearML Stack        │
├─────────────────────────┤    ├─────────────────────────┤
│ • Label Studio :8090    │    │ • Web UI :8080          │
│ • PostgreSQL :5432      │    │ • API Server :8008      │
│ • /shared-data volume   │    │ • File Server :8081     │
└─────────────────────────┘    │ • MongoDB :27017        │
                               │ • Elasticsearch :9200    │
                               │ • Redis :6379           │
                               │ • /shared-data volume   │
                               └─────────────────────────┘
```

## Deployment Options

### Option 1: Run Only ClearML (Separate from Label Studio)

```powershell
# Start ClearML server stack
docker-compose -f docker-compose.clearml.yml up -d

# Check status
docker-compose -f docker-compose.clearml.yml ps

# View logs
docker-compose -f docker-compose.clearml.yml logs -f
```

**Services Started:**
- ClearML Web UI: http://localhost:8080
- ClearML API: http://localhost:8008
- ClearML Files: http://localhost:8081
- MongoDB: localhost:27017
- Elasticsearch: localhost:9200
- Redis: localhost:6379

### Option 2: Run Only Label Studio (Original Setup)

```powershell
# Start Label Studio stack
docker-compose up -d

# Check status
docker-compose ps
```

**Services Started:**
- Label Studio: http://localhost:8090 (changed from 8080 to avoid conflict)
- PostgreSQL: localhost:5432

### Option 3: Run Full Stack (Both Systems Together)

```powershell
# Start everything at once
docker-compose -f docker-compose.full.yml up -d

# Check all services
docker-compose -f docker-compose.full.yml ps

# View logs
docker-compose -f docker-compose.full.yml logs -f
```

**All Services:**
- **Label Studio**: http://localhost:8090
- **ClearML Web**: http://localhost:8080
- **ClearML API**: http://localhost:8008
- **ClearML Files**: http://localhost:8081
- PostgreSQL: localhost:5432
- MongoDB: localhost:27017
- Elasticsearch: localhost:9200
- Redis: localhost:6379

## Shared Storage Configuration

All deployments share the same volume for file management:

```
./shared-data → /shared-data (in all containers)
```

### Directory Structure

```
shared-data/
├── upload/              # Label Studio uploaded images
│   ├── 1/              # Project 1 files
│   ├── 2/              # Project 2 files
│   └── ...
├── datasets/           # ClearML datasets (optional)
└── models/             # ClearML models (optional)
```

### Benefits of Shared Storage

✅ **No File Duplication**: Same files used by both systems  
✅ **No HTTP Downloads**: Direct file system access  
✅ **Faster Processing**: No network overhead  
✅ **Disk Space Savings**: Single copy of all images  
✅ **Simplified Management**: One location for all files  

## First-Time Setup

### 1. Create Shared Data Directory

```powershell
# Create the directory if it doesn't exist
New-Item -ItemType Directory -Force -Path .\shared-data
New-Item -ItemType Directory -Force -Path .\shared-data\upload
```

### 2. Start Services

**For Full Stack:**
```powershell
docker-compose -f docker-compose.full.yml up -d
```

**Wait for all services to be healthy** (~2-3 minutes):
```powershell
docker-compose -f docker-compose.full.yml ps
```

### 3. Access ClearML Web UI

Open browser: **http://localhost:8080**

**First Login:**
- ClearML will prompt you to create an account
- No authentication required for local deployment
- Create credentials (saved in browser)

### 4. Generate ClearML API Credentials

1. Go to http://localhost:8080
2. Click on your profile (top right)
3. Go to **Settings** → **Workspace** → **Create new credentials**
4. Copy the generated credentials:
   ```
   api {
     web_server: http://localhost:8080
     api_server: http://localhost:8008
     files_server: http://localhost:8081
     credentials {
       "access_key" = "YOUR_ACCESS_KEY"
       "secret_key" = "YOUR_SECRET_KEY"
     }
   }
   ```

### 5. Configure Local ClearML Client

**Option A: Interactive Setup**
```powershell
clearml-init
```

Enter when prompted:
- API Server: `http://localhost:8008`
- Web Server: `http://localhost:8080`
- Files Server: `http://localhost:8081`
- Access Key: (from step 4)
- Secret Key: (from step 4)

**Option B: Manual Configuration**

Edit `~/clearml.conf`:
```ini
api {
    web_server: http://localhost:8080
    api_server: http://localhost:8008
    files_server: http://localhost:8081
    credentials {
        "access_key" = "YOUR_ACCESS_KEY"
        "secret_key" = "YOUR_SECRET_KEY"
    }
}
```

### 6. Update Environment Variables

Edit your `.env` file:
```env
# ClearML Self-Hosted
CLEARML_WEB_HOST=http://localhost:8080
CLEARML_API_HOST=http://localhost:8008
CLEARML_FILES_HOST=http://localhost:8081
CLEARML_API_ACCESS_KEY=YOUR_ACCESS_KEY
CLEARML_API_SECRET_KEY=YOUR_SECRET_KEY

# Label Studio (updated port)
LABEL_STUDIO_URL=http://localhost:8090
LABEL_STUDIO_API_KEY=your-label-studio-token

# Shared Storage
SHARED_DATA_DIR=./shared-data
```

### 7. Configure Label Studio Storage

Since Label Studio now runs on port **8090**:

1. Open http://localhost:8090
2. Create account / Login
3. Generate API token (Settings → Account → Access Token)
4. Configure Cloud Storage:
   - Go to **Settings** → **Cloud Storage** → **Add Source Storage**
   - **Storage Type**: Local files
   - **Absolute local path**: `/shared-data/upload`
   - **File Filter Regex**: `.*\.(jpg|jpeg|png|bmp|gif|svg)$`
   - **Treat every bucket object as a source file**: ✓
   - Save

## Service Management

### Start Services
```powershell
# Full stack
docker-compose -f docker-compose.full.yml up -d

# Only ClearML
docker-compose -f docker-compose.clearml.yml up -d

# Only Label Studio
docker-compose up -d
```

### Stop Services
```powershell
# Full stack
docker-compose -f docker-compose.full.yml down

# Only ClearML
docker-compose -f docker-compose.clearml.yml down

# Only Label Studio
docker-compose down
```

### View Logs
```powershell
# All services
docker-compose -f docker-compose.full.yml logs -f

# Specific service
docker-compose -f docker-compose.full.yml logs -f clearml-apiserver
docker-compose -f docker-compose.full.yml logs -f label-studio
```

### Restart Services
```powershell
# Restart all
docker-compose -f docker-compose.full.yml restart

# Restart specific service
docker-compose -f docker-compose.full.yml restart clearml-apiserver
```

### Check Status
```powershell
docker-compose -f docker-compose.full.yml ps
```

### Remove Everything (Including Data)
```powershell
# ⚠️ WARNING: This deletes all data!
docker-compose -f docker-compose.full.yml down -v
```

## Resource Requirements

### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 20 GB free space

### Recommended Requirements
- **CPU**: 8 cores
- **RAM**: 16 GB
- **Disk**: 50 GB free space (for datasets and models)

### Docker Resource Limits

Edit Docker Desktop settings:
- **Memory**: At least 8 GB (12 GB recommended)
- **Disk**: At least 60 GB

## Ports Summary

| Service              | Port  | Purpose                        |
|---------------------|-------|--------------------------------|
| Label Studio        | 8090  | Annotation UI                  |
| ClearML Web         | 8080  | ClearML Dashboard              |
| ClearML API         | 8008  | API Server                     |
| ClearML Files       | 8081  | File Server                    |
| PostgreSQL          | 5432  | Label Studio Database          |
| MongoDB             | 27017 | ClearML Database               |
| Elasticsearch       | 9200  | ClearML Search                 |
| Redis               | 6379  | ClearML Cache                  |

## Troubleshooting

### ClearML UI Not Loading

**Check if services are running:**
```powershell
docker-compose -f docker-compose.full.yml ps
```

**Check API server logs:**
```powershell
docker-compose -f docker-compose.full.yml logs clearml-apiserver
```

**Restart services:**
```powershell
docker-compose -f docker-compose.full.yml restart clearml-apiserver clearml-webserver
```

### Elasticsearch Won't Start

**Error**: `max virtual memory areas vm.max_map_count [65530] is too low`

**Solution** (Windows with WSL2):
```powershell
# In WSL2 terminal
wsl -d docker-desktop
sysctl -w vm.max_map_count=262144
```

**Permanent fix** - Create/edit `C:\Users\<YourUser>\.wslconfig`:
```ini
[wsl2]
kernelCommandLine = "sysctl.vm.max_map_count=262144"
```

### Services Can't Connect to MongoDB/Elasticsearch

**Check network:**
```powershell
docker network inspect ls2clearml_pipline_shared_network
```

**Restart dependent services:**
```powershell
docker-compose -f docker-compose.full.yml restart clearml-apiserver
```

### Port Conflicts

**Find what's using a port:**
```powershell
netstat -ano | findstr :8080
```

**Change port in docker-compose.full.yml:**
```yaml
ports:
  - "8081:80"  # Change 8080 to 8081
```

### Shared Volume Not Working

**Check volume mount:**
```powershell
docker exec clearml-fileserver ls -la /shared-data
docker exec label-studio ls -la /shared-data
```

**Should see files in both containers:**
```
drwxr-xr-x  upload/
```

## Webhook Server Configuration

Update `config.py` to use local ClearML:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ClearML Self-Hosted
    clearml_web_host: str = "http://localhost:8080"
    clearml_api_host: str = "http://localhost:8008"
    clearml_files_host: str = "http://localhost:8081"
    
    # ... rest of config
```

## Testing the Setup

### 1. Test Label Studio
```powershell
# Open browser
start http://localhost:8090
```

### 2. Test ClearML
```powershell
# Open browser
start http://localhost:8080
```

### 3. Test Shared Storage
```powershell
# Upload file to Label Studio
# Check it appears in both containers:

docker exec label-studio ls /shared-data/upload
docker exec clearml-fileserver ls /shared-data/upload
```

### 4. Test API Connection
```powershell
# Test ClearML API
curl http://localhost:8008/v2.23/server.info

# Test File Server
curl http://localhost:8081/
```

### 5. Run Pipeline Test
```powershell
# Start webhook server
python webhook_server_optimized.py

# Create annotation in Label Studio
# Verify dataset appears in ClearML
```

## Backup and Restore

### Backup Volumes
```powershell
# Stop services
docker-compose -f docker-compose.full.yml down

# Backup
docker run --rm -v ls2clearml_pipline_mongo_data:/data -v ${PWD}:/backup ubuntu tar czf /backup/mongo_backup.tar.gz /data
docker run --rm -v ls2clearml_pipline_elasticsearch_data:/data -v ${PWD}:/backup ubuntu tar czf /backup/elasticsearch_backup.tar.gz /data

# Backup shared data
tar -czf shared_data_backup.tar.gz ./shared-data
```

### Restore Volumes
```powershell
# Restore
docker run --rm -v ls2clearml_pipline_mongo_data:/data -v ${PWD}:/backup ubuntu tar xzf /backup/mongo_backup.tar.gz -C /

# Restore shared data
tar -xzf shared_data_backup.tar.gz
```

## Production Considerations

### Security
- Change default MongoDB password
- Enable authentication on Redis
- Use HTTPS with reverse proxy (nginx)
- Restrict network access

### Performance
- Increase Elasticsearch heap size for large datasets
- Use SSD for Docker volumes
- Monitor resource usage

### High Availability
- Use external MongoDB cluster
- Use managed Elasticsearch service
- Load balance API servers

## Summary

✅ **ClearML Self-Hosted**: Running locally on Docker  
✅ **Label Studio Integration**: Shared volume access  
✅ **Complete Stack**: All services in one docker-compose  
✅ **Production Ready**: Scalable architecture  
✅ **Easy Management**: Simple commands to start/stop  

---

**Quick Start Command:**
```powershell
docker-compose -f docker-compose.full.yml up -d
```

**Access:**
- Label Studio: http://localhost:8090
- ClearML: http://localhost:8080
- Webhook Dashboard: http://localhost:3000

---

**Created**: October 26, 2025  
**Version**: 1.0
