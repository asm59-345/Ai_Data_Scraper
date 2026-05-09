$ROOT     = $PSScriptRoot
$FRONTEND = Join-Path $ROOT "frontend"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   AI Trust Scraper — Single Server Production Mode" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Install frontend deps and build ───────────────────
if (-not (Test-Path "$FRONTEND\dist")) {
    Write-Host "[INFO] Building frontend (this only happens once)..." -ForegroundColor Yellow
    Push-Location $FRONTEND
    npm install --silent
    npm run build
    Pop-Location
    Write-Host "[OK] Frontend built to dist/ directory" -ForegroundColor Green
} else {
    Write-Host "[OK] Frontend dist/ already exists" -ForegroundColor Green
}

# ── Step 2: Check Python & Install dependencies ───────────────
$uvicorn = python -c "import uvicorn; print('ok')" 2>$null
if ($uvicorn -ne "ok") {
    Write-Host "[INFO] Installing Python dependencies..." -ForegroundColor Yellow
    python -m pip install -r "$ROOT\requirements.txt" --quiet
}
Write-Host "[OK] Backend dependencies ready" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Starting Single Server (FastAPI + React)..." -ForegroundColor Green
Write-Host ""
Write-Host "  App & Dashboard -> http://localhost:8000" -ForegroundColor Yellow
Write-Host "  API Docs        -> http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# ── Step 3: Launch FastAPI backend ────────────────────────────
cd "$ROOT"
Start-Process "http://localhost:8000"
python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000