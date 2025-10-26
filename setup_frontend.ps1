# Frontend Setup Script

Write-Host "🎨 Setting up Label Studio to ClearML Pipeline Frontend..." -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
$nodeVersion = node --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Node.js is not installed!" -ForegroundColor Red
    Write-Host "Please install Node.js from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Node.js $nodeVersion detected" -ForegroundColor Green

# Navigate to frontend directory
Set-Location frontend

# Install dependencies
Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Frontend setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Start the webhook server: " -NoNewline
Write-Host "cd .. && uv run webhook_server.py" -ForegroundColor Yellow
Write-Host "  2. Start the frontend: " -NoNewline
Write-Host "cd frontend && npm run dev" -ForegroundColor Yellow
Write-Host "  3. Open http://localhost:3000 in your browser" -ForegroundColor Yellow
Write-Host ""
