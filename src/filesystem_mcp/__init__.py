"""
Filesystem MCP - A FastMCP 2.14.3+ compliant server for file system operations.

This module provides a comprehensive MCP server with file system, Git repository,
and Docker container management capabilities using the portmanteau pattern for
consolidated tool interfaces with enhanced conversational responses and sampling.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Configure structured logging for MCP compliance
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


@asynccontextmanager
async def server_lifespan(mcp_instance: FastMCP):
    """Server lifespan for startup and cleanup."""
    logger.info("Filesystem MCP server starting up", version="2.2.0")
    yield
    logger.info("Filesystem MCP server shutting down")


# Create the main application instance
app = FastMCP(
    name="filesystem-mcp",
    instructions="""You are a comprehensive MCP server for advanced file system, Git repository, and Docker container operations using FastMCP 2.14.3+ with conversational tool returns and sampling capabilities.

CORE CAPABILITIES:
- File system operations: read, write, edit, move, search, analyze files and directories
- Git repository management: clone, commit, branch, merge, diff, history tracking
- Docker container orchestration: lifecycle, images, networks, volumes, compose
- System monitoring: resources, processes, performance metrics
- Agentic workflows: SEP-1577 compliant autonomous file operations with and without sampling

AVAILABLE PORTMANTEAU TOOLS:
\u2022 file_ops: Basic File IO and Metadata (read, write, move, exists, info)
\u2022 dir_ops: Directory structure and management (list, mkdir, tree, size)
\u2022 search_ops: Content analysis, grep, and comparison (grep, search, logs, diff)
\u2022 container_ops: Docker container lifecycle (list, start, stop, exec, logs)
\u2022 infra_ops: Docker images, networks, and volumes
\u2022 orch_ops: Docker Compose operations (up, down, ps, config)
\u2022 repo_ops: Git core repository operations (status, commit, history, diff, etc.)
\u2022 git_ops: Git administrative operations (branches, tags, remotes, stash, rebase, etc.)
\u2022 monitor_ops: Real-time system metrics, resources, and processes
\u2022 host_ops: Host system information, environment, help, and user details
\u2022 agentic_file_workflow: LLM-orchestrated workflows (requires client sampling support: VS Code, Cline)
\u2022 agentic_file_workflow_nosampling: Pure Python workflows, works in ALL clients

Each portmanteau tool consolidates multiple related operations into a single interface,
reducing tool complexity while maintaining full functionality.""",
    lifespan=server_lifespan,
    version="2.2.0",
)


# Import and register all tool modules after app creation
# This ensures all tools are available when the server starts
def _import_tools():
    """Import all portmanteau tool modules to register them with the app."""
    try:
        # Import the portmanteau tool modules - they will register with the global app object
        import importlib

        tool_modules = [
            ".tools.portmanteau_file",           # Basic File IO
            ".tools.portmanteau_directory",      # Directory structure
            ".tools.portmanteau_search",         # Search and comparison
            ".tools.portmanteau_container",      # Container lifecycle
            ".tools.portmanteau_infrastructure", # Images, nets, volumes
            ".tools.portmanteau_orchestration",  # Docker Compose
            ".tools.portmanteau_repository",     # Git core
            ".tools.portmanteau_git_mgmt",       # Git management
            ".tools.portmanteau_monitoring",     # System monitoring
            ".tools.portmanteau_host",           # Host context
            ".tools.agentic_file_workflow",             # Sampling-based, no-tools pattern (Claude Desktop compatible)
        ]

        for module_name in tool_modules:
            try:
                importlib.import_module(module_name, package=__name__)
                logger.debug(
                    f"Portmanteau tool module {module_name} imported successfully"
                )
            except ImportError as e:
                # Log warning but don't fail - some modules may have optional dependencies
                logger.warning(
                    f"Failed to import portmanteau tool module {module_name}: {e}. Some tools may not be available."
                )
            except Exception as e:
                logger.error(
                    f"Failed to import portmanteau tool module {module_name}: {e}"
                )
                # Only raise for non-import errors
                raise

        logger.info("All portmanteau tool modules imported successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to import portmanteau tool modules: {e}")
        return False


# Import tools immediately
_tools_imported = _import_tools()


# Export ASGI app for HTTP/HTTPS mode (for web apps)
def http_app():
    """Get ASGI application for HTTP/HTTPS mode.

    Usage:
        from filesystem_mcp import http_app
        import uvicorn
        uvicorn.run(http_app(), host="127.0.0.1", port=8000)
    """
    return app.http_app()


def main():
    """Main entry point for the MCP server with unified transport handling."""
    from .transport import run_server

    logger.info("Starting Filesystem MCP server v2.2.0 (FastMCP 2.14.4+)")
    logger.info("Python path", python_path=sys.executable)
    logger.info("Working directory", cwd=str(Path.cwd()))

    # Note: Some tools may not be available if optional dependencies are missing
    logger.info(
        "Note: Some tools may not be available if optional dependencies are missing"
    )

    # Use unified transport runner
    run_server(app, server_name="filesystem-mcp")


def run():
    """Entry point function for console script (Unified Transport)."""
    main()


if __name__ == "__main__":
    main()
