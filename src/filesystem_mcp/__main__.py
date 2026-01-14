"""
Filesystem MCP - Main entry point.

This module provides the main entry point for the Filesystem MCP server.
Supports both stdio (for Claude Desktop) and HTTP/HTTPS (for web apps).
"""

import asyncio
import logging
import os
import sys

from . import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("filesystem-mcp")


async def main() -> None:
    """Run the Filesystem MCP server."""
    # Check for HTTP mode via environment variable
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    
    if transport == "http":
        logger.info(f"Starting Filesystem MCP server in HTTP mode on {host}:{port}")
        logger.info(f"MCP endpoint will be available at: http://{host}:{port}/mcp/")
        # Run HTTP server (blocks)
        app.run(transport="http", host=host, port=port)
    else:
        # Default: stdio mode for Claude Desktop
        logger.info("Starting Filesystem MCP server in stdio mode")
        await app.run_stdio_async()


def run() -> None:
    """Run the MCP server in an asyncio event loop."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception:
        logger.exception("Error in MCP server:")
        sys.exit(1)


if __name__ == "__main__":
    run()
