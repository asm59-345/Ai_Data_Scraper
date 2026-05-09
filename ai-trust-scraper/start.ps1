# ============================================================
#  start.ps1
#  Run the AI Trust Scraper — backend + frontend together.
#
#  Usage (from ai-trust-scraper\ folder):
#    .\start.ps1
# ============================================================

$ROOT     = $PSScriptRoot
$FRONTEND = Join-Path $ROOT "frontend"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   AI Trust Scraper — Full Stack Startup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Check Python ──────────────────────────────────────
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "[ERROR] Python not found. Install Python 3.10+ and try again." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Python found: $($python.Source)" -ForegroundColor Green

# ── Step 2: Check uvicorn ─────────────────────────────────────
$uvicorn = python -c "import uvicorn; print('ok')" 2>$null
if ($uvicorn -ne "ok") {
    Write-Host "[INFO] Installing Python dependencies..." -ForegroundColor Yellow
    python -m pip install -r "$ROOT\requirements.txt" --quiet
}
Write-Host "[OK] uvicorn/fastapi ready" -ForegroundColor Green

# ── Step 3: Check Node.js ─────────────────────────────────────
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Host "[ERROR] Node.js not found. Install Node.js 18+ and try again." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Node.js found: $(node --version)" -ForegroundColor Green

# ── Step 4: Install frontend deps if needed ───────────────────
if (-not (Test-Path "$FRONTEND\node_modules")) {
    Write-Host "[INFO] Installing frontend dependencies (npm install)..." -ForegroundColor Yellow
    Push-Location $FRONTEND
    npm install --silent
    Pop-Location
}
Write-Host "[OK] Frontend node_modules ready" -ForegroundColor Green

Write-Host ""
Write-Host "Starting services..." -ForegroundColor White
Write-Host ""

# ── Step 5: Launch FastAPI backend in a new terminal window ───
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Write-Host '=== FastAPI Backend (port 8000) ===' -ForegroundColor Cyan; " +
    "cd '$ROOT'; " +
    "python -m uvicorn backend.api:app --reload --port 8000"
) -WindowStyle Normal

Start-Sleep -Seconds 3

# ── Step 6: Launch Vite frontend in a new terminal window ─────
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Write-Host '=== React Frontend (port 5173) ===' -ForegroundColor Cyan; " +
    "cd '$FRONTEND'; " +
    "npm run dev"
) -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Both services are starting!" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend  API  -> http://localhost:8000"       -ForegroundColor Yellow
Write-Host "  API Docs      -> http://localhost:8000/docs"  -ForegroundColor Yellow
Write-Host "  Frontend App  -> http://localhost:5173"       -ForegroundColor Yellow
Write-Host ""
Write-Host "  Data loaded from: output\scraped_data.json (981 items)"  -ForegroundColor Gray
Write-Host "  Use 'Run Pipeline' button to scrape fresh data."          -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Close the two new terminal windows to stop the services." -ForegroundColor Gray
