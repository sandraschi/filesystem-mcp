param(
    [switch]$NoSign,
    [switch]$NoValidate,
    [string]$OutputDir = "dist",
    [string]$Version = "",
    [switch]$Help
)

# Filesystem MCP - MCPB Build Script
# FastMCP 2.14.1+ compatible

if ($Help) {
    Write-Host "Filesystem MCP - MCPB Build Script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\scripts\build-mcpb.ps1 [options]"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -NoSign        Skip package signing (for development)"
    Write-Host "  -NoValidate    Skip manifest validation"
    Write-Host "  -OutputDir     Output directory (default: dist)"
    Write-Host "  -Version       Override version from manifest"
    Write-Host "  -Help          Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\scripts\build-mcpb.ps1                    # Build with signing"
    Write-Host "  .\scripts\build-mcpb.ps1 -NoSign            # Build without signing"
    Write-Host "  .\scripts\build-mcpb.ps1 -OutputDir build   # Custom output directory"
    exit 0
}

# Configuration
$ScriptDir = Split-Path -Parent $PSCommandPath
$RootDir = Split-Path -Parent $ScriptDir
$McpbManifestPath = Join-Path $RootDir "mcpb_manifest.json"
$McpbConfigPath = Join-Path $RootDir "mcpb.json"
$OutputDir = Join-Path $RootDir $OutputDir

Write-Host "🔧 Filesystem MCP - MCPB Build Script" -ForegroundColor Green
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

# Check MCPB CLI
try {
    $mcpbVersion = mcpb --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing MCPB CLI..." -ForegroundColor Yellow
        npm install -g @anthropic-ai/mcpb
        $mcpbVersion = mcpb --version
    }
    Write-Host "✅ MCPB CLI: $mcpbVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ MCPB CLI not available. Installing..." -ForegroundColor Yellow
    try {
        npm install -g @anthropic-ai/mcpb
        $mcpbVersion = mcpb --version
        Write-Host "✅ MCPB CLI: $mcpbVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install MCPB CLI. Please install manually: npm install -g @anthropic-ai/mcpb" -ForegroundColor Red
        exit 1
    }
}

# Validate manifest
if (-not $NoValidate) {
    Write-Host "" -ForegroundColor Yellow
    Write-Host "🔍 Validating MCPB manifest..." -ForegroundColor Yellow

    if (-not (Test-Path $McpbManifestPath)) {
        Write-Host "❌ Manifest file not found: $McpbManifestPath" -ForegroundColor Red
        exit 1
    }

    try {
        mcpb validate $McpbManifestPath
        if ($LASTEXITCODE -ne 0) {
            throw "Manifest validation failed"
        }
        Write-Host "✅ Manifest validation passed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Manifest validation failed: $_" -ForegroundColor Red
        exit 1
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
        pip install "fastmcp>=2.14.1,<3.0.0" pydantic gitpython
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

# Build MCPB package
Write-Host "" -ForegroundColor Yellow
Write-Host "📦 Building MCPB package..." -ForegroundColor Yellow

try {
    $packageName = "filesystem-mcp.mcpb"
    $packagePath = Join-Path $OutputDir $packageName

    mcpb pack $RootDir $packagePath
    if ($LASTEXITCODE -ne 0) {
        throw "MCPB pack failed"
    }
    Write-Host "✅ MCPB package built: $packagePath" -ForegroundColor Green
} catch {
    Write-Host "❌ MCPB package build failed: $_" -ForegroundColor Red
    exit 1
}

# Sign package (if not disabled)
if (-not $NoSign) {
    Write-Host "" -ForegroundColor Yellow
    Write-Host "🔐 Signing MCPB package..." -ForegroundColor Yellow

    try {
        $packagePath = Join-Path $OutputDir "filesystem-mcp.mcpb"

        # Check if signing key exists
        $keyPath = Join-Path $RootDir "signing.key"
        if (Test-Path $keyPath) {
            mcpb sign --key $keyPath $packagePath
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
Write-Host "✅ Verifying MCPB package..." -ForegroundColor Yellow

try {
    $packagePath = Join-Path $OutputDir "filesystem-mcp.mcpb"

    if (Test-Path $packagePath) {
        # Basic file verification
        $packageSize = (Get-Item $packagePath).Length
        Write-Host "✅ Package size: $([math]::Round($packageSize/1KB, 2)) KB" -ForegroundColor Green

        # MCPB verification if key is available
        $keyPath = Join-Path $RootDir "signing.key"
        if (Test-Path $keyPath) {
            mcpb verify $packagePath
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
Write-Host "🎉 MCPB Build Complete!" -ForegroundColor Green
Write-Host "" -ForegroundColor Cyan
Write-Host "📦 Output files:" -ForegroundColor Cyan
Get-ChildItem $OutputDir -Name | ForEach-Object {
    Write-Host "  - $_" -ForegroundColor White
}

Write-Host "" -ForegroundColor Cyan
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Test the package: Drag filesystem-mcp.mcpb to Claude Desktop" -ForegroundColor White
Write-Host "2. Configure your working directory when prompted" -ForegroundColor White
Write-Host "3. Test the tools in Claude Desktop" -ForegroundColor White
Write-Host "4. Check logs in: %APPDATA%\Claude\logs\" -ForegroundColor White

Write-Host "" -ForegroundColor Green
Write-Host "✅ Build completed successfully!" -ForegroundColor Green
