"""
Filesystem MCP - A FastMCP 2.10 compliant server for file system and repository operations.

This module provides tools for file system operations and Git repository management,
designed to enable agentic AI programming capabilities.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from mcp import Application

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the FastMCP application
app = Application("filesystem-mcp")

# Import all tools to register them with the app
from .tools.file_operations import *  # noqa
from .tools.repo_operations import *  # noqa

# Add a health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}

def run(host: str = "0.0.0.0", port: int = 8000):
    """
    Run the Filesystem MCP server.
    
    Args:
        host: Host to bind to (default: 0.0.0.0).
        port: Port to listen on (default: 8000).
    """
    import uvicorn
    
    logger.info(f"Starting Filesystem MCP server on {host}:{port}")
    logger.info(f"Available tools: {', '.join(app.list_tools().keys())}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    run()
