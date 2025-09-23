param(
    [switch]$NoSign,
    [switch]$NoValidate,
    [string]$OutputDir = "dist",
    [string]$Version = "",
    [switch]$Help
)

# Filesystem MCP - DXT Build Script
# FastMCP 2.12.0+ compatible

if ($Help) {
    Write-Host "Filesystem MCP - DXT Build Script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\scripts\build-dxt.ps1 [options]"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -NoSign        Skip package signing (for development)"
    Write-Host "  -NoValidate    Skip manifest validation"
    Write-Host "  -OutputDir     Output directory (default: dist)"
    Write-Host "  -Version       Override version from manifest"
    Write-Host "  -Help          Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\scripts\build-dxt.ps1                    # Build with signing"
    Write-Host "  .\scripts\build-dxt.ps1 -NoSign            # Build without signing"
    Write-Host "  .\scripts\build-dxt.ps1 -OutputDir build   # Custom output directory"
    exit 0
}

# Configuration
$ScriptDir = Split-Path -Parent $PSCommandPath
$RootDir = Split-Path -Parent $ScriptDir
$DxtDir = Join-Path $RootDir "dxt"
$ManifestPath = Join-Path $DxtDir "manifest.json"
$OutputDir = Join-Path $RootDir $OutputDir

Write-Host "🔧 Filesystem MCP - DXT Build Script" -ForegroundColor Green
Write-Host "📁 Working directory: $RootDir" -ForegroundColor Cyan
Write-Host "📦 Output directory: $OutputDir" -ForegroundColor Cyan

# Check prerequisites
Write-Host "" -ForegroundColor Yellow
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Node.js not found"
    }
    Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check DXT CLI
try {
    $dxtVersion = dxt --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing DXT CLI..." -ForegroundColor Yellow
        npm install -g @anthropic-ai/dxt
        $dxtVersion = dxt --version
    }
    Write-Host "✅ DXT CLI: $dxtVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ DXT CLI not available. Installing..." -ForegroundColor Yellow
    try {
        npm install -g @anthropic-ai/dxt
        $dxtVersion = dxt --version
        Write-Host "✅ DXT CLI: $dxtVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install DXT CLI. Please install manually: npm install -g @anthropic-ai/dxt" -ForegroundColor Red
        exit 1
    }
}

# Validate manifest
if (-not $NoValidate) {
    Write-Host "" -ForegroundColor Yellow
    Write-Host "🔍 Validating DXT manifest..." -ForegroundColor Yellow

    if (-not (Test-Path $ManifestPath)) {
        Write-Host "❌ Manifest file not found: $ManifestPath" -ForegroundColor Red
        exit 1
    }

    try {
        Push-Location $DxtDir
        dxt validate manifest.json
        if ($LASTEXITCODE -ne 0) {
            throw "Manifest validation failed"
        }
        Write-Host "✅ Manifest validation passed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Manifest validation failed: $_" -ForegroundColor Red
        exit 1
    } finally {
        Pop-Location
    }
}

# Install dependencies
Write-Host "" -ForegroundColor Yellow
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow

try {
    python -m pip install --upgrade pip
    if (Test-Path "requirements.txt") {
        pip install -r requirements.txt
    } else {
        pip install "fastmcp>=2.12.0,<3.0.0" pydantic gitpython
    }
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install dependencies: $_" -ForegroundColor Red
    exit 1
}

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
    Write-Host "📁 Created output directory: $OutputDir" -ForegroundColor Cyan
}

# Build Python package
Write-Host "" -ForegroundColor Yellow
Write-Host "🔨 Building Python package..." -ForegroundColor Yellow

try {
    python -m build
    Write-Host "✅ Python package built" -ForegroundColor Green
} catch {
    Write-Host "❌ Python package build failed: $_" -ForegroundColor Red
    exit 1
}

# Build DXT package
Write-Host "" -ForegroundColor Yellow
Write-Host "📦 Building DXT package..." -ForegroundColor Yellow

try {
    Push-Location $DxtDir
    $packageName = "filesystem-mcp.dxt"
    $packagePath = Join-Path $OutputDir $packageName

    dxt pack . $packagePath
    if ($LASTEXITCODE -ne 0) {
        throw "DXT pack failed"
    }
    Write-Host "✅ DXT package built: $packagePath" -ForegroundColor Green
} catch {
    Write-Host "❌ DXT package build failed: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

# Sign package (if not disabled)
if (-not $NoSign) {
    Write-Host "" -ForegroundColor Yellow
    Write-Host "🔐 Signing DXT package..." -ForegroundColor Yellow

    try {
        $packagePath = Join-Path $OutputDir "filesystem-mcp.dxt"

        # Check if signing key exists
        $keyPath = Join-Path $RootDir "signing.key"
        if (Test-Path $keyPath) {
            dxt sign --key $keyPath $packagePath
            if ($LASTEXITCODE -ne 0) {
                throw "Package signing failed"
            }
            Write-Host "✅ Package signed successfully" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Signing key not found, skipping package signing" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Package signing failed: $_" -ForegroundColor Red
        Write-Host "   Continuing without signing..." -ForegroundColor Yellow
    }
}

# Verify package
Write-Host "" -ForegroundColor Yellow
Write-Host "✅ Verifying DXT package..." -ForegroundColor Yellow

try {
    $packagePath = Join-Path $OutputDir "filesystem-mcp.dxt"

    if (Test-Path $packagePath) {
        # Basic file verification
        $packageSize = (Get-Item $packagePath).Length
        Write-Host "✅ Package size: $([math]::Round($packageSize/1KB, 2)) KB" -ForegroundColor Green

        # DXT verification if key is available
        $keyPath = Join-Path $RootDir "signing.key"
        if (Test-Path $keyPath) {
            dxt verify $packagePath
            if ($LASTEXITCODE -ne 0) {
                throw "Package verification failed"
            }
            Write-Host "✅ Package verification passed" -ForegroundColor Green
        }
    } else {
        throw "Package file not found"
    }
} catch {
    Write-Host "❌ Package verification failed: $_" -ForegroundColor Red
    exit 1
}

# Display results
Write-Host "" -ForegroundColor Green
Write-Host "🎉 DXT Build Complete!" -ForegroundColor Green
Write-Host "" -ForegroundColor Cyan
Write-Host "📦 Output files:" -ForegroundColor Cyan
Get-ChildItem $OutputDir -Name | ForEach-Object {
    Write-Host "  - $_" -ForegroundColor White
}

Write-Host "" -ForegroundColor Cyan
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Test the package: Drag filesystem-mcp.dxt to Claude Desktop" -ForegroundColor White
Write-Host "2. Configure your working directory when prompted" -ForegroundColor White
Write-Host "3. Test the tools in Claude Desktop" -ForegroundColor White
Write-Host "4. Check logs in: %APPDATA%\Claude\logs\" -ForegroundColor White

Write-Host "" -ForegroundColor Green
Write-Host "✅ Build completed successfully!" -ForegroundColor Green
