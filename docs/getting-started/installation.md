# Installation Guide

Complete installation instructions for the Label Studio to ClearML pipeline.

## Table of Contents
- [System Requirements](#system-requirements)
- [Python Setup](#python-setup)
- [Docker Setup](#docker-setup)
- [ClearML Configuration](#clearml-configuration)
- [Label Studio Configuration](#label-studio-configuration)
- [Frontend Setup](#frontend-setup)
- [Verification](#verification)

## System Requirements

### Minimum
- **OS**: Windows 10/11, Ubuntu 20.04+, macOS 11+
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 30 GB free (SSD recommended)
- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **Docker**: Docker Desktop 4.0+

### Recommended
- **CPU**: 8 cores
- **RAM**: 16 GB  
- **Disk**: 50 GB SSD
- **Docker Memory**: 12 GB allocated

## Python Setup

### 1. Verify Python Version
```powershell
python --version
# Should show Python 3.11.x or higher
```

### 2. Install UV (Package Manager)
```powershell
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Clone Repository
```powershell
git clone https://github.com/NaveDanan/ls2clearml_pipline.git
cd ls2clearml_pipline
```

### 4. Install Dependencies
```powershell
# Install project in editable mode
uv pip install -e .

# Or use standard pip
pip install -e .
```

**Expected packages:**
- clearml
- fastapi
- uvicorn
- label-studio-sdk
- python-dotenv
- pydantic-settings
- redis (optional)
- httpx

## Docker Setup

### 1. Install Docker Desktop

**Windows:**
- Download from https://www.docker.com/products/docker-desktop
- Run installer
- Enable WSL2 integration
- Restart computer

**Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER
```

**macOS:**
- Download from https://www.docker.com/products/docker-desktop
- Drag to Applications
- Start Docker Desktop

### 2. Configure Docker Resources

1. Open Docker Desktop
2. Go to **Settings → Resources**
3. Set:
   - **Memory**: 8 GB minimum (12 GB recommended)
   - **Disk**: 60 GB minimum
4. Click **Apply & Restart**

### 3. Verify Docker
```powershell
docker --version
docker-compose --version
docker ps
```

## ClearML Configuration

### 1. Create ClearML Account

1. Go to https://clear.ml
2. Click **Sign Up**
3. Complete registration
4. Verify email

### 2. Get API Credentials

1. Log in to ClearML
2. Click profile icon → **Settings**
3. Navigate to **Workspace → App Credentials**
4. Click **Create new credentials**
5. Copy the generated credentials

### 3. Initialize ClearML

```powershell
clearml-init
```

**Prompts:**
```
ClearML SDK setup process

Please create new clearml credentials through the settings page in your `clearml-server` web app
Navigate to Settings -> Workspace -> Create new credentials

Or create a free account at https://app.clear.ml/settings/workspace-configuration

In the settings page, press "Create new credentials", then press "Copy to clipboard".
Paste copied configuration here:
```

**Paste your credentials** (should look like):
```
api {
    web_server: https://app.clear.ml
    api_server: https://api.clear.ml
    files_server: https://files.clear.ml
    credentials {
        "access_key" = "YOUR_ACCESS_KEY"
        "secret_key" = "YOUR_SECRET_KEY"
    }
}
```

### 4. Verify ClearML Connection

```powershell
python -c "from clearml import Task; Task.init(project_name='Test', task_name='Setup'); print('✓ ClearML connected!')"
```

### 5. Update Environment File

Create `.env` file:
```powershell
Copy-Item .env.example .env
notepad .env
```

Update ClearML section:
```env
# ClearML
CLEARML_API_HOST=https://api.clear.ml
CLEARML_WEB_HOST=https://app.clear.ml
CLEARML_FILES_HOST=https://files.clear.ml
CLEARML_API_ACCESS_KEY=your-access-key-here
CLEARML_API_SECRET_KEY=your-secret-key-here
CLEARML_PROJECT_NAME=ImageAnnotation
CLEARML_DATASET_NAME=AnnotatedImages
```

## Label Studio Configuration

### 1. Start Label Studio

```powershell
docker-compose up -d
```

### 2. Wait for Services

```powershell
# Check status
docker-compose ps

# Wait until both services show "Up"
# Usually takes 30-60 seconds
```

### 3. Access Label Studio

Open browser: http://localhost:8090

### 4. Create Account

1. Click **Sign Up**
2. Enter email and password
3. Complete registration

### 5. Generate API Token

1. Click your username (top right)
2. Go to **Account & Settings**
3. Click **Access Token** tab
4. Copy the token

### 6. Update Environment File

Edit `.env`:
```env
# Label Studio
LABEL_STUDIO_URL=http://localhost:8090
LABEL_STUDIO_API_KEY=your-token-here
```

### 7. Create Project (Optional)

The setup script will create a project, or create manually:

1. Click **Create Project**
2. Name: "ImageAnnotation"
3. Select template: **Object Detection with Bounding Boxes**
4. Click **Save**

## Frontend Setup

### 1. Install Node.js

**Windows:**
- Download from https://nodejs.org (LTS version)
- Run installer
- Verify: `node --version`

**Linux:**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**macOS:**
```bash
brew install node@18
```

### 2. Install pnpm

```powershell
npm install -g pnpm
```

### 3. Install Frontend Dependencies

```powershell
cd frontend
pnpm install
```

### 4. Verify Frontend

```powershell
pnpm run dev
```

Open http://localhost:3000 - should show dashboard (may be empty initially)

## Run Setup Script

```powershell
# Back to project root
cd ..

# Run setup using the CLI
uv run .\main.py setup
```

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

✓ Pipeline setup complete!
```

## Verification

### 1. Check All Services

```powershell
# Docker services
docker-compose ps
# Should show label-studio and labelstudio-postgres as "Up"

# Webhook server
curl http://localhost:8000/health
# Should return {"status":"healthy"}

# Frontend
curl http://localhost:3000
# Should return HTML
```

### 2. Test End-to-End

1. **Start webhook server**: `uv run .\main.py webhook`
2. **Start frontend**: `cd frontend && pnpm run dev`
3. **Open Label Studio**: http://localhost:8090
4. **Create annotation**: Annotate one image
5. **Check dashboard**: http://localhost:3000 should show update
6. **Click "Process Batches Now"**
7. **Verify ClearML**: https://app.clear.ml should show dataset

### 3. Verification Checklist

- [ ] Python 3.11+ installed and working
- [ ] Docker Desktop running
- [ ] Label Studio accessible at http://localhost:8090
- [ ] Label Studio API token generated and in `.env`
- [ ] ClearML credentials configured
- [ ] Webhook server starts without errors
- [ ] Frontend runs on http://localhost:3000
- [ ] Test annotation creates dataset in ClearML
- [ ] Dashboard shows real-time updates

## Troubleshooting Installation

### Python Issues

**Error:** `python: command not found`
```powershell
# Add Python to PATH or use full path:
C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe
```

**Error:** `ModuleNotFoundError`
```powershell
# Reinstall dependencies
uv pip install -e . --force-reinstall
```

### Docker Issues

**Error:** `Cannot connect to Docker daemon`
```powershell
# Start Docker Desktop and wait for it to fully load
# Check system tray for Docker icon
```

**Error:** `Port 8090 already in use`
```powershell
# Find what's using the port
netstat -ano | findstr :8090

# Kill the process or change port in docker-compose.yml
```

### ClearML Issues

**Error:** `401 Unauthorized`
```powershell
# Delete old config and reinitialize
Remove-Item ~/.clearml.conf
clearml-init
```

**Error:** `Connection refused`
```powershell
# Check internet connection
# Verify firewall isn't blocking ClearML
ping api.clear.ml
```

### Label Studio Issues

**Error:** `502 Bad Gateway`
```powershell
# Wait 1-2 minutes after docker-compose up
# Check logs
docker-compose logs label-studio
```

**Error:** `Database migration failed`
```powershell
# Reset Label Studio database
docker-compose down -v
docker-compose up -d
```

## Post-Installation

### Recommended Next Steps

1. **Configure Shared Storage** - See [Shared Storage Guide](../deployment/shared-storage.md)
2. **Learn Batch Processing** - See [Batch Guide](../guides/batch-annotations.md)
3. **Explore Dashboard** - See [Dashboard Guide](../guides/dashboard.md)
4. **Read Architecture** - See [Architecture Overview](../architecture/overview.md)

### Optional Enhancements

- Install Redis for distributed queue: See [Performance Guide](../architecture/performance.md)
- Set up ClearML Server locally: See [ClearML Server Guide](../deployment/clearml-server.md)
- Configure production deployment: See [Docker Compose Guide](../deployment/docker-compose.md)

## Uninstallation

### Complete Cleanup

```powershell
# Stop all services
docker-compose down -v

# Remove Python packages
uv pip uninstall ls2clearml-pipline

# Remove project directory
cd ..
Remove-Item -Recurse -Force ls2clearml_pipline

# Remove Docker images (optional)
docker rmi heartexlabs/label-studio:latest
docker rmi postgres:13
```

---

**Estimated Installation Time**: 20-30 minutes  
**Difficulty**: Moderate  
**Next**: [Configuration Guide](configuration.md)
