  EDITED  D:\Dev\repos\filesystem-mcp\start.ps1 Param([switch]$Headless)

# --- SOTA Headless Standard ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
$WindowStyle = if ($Headless) { 'Hidden' } else { 'Normal' }
# ------------------------------

$env:FASTMCP_LOG_LEVEL = 'WARNING'
# filesystem-mcp Start - Standards-Compliant SOTA
Write-Host 'Starting filesystem-mcp...' -ForegroundColor Cyan

uv run filesystem-mcp