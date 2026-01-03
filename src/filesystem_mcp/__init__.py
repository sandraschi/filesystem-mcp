"""
Filesystem MCP - A FastMCP 2.14.1+ compliant server for file system operations.

This module provides a comprehensive MCP server with file system, Git repository,
and Docker container management capabilities using the portmanteau pattern for
consolidated tool interfaces.
"""

import logging
import sys
from pathlib import Path

# Configure comprehensive logging for FastMCP 2.12
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),  # For Claude Desktop visibility
        logging.FileHandler("filesystem_mcp.log"),  # Persistent log file
    ],
)
logger = logging.getLogger(__name__)

# Import FastMCP 2.12 compliant server
from fastmcp import FastMCP

# Create the main application instance
app = FastMCP(
    name="filesystem-mcp",
    instructions="""A comprehensive MCP server for file system, Git repository, and Docker container operations using FastMCP 2.14.1+ portmanteau pattern.

Available Portmanteau Tools:
• file_ops: Basic File IO and Metadata (read, write, move, exists, info)
• dir_ops: Directory structure and management (list, mkdir, tree, size)
• search_ops: Content analysis, grep, and comparison (grep, search, logs, diff)
• container_ops: Docker container lifecycle (list, start, stop, exec, logs)
• infra_ops: Docker images, networks, and volumes
• orch_ops: Docker Compose operations (up, down, ps, config)
• repo_ops: Git core repository operations (status, commit, history, diff, etc.)
• git_ops: Git administrative operations (branches, tags, remotes, stash, rebase, etc.)
• monitor_ops: Real-time system metrics, resources, and processes
• host_ops: Host system information, environment, help, and user details

Each portmanteau tool consolidates multiple related operations into a single interface,
reducing tool complexity while maintaining full functionality.""",
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
            ".tools.portmanteau_file",  # Basic File IO
            ".tools.portmanteau_directory",  # Directory structure
            ".tools.portmanteau_search",  # Search and comparison
            ".tools.portmanteau_container",  # Container lifecycle
            ".tools.portmanteau_infrastructure",  # Images, nets, volumes
            ".tools.portmanteau_orchestration",  # Docker Compose
            ".tools.portmanteau_repository",  # Git core
            ".tools.portmanteau_git_mgmt",  # Git management
            ".tools.portmanteau_monitoring",  # System monitoring
            ".tools.portmanteau_host",  # Host context
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
        logger.error(f"Failed to import portmanteau tool modules: {e}")
        return False


# Import tools immediately
_tools_imported = _import_tools()


def main():
    """Main entry point for the MCP server."""
    try:
        logger.info("Starting Filesystem MCP server v2.2.0 (FastMCP 2.14.1+)")
        logger.info(f"Python path: {sys.executable}")
        logger.info(f"Working directory: {Path.cwd()}")

        # Check if tools were imported successfully
        # Note: _tools_imported may be True even if some modules failed (optional deps)
        # We only fail if there's a critical error, not missing optional dependencies

        # Log startup info
        logger.info("Filesystem MCP server ready to start")
        logger.info("Note: Some tools may not be available if optional dependencies are missing")

        # Run the server using stdio (MCP protocol)
        import asyncio

        asyncio.run(app.run_stdio_async())

    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}", exc_info=True)
        raise


def run():
    """Entry point function for console script."""
    import asyncio

    async def run_async():
        """Run the MCP server asynchronously."""
        await app.run_stdio_async()

    try:
        asyncio.run(run_async())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception:
        logger.exception("Error in MCP server:")
        sys.exit(1)


if __name__ == "__main__":
    main()
