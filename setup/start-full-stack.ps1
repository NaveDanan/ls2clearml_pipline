# ClearML + Label Studio Full Stack Startup Script
# This script starts both ClearML and Label Studio with shared storage

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " ClearML + Label Studio Full Stack" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Create shared data directory if it doesn't exist
Write-Host "`nCreating shared data directory..." -ForegroundColor Yellow
if (!(Test-Path "./shared-data")) {
    New-Item -ItemType Directory -Path "./shared-data" -Force | Out-Null
    New-Item -ItemType Directory -Path "./shared-data/upload" -Force | Out-Null
    Write-Host "✓ Created ./shared-data directory" -ForegroundColor Green
} else {
    Write-Host "✓ Shared data directory exists" -ForegroundColor Green
}

# Stop any existing services
Write-Host "`nStopping existing services..." -ForegroundColor Yellow
docker-compose -f ../docker/docker-compose.full.yml down 2>$null
Write-Host "✓ Stopped existing services" -ForegroundColor Green

# Start services
Write-Host "`nStarting services..." -ForegroundColor Yellow
Write-Host "  This may take 2-3 minutes for first-time setup..." -ForegroundColor Gray
docker-compose -f ../docker/docker-compose.full.yml up -d

# Wait for services to be healthy
Write-Host "`nWaiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service status
Write-Host "`nService Status:" -ForegroundColor Yellow
docker-compose -f ../docker/docker-compose.full.yml ps

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Services Started Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access your services:" -ForegroundColor Yellow
Write-Host "  • Label Studio:  http://localhost:8090" -ForegroundColor White
Write-Host "  • ClearML Web:   http://localhost:8080" -ForegroundColor White
Write-Host "  • ClearML API:   http://localhost:8008" -ForegroundColor White
Write-Host "  • ClearML Files: http://localhost:8081" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Configure Label Studio storage (see documents/CLEARML_SERVER_SETUP.md)" -ForegroundColor White
Write-Host "  2. Generate ClearML credentials" -ForegroundColor White
Write-Host "  3. Update .env file with new URLs" -ForegroundColor White
Write-Host "  4. Start webhook server: python webhook_server_optimized.py" -ForegroundColor White
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Yellow
Write-Host "  docker-compose -f docker/docker-compose.full.yml logs -f" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop services:" -ForegroundColor Yellow
Write-Host "  docker-compose -f docker/docker-compose.full.yml down" -ForegroundColor Gray
Write-Host ""
