"""
Filesystem MCP tools package - FastMCP 2.14.1+ compliant.

This package contains all the tools for the Filesystem MCP server.
All tools are registered using FastMCP's @app.tool() decorator pattern.
"""

import logging

logger = logging.getLogger(__name__)

# Tool modules are imported by the main application after app creation
# This prevents circular import issues and follows FastMCP best practices

logger.info("Tool modules will be imported by the main application")

# These will be populated by the main app during import
__all__ = []
