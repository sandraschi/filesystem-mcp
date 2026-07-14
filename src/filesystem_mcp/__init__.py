"""
Filesystem MCP - A FastMCP 3.2+ compliant server for file system operations with concurrency safety.

This module provides a comprehensive MCP server with file system, Git repository,
and Docker container management capabilities using the portmanteau pattern for
consolidated tool interfaces with enhanced conversational responses and sampling.

CRITICAL: All file operations now use atomic patterns and proper locking to prevent
corruption when multiple clients access the same files simultaneously via FastMCP 3.2+ universal connect pattern.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import structlog

# Configure structlog for JSON output with proper MCP stderr handling
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Setup file handler for persistent logs
# Use the repository's logs directory instead of CWD to avoid PermissionErrors in Claude Desktop
try:
    # Resolve path to repo root: src/filesystem_mcp/__init__.py -> src/filesystem_mcp -> src -> repo_root
    repo_root = Path(__file__).resolve().parent.parent.parent
    log_dir = repo_root / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "filesystem_mcp.log"
except Exception:
    # Fallback to home directory if repo path resolution fails
    log_dir = Path.home() / ".filesystem-mcp"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "filesystem_mcp.log"

file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter("%(message)s"))

# Setup stderr handler for MCP server logs (stdout is reserved for MCP protocol)
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setFormatter(logging.Formatter("%(message)s"))

# Configure root logger - file and stderr output
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(stderr_handler)

logger = structlog.get_logger(__name__)

# Import FastMCP 2.14.3+ compliant server
from fastmcp import FastMCP  # noqa: E402
from fastmcp.server import create_proxy  # noqa: E402


@asynccontextmanager
async def server_lifespan(mcp_instance: FastMCP):
    """Server lifespan for startup and cleanup."""
    logger.info("Filesystem MCP server starting up", version="2.2.0")
    logger.info("FastMCP 3.2+ with concurrency safety enabled")
    yield
    logger.info("Filesystem MCP server shutting down")


# Create the main application instance
app = FastMCP(
    name="filesystem-mcp",
    instructions="""You are an MCP server for file system and Docker operations with FastMCP 3.2+ concurrency safety.

CORE CAPABILITIES:
- File system operations: read, write, edit, move, search, analyze files and directories
- Git repository management: clone, commit, branch, merge, diff, history tracking
- Docker container orchestration: lifecycle, images, networks, volumes, compose
- System monitoring: resources, processes, performance metrics
- Agentic workflows: SEP-1577 compliant autonomous file operations with and without sampling

CONCURRENCY SAFETY:
- All file write operations use atomic patterns to prevent corruption
- Proper locking mechanisms prevent race conditions
- FastMCP 3.2+ universal connect pattern support (stdio + HTTP)
- Thread-safe operations for 5+ simultaneous clients

AVAILABLE TOOLS:
\u2022 file_ops, dir_ops, search_ops — file and directory I/O
\u2022 container_ops, infra_ops — Docker containers, images, networks, volumes
\u2022 compose_up, compose_down, compose_ps, compose_logs, compose_config, compose_restart — Docker Compose
\u2022 monitor_get_* — system metrics and processes (e.g. monitor_get_resource_usage)
\u2022 host_ops — host info, environment, help
\u2022 agentic_file_workflow — LLM sampling workflow (requires client ctx.sample)

