"""
Filesystem MCP - Main entry point.

This module provides the main entry point for the Filesystem MCP server.
Supports both stdio (for Claude Desktop) and HTTP/HTTPS (for web apps).
"""

from . import main, run

if __name__ == "__main__":
    main()
