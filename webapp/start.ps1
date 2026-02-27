# Filesystem MCP Webapp Start (Plex Pattern)
# Run: powershell -ExecutionPolicy Bypass -File webapp/start.ps1

$ErrorActionPreference = "Stop"
$BackendPort = 10742
$FrontendPort = 10743
$WebappRoot = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $WebappRoot
$SrcPath = Join-Path $ProjectRoot "src"

Write-Host "Starting Filesystem MCP Webapp (Plex Pattern)..." -ForegroundColor Cyan

# 1. Clear ports (kill-port)
Write-Host "Clearing ports $BackendPort, $FrontendPort..." -ForegroundColor Yellow
try {
    # Try to use npx if available, otherwise just continue. 
    # Validating environment: providing full path to npx if needed or assuming in PATH.
    npx --yes kill-port $BackendPort $FrontendPort 2>$null
}
catch { 
    Write-Warning "Could not kill ports. If they are in use, startup may fail."
}
Start-Sleep -Seconds 1

# 2. Env for backend
$env:PYTHONPATH = $SrcPath
$env:PORT = $BackendPort
# Allow both localhost and 127.0.0.1 for CORS to avoid issues
$env:CORS_ORIGINS = "http://localhost:$FrontendPort,http://127.0.0.1:$FrontendPort"

# 3. Start Backend (FastAPI Monolith)
Write-Host "Starting Backend on port $BackendPort..." -ForegroundColor Yellow
$backendDir = Join-Path $WebappRoot "backend"

if (-not (Test-Path $backendDir)) {
    Write-Error "Backend directory not found: $backendDir"
}

# Launch Uvicorn
# We use 'bridge.main:app' to avoid namespace collisions with other 'app' packages
# Also setting CORS_ORIGINS as JSON string just in case
$env:CORS_ORIGINS = '["http://localhost:10743", "http://127.0.0.1:10743"]'
$backendCmd = "Set-Location '$backendDir'; `$env:PYTHONPATH='$SrcPath'; `$env:PORT='$BackendPort'; `$env:CORS_ORIGINS='$env:CORS_ORIGINS'; python -m uvicorn bridge.main:app --reload --host 0.0.0.0 --port $BackendPort"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Write-Host "Backend started." -ForegroundColor Green

# 4. Wait for Backend
Start-Sleep -Seconds 3

# 5. Start Frontend (Vite)
Write-Host "Starting Frontend on port $FrontendPort..." -ForegroundColor Yellow
$frontendDir = $WebappRoot
if (Test-Path "$frontendDir\package.json") {
    $apiUrl = "http://localhost:$BackendPort"
    $frontendCmd = "Set-Location '$frontendDir'; `$env:VITE_API_URL='$apiUrl'; npm run dev -- --port $FrontendPort"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd
    Write-Host "Frontend started." -ForegroundColor Green
}
else {
    Write-Error "package.json not found in $frontendDir"
}

Write-Host "Backend ($BackendPort) and Frontend ($FrontendPort) started." -ForegroundColor Green
Write-Host "Close the opened PowerShell windows to stop the servers." -ForegroundColor Red
