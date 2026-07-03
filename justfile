set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]
import 'scripts/just/fleet.just'

# Open the interactive recipe dashboard in the browser
default:
    @just --list

# ── Quality ───────────────────────────────────────────────────────────────────

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check src/ tests/
    npx @biomejs/biome check . 2>$null || Write-Host "biome: skipped (not configured)"

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check --fix src/ tests/
    uv run ruff format src/ tests/
    npx @biomejs/biome check --write . 2>$null || Write-Host "biome: skipped (not configured)"

# ── Testing ───────────────────────────────────────────────────────────────────

# Run all tests
test:
    Set-Location '{{justfile_directory()}}'
    uv run pytest

e2e:
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "D:\Dev\repos\mcp-central-docs\scripts\playwright-audit.ps1" -RepoPath "{{justfile_directory()}}"

# Quick import check and type checking
check:
    Set-Location '{{justfile_directory()}}'
    uv run python -c "import filesystem_mcp; print('Import OK')"

# ── Installation ──────────────────────────────────────────────────────────────

# Install all dependencies
install:
    Set-Location '{{justfile_directory()}}'
    uv sync

# ── Dev ───────────────────────────────────────────────────────────────────────

# Start the MCP stdio server (for Claude Desktop testing)
mcp:
    Set-Location '{{justfile_directory()}}'
    uv run python -m filesystem_mcp

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

# Run tests with coverage
test-cov:
    Set-Location '{{justfile_directory()}}'
    uv run pytest --cov=filesystem_mcp --cov-report=term --cov-report=html --cov-fail-under=80

# Run mypy type checking
typecheck:
    Set-Location '{{justfile_directory()}}'
    uv run mypy src/

# Build wheel
build:
    Set-Location '{{justfile_directory()}}'
    uv build

# ── Cleanup ───────────────────────────────────────────────────────────────────

# CUA-NSIS smoke test against installed NSIS app
cua-nsis-test:
    uv run python scripts/cua-smoke.py

# Clean build artifacts and caches
clean:
    Set-Location '{{justfile_directory()}}'
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .ruff_cache, .pytest_cache, __pycache__, *.egg-info, dist, build
