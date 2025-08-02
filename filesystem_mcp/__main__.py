"""
Filesystem MCP - Main entry point.

This module provides the main entry point for the Filesystem MCP server.
"""

import uvicorn
from .app import app, logger

def main() -> None:
    """Run the Filesystem MCP server."""
    logger.info("Starting Filesystem MCP server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,
    )

if __name__ == "__main__":
    main()
