"""
Filesystem MCP - Main entry point.

This module provides the main entry point for the Filesystem MCP server.
"""

import asyncio
import logging
import sys
from . import app as server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("filesystem-mcp")

async def main() -> None:
    """Run the Filesystem MCP server."""
    # The server is already configured in __init__.py

    # Run the server
    await server.run_async()

def run() -> None:
    """Run the MCP server in an asyncio event loop."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.exception("Error in MCP server:")
        sys.exit(1)

if __name__ == "__main__":
    run()
