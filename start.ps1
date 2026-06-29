# HuanYou Windows PowerShell Startup Script
# Usage: .\start.ps1 [setup|backend|frontend|all|db]
param([string]$Command = "all", [int]$Port = 8000)

$projectRoot = $PSScriptRoot

function Start-Backend {
    Write-Host "Starting FastAPI backend..." -ForegroundColor Green
    Set-Location "$projectRoot\backend"
    $env:PYTHONPATH = "$projectRoot\backend"
    Write-Host "  API Docs: http://localhost:$Port/docs" -ForegroundColor Cyan
    Write-Host "  Health:   http://localhost:$Port/api/health" -ForegroundColor Cyan
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $Port
}

function Start-Frontend {
    Write-Host "Starting Vue 3 frontend..." -ForegroundColor Green
    Set-Location "$projectRoot\frontend"
    if (-not (Test-Path "node_modules")) {
        Write-Host "  First run: installing npm packages..." -ForegroundColor Yellow
        npm install
    }
    Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Cyan
    npm run dev
}

function Invoke-Setup {
    Write-Host "========================================" -ForegroundColor Magenta
    Write-Host "  HuanYou - Project Setup" -ForegroundColor Magenta
    Write-Host "========================================" -ForegroundColor Magenta

    # Check .env
    if (-not (Test-Path "$projectRoot\.env")) {
        Copy-Item "$projectRoot\.env.example" "$projectRoot\.env"
        Write-Host "[1/4] Created .env - please edit to set DEEPSEEK_API_KEY" -ForegroundColor Yellow
    } else {
        Write-Host "[1/4] .env exists" -ForegroundColor Green
    }

    # Install Python deps
    Write-Host "[2/4] Installing Python dependencies..." -ForegroundColor Yellow
    Set-Location $projectRoot
    pip install aiosqlite sqlalchemy fastapi uvicorn python-jose python-multipart python-dotenv pydantic-settings bcrypt sse-starlette 2>&1 | Select-Object -Last 3

    # Create directories
    Write-Host "[3/4] Creating data directories..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path "$projectRoot\data\uploads" | Out-Null

    # Initialize database
    Write-Host "[4/4] Initializing database with seed data..." -ForegroundColor Yellow
    Set-Location "$projectRoot\backend"
    $env:PYTHONPATH = "$projectRoot\backend"
    python -m scripts.seed_data 2>&1 | Select-Object -Last 6

    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Start backend:  .\start.ps1 backend" -ForegroundColor Cyan
    Write-Host "  Start frontend: .\start.ps1 frontend" -ForegroundColor Cyan
    Write-Host "  Edit .env to set DEEPSEEK_API_KEY for AI features" -ForegroundColor Yellow
    Write-Host "  Test accounts: 13800000001/admin123 (shop)  13800000002/user123 (user)" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Green
}

function Invoke-DB {
    Write-Host "Database operations:" -ForegroundColor Green
    Write-Host "  1. Rebuild & seed (fresh start)" -ForegroundColor Cyan
    Write-Host "  2. Alembic migrate (needs PostgreSQL)" -ForegroundColor Cyan
    $choice = Read-Host "Select [1/2]"
    Set-Location "$projectRoot\backend"
    $env:PYTHONPATH = "$projectRoot\backend"
    if ($choice -eq "1") {
        Remove-Item "$projectRoot\backend\huanyou.db" -Force -ErrorAction SilentlyContinue
        python -m scripts.seed_data
    } elseif ($choice -eq "2") {
        alembic upgrade head
    }
}

function Start-All {
    Write-Host "Starting all services..." -ForegroundColor Green
    Write-Host "  Open two terminals and run:" -ForegroundColor Yellow
    Write-Host "    Terminal 1: .\start.ps1 backend" -ForegroundColor Cyan
    Write-Host "    Terminal 2: .\start.ps1 frontend" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Or start backend now + frontend after:" -ForegroundColor Yellow
    $choice = Read-Host "Start backend now? [y/n]"
    if ($choice -eq "y") {
        Start-Backend
    }
}

switch ($Command) {
    "backend"   { Start-Backend }
    "frontend"  { Start-Frontend }
    "setup"     { Invoke-Setup }
    "db"        { Invoke-DB }
    "all"       { Start-All }
    default {
        Write-Host "HuanYou Startup Script" -ForegroundColor Magenta
        Write-Host ""
        Write-Host "Usage: .\start.ps1 [command]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  setup    - Install deps + init database (first run)" -ForegroundColor Cyan
        Write-Host "  backend  - Start FastAPI server (port $Port)" -ForegroundColor Cyan
        Write-Host "  frontend - Start Vue dev server" -ForegroundColor Cyan
        Write-Host "  all      - Start everything" -ForegroundColor Cyan
        Write-Host "  db       - Database operations" -ForegroundColor Cyan
    }
}
