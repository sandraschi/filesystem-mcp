"""
Filesystem MCP - A FastMCP 2.12 compliant server for file system operations.

This module provides a comprehensive MCP server with file system, Git repository,
and Docker container management capabilities.
"""

import logging
import sys
from pathlib import Path

# Configure comprehensive logging for FastMCP 2.12
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),  # For Claude Desktop visibility
        logging.FileHandler('filesystem_mcp.log')  # Persistent log file
    ]
)
logger = logging.getLogger(__name__)

# Import FastMCP 2.12 compliant server
from fastmcp import FastMCP

# Create the main application instance
app = FastMCP(
    name="filesystem-mcp",
    instructions="""A comprehensive MCP server for file system, Git repository, and Docker container operations.

Available Operations:
• File Operations: read, write, list, check existence, get metadata
• Git Operations: clone, status, branches, commit, read repository
• Docker Operations: list containers, manage images, networks, volumes

Use the tools below to perform various file system and development operations.""",
    version="2.0.0"
)

# Import and register all tool modules after app creation
# This ensures all tools are available when the server starts
def _import_tools():
    """Import all tool modules to register them with the app."""
    try:
        # Import the tool modules - they will register with the global app object
        import sys
        import importlib

        tool_modules = [
            '.tools.file_operations',
            # '.tools.repo_operations',  # TODO: Check for syntax errors
            '.tools.docker_operations',
            # '.tools.system_tools'  # TODO: Check for syntax errors
        ]

        for module_name in tool_modules:
            try:
                importlib.import_module(module_name, package=__name__)
                logger.debug(f"Tool module {module_name} imported successfully")
            except Exception as e:
                logger.error(f"Failed to import tool module {module_name}: {e}")
                raise

        logger.info("All tool modules imported successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to import tool modules: {e}")
        return False

# Import tools immediately
_tools_imported = _import_tools()

def main():
    """Main entry point for the MCP server."""
    try:
        logger.info("Starting Filesystem MCP server v2.0.0")
        logger.info(f"Python path: {sys.executable}")
        logger.info(f"Working directory: {Path.cwd()}")

        # Check if tools were imported successfully
        if not _tools_imported:
            logger.error("Tool modules were not imported successfully")
            raise RuntimeError("Failed to import tool modules")

        # Validate that tools are registered
        tools = app.get_tools()
        logger.info(f"Registered tools: {list(tools.keys())}")

        if not tools:
            logger.warning("No tools were registered - this may indicate an issue")

        # Run the server
        app.run()

    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