Portmanteau tools (file_ops, dir_ops) use an operation enum; Compose and monitoring are atomic per operation.""",
    lifespan=server_lifespan,
    version="2.2.0",
)

_bridge_proxies = []
bridge_urls = os.getenv("MCP_BRIDGE_URLS", "")
if bridge_urls:
    for url in bridge_urls.split(","):
        url = url.strip()
        if url:
            try:
                app.add_provider(create_proxy(url))
                _bridge_proxies.append(url)
            except Exception as exc:
                logger.warning("Failed to register bridge proxy", url=url, error=str(exc))


# Import and register all tool modules after app creation
# This ensures all tools are available when the server starts
def _import_tools():
    """Import all portmanteau tool modules to register them with the app."""
    try:
        # Import the portmanteau tool modules - they will register with the global app object
        import importlib

        tool_modules = [
            ".tools.portmanteau_file_safe",  # Concurrency-safe file utilities
            ".tools.portmanteau_file",  # File IO portmanteau
            ".tools.portmanteau_directory",  # Directory structure
            ".tools.portmanteau_search",  # Search and comparison
            ".tools.portmanteau_container",  # Container lifecycle
            ".tools.portmanteau_infrastructure",  # Images, nets, volumes
            ".tools.portmanteau_orchestration",  # Docker Compose
            ".tools.portmanteau_monitoring",  # System monitoring
            ".tools.portmanteau_host",  # Host context
            ".tools.agentic_file_workflow",  # Sampling-based autonomous workflow
        ]

        for module_name in tool_modules:
            try:
                importlib.import_module(module_name, package=__name__)
                logger.debug(f"Portmanteau tool module {module_name} imported successfully")
            except ImportError as e:
                # Log warning but don't fail - some modules may have optional dependencies
                logger.warning(
                    f"Failed to import portmanteau tool module {module_name}: {e}. Some tools may not be available."
                )
            except Exception as e:
                logger.error(f"Failed to import portmanteau tool module {module_name}: {e}")
                # Only raise for non-import errors
                raise

        logger.info("All portmanteau tool modules imported successfully")
        return True

    except Exception as e:
        logger.exception("Failed to import portmanteau tool modules: %s", e)
        raise


# Import tools immediately — raises on failure, server must not start without tools
_import_tools()


# Export ASGI app for HTTP/HTTPS mode (for web apps)
def http_app():
    """Get ASGI application for HTTP/HTTPS mode.

    Usage:
        from filesystem_mcp import http_app
        import uvicorn
        uvicorn.run(http_app(), host="127.0.0.1", port=10742)
    """
    import os
    import time

    from starlette.responses import JSONResponse
    from starlette.routing import Route

    _start = time.time()

    async def diagnostics(request):
        try:
            import psutil

            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
        except ImportError:
            cpu = mem = disk = 0
        return JSONResponse(
            {
                "success": True,
                "backend": {"port": 10742, "status": "running", "uptime": time.time() - _start},
                "system": {"cpu_percent": cpu, "memory_percent": mem, "disk_percent": disk},
                "tools": {"total": 0},
                "cua_status": {"tesseract_available": False, "window_found": False},
            }
        )

    asgi = app.http_app()
    asgi.routes.append(Route("/api/v1/diagnostics", endpoint=diagnostics))
    return asgi


def main():
    """Main entry point for the MCP server with unified transport handling."""
    from .transport import run_server

    _kill_orphaned_stdio()

    logger.info("Starting Filesystem MCP server v2.2.0 (FastMCP 3.2+)")
    logger.info("Python path", python_path=sys.executable)
    logger.info("Working directory", cwd=str(Path.cwd()))
    logger.info("Concurrency safety: Enabled for all file operations")

    # Note: Some tools may not be available if optional dependencies are missing
    logger.info("Note: Some tools may not be available if optional dependencies are missing")

    # Use unified transport runner
    run_server(app, server_name="filesystem-mcp")


def _kill_orphaned_stdio():
    """Kill stale filesystem_mcp stdio processes left by previous CD sessions.

    Skips the HTTP daemon (identified by holding port 10742) so the infrastructure
    service is never touched. Only cleans up orphaned IDE-spawned stdio instances.
    """
    import subprocess

    try:
        # Find PID holding port 10742 (the HTTP daemon — never kill this)
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=10)
        daemon_pid = None
        for line in result.stdout.splitlines():
            if ":10742" in line and "LISTENING" in line:
                parts = line.split()
                if parts:
                    daemon_pid = int(parts[-1])
                    break

        # Find all filesystem_mcp Python processes
        procs = subprocess.run(
            [
                "wmic",
                "process",
                "where",
                "name='python.exe' or name='python3.exe'",
                "get",
                "ProcessId,CommandLine",
                "/format:csv",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        my_pid = os.getpid()
        killed = 0
        for line in procs.stdout.splitlines():
            if "filesystem_mcp" not in line:
                continue
            parts = line.rsplit(",", 1)
            if len(parts) < 2:
                continue
            try:
                pid = int(parts[-1].strip())
            except ValueError:
                continue
            if pid == my_pid or pid == daemon_pid:
                continue
            # Kill the orphan
            try:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=5)
                killed += 1
            except Exception:
                logger.warning("Failed to kill orphan PID %d", pid, exc_info=True)

        if killed:
            logger.info("Cleaned up %d orphaned stdio process(es)", killed)
    except Exception:
        logger.warning("Orphan cleanup failed (non-fatal)", exc_info=True)


def run():
    """Entry point function for console script (Unified Transport)."""
    main()


if __name__ == "__main__":
    main()
