param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser
)

$WebPort = 10743
$BackendPort = 10742
$ProjectRoot = Split-Path -Parent $PSScriptRoot

$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath
$FleetStart = Initialize-FleetStartMode @PSBoundParameters
Enter-FleetHeadlessConsole -Headless:$Headless -BackendOnly:$BackendOnly
Stop-FleetPortSquatters -Ports @($WebPort, $BackendPort) -Label "filesystem-mcp"

if (-not (Assert-FleetPortsAvailable -Ports @($WebPort, $BackendPort) -Label "filesystem-mcp")) { exit 1 }

# 2. Setup
Set-Location $PSScriptRoot
if (-not (Test-Path "node_modules")) { npm install }

# 3. Start the Python backend (Background)
Write-Host "Starting Python backend on port $BackendPort ..." -ForegroundColor Cyan

# Run uvicorn from backend/bridge (no backend package __init__); PYTHONPATH includes repo src
$srcPath = Join-Path $ProjectRoot "src"
$bridgeDir = Join-Path $PSScriptRoot "backend\bridge"
$backendCmd = "`$env:PYTHONPATH = '$srcPath'; Set-Location '$ProjectRoot'; uv run --project '$ProjectRoot' uvicorn main:app --app-dir '$bridgeDir' --host 127.0.0.1 --port $BackendPort --log-level info"

$BackendProc = Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $backendCmd -PassThru
Start-Sleep -Seconds 2

$healthUrl = "http://127.0.0.1:$BackendPort/health"
$maxAttempts = 30
$attempt = 0
$backendUp = $false
while ($attempt -lt $maxAttempts) {
    try {
        $null = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        $backendUp = $true
        break
    } catch {
        Start-Sleep -Seconds 2
        $attempt++
    }
}
if ($backendUp) {
    Write-Host "Backend (port $BackendPort) answered GET /health." -ForegroundColor Green
} else {
    Write-Host "Backend (port $BackendPort) did not return HTTP 200 from /health; check the backend window." -ForegroundColor Yellow
}

# 4. Run server (Vite dev)
if (-not $FleetStart.RunFrontend) { return }

Write-Host "Starting Vite frontend on port $WebPort ..." -ForegroundColor Green

# 4b. Launch background task to open browser once frontend is ready (Auto-opened by Antigravity)
$frontendUrl = "http://127.0.0.1:$WebPort/"
$pollAndOpen = "for (`$i = 0; `$i -lt 60; `$i++) { try { `$null = Invoke-WebRequest -Uri '$frontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Start-Process '$frontendUrl'; exit } catch { Start-Sleep -Seconds 1 } }"
Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen

Write-Host "Browser will open automatically when Vite is ready." -ForegroundColor Gray
if (-not $FleetStart.RunFrontend) { return }
npm run dev -- --port $WebPort --host







