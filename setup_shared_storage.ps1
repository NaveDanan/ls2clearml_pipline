# Setup Shared Storage for Label Studio and ClearML

Write-Host "🔧 Setting up shared storage for Label Studio and ClearML..." -ForegroundColor Cyan

# Create shared-data directory structure
$sharedDataDir = ".\shared-data"
$uploadDir = "$sharedDataDir\upload"

if (-not (Test-Path $sharedDataDir)) {
    Write-Host "📁 Creating shared-data directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $sharedDataDir | Out-Null
    New-Item -ItemType Directory -Path $uploadDir | Out-Null
    Write-Host "✅ Created: $sharedDataDir" -ForegroundColor Green
} else {
    Write-Host "✅ shared-data directory already exists" -ForegroundColor Green
}

# Check if Docker containers are running
Write-Host "`n🐳 Checking Docker containers..." -ForegroundColor Cyan
$containers = docker ps --format "{{.Names}}" 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

$labelStudioRunning = $containers -contains "label-studio"
$postgresRunning = $containers -contains "labelstudio-postgres"

if (-not $labelStudioRunning -or -not $postgresRunning) {
    Write-Host "⚠️  Docker containers not running. Starting them now..." -ForegroundColor Yellow
    docker-compose up -d
    Start-Sleep -Seconds 5
} else {
    Write-Host "✅ Docker containers are running" -ForegroundColor Green
}

# Verify volume mount
Write-Host "`n📦 Verifying volume mount..." -ForegroundColor Cyan
$volumeCheck = docker exec label-studio ls -la /shared-data 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Volume mounted successfully in Label Studio container" -ForegroundColor Green
    Write-Host "   Container path: /shared-data" -ForegroundColor Gray
    Write-Host "   Host path: $((Get-Item $sharedDataDir).FullName)" -ForegroundColor Gray
} else {
    Write-Host "❌ Volume mount verification failed" -ForegroundColor Red
    Write-Host "   Please restart containers: docker-compose down && docker-compose up -d" -ForegroundColor Yellow
}

# Display next steps
Write-Host "`n✨ Setup complete! Next steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Configure Label Studio to use shared storage:" -ForegroundColor White
Write-Host "   - Open http://localhost:8080" -ForegroundColor Gray
Write-Host "   - Go to Settings → Cloud Storage" -ForegroundColor Gray
Write-Host "   - Add Local Files storage with path: /shared-data/upload" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start the webhook server:" -ForegroundColor White
Write-Host "   uv run python webhook_server.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start the dashboard (optional):" -ForegroundColor White
Write-Host "   cd frontend && pnpm dev" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Test by uploading and annotating an image in Label Studio" -ForegroundColor White
Write-Host ""
Write-Host "📚 For detailed instructions, see: SHARED_STORAGE_SETUP.md" -ForegroundColor Cyan
Write-Host ""
