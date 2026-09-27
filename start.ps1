# *********************************************************************************
# * SOTA Fleet Orchestration - Standardized Start System (v1.19.0)                *
# * Generated/Repaired by Antigravity on 2026-09-27                  *
# *********************************************************************************

Param([switch]$Headless)

# --- SOTA Headless Standard ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
# --- SOTA PORT SAFETY START ---
# Ports live in fleet-start.config.ps1 (no $Port var in this file).
foreach ($portNum in @(10742, 10743)) {
    Get-NetTCPConnection -LocalPort $portNum -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.OwningProcess -ne $PID) {
            Write-Host "Clearing stale listener on port $portNum (PID $($_.OwningProcess))..." -ForegroundColor Yellow
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
}
Start-Sleep -Seconds 1
# --- SOTA PORT SAFETY END ---
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
$WindowStyle = if ($Headless) { 'Hidden' } else { 'Normal' }
# ------------------------------

$env:FASTMCP_LOG_LEVEL = 'WARNING'
# filesystem-mcp Start - Standards-Compliant SOTA
Write-Host 'Starting filesystem-mcp...' -ForegroundColor Cyan

uv run filesystem-mcp
