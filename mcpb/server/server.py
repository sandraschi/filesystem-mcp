"""MCP server entry point for Filesystem MCP."""

import sys
from pathlib import Path

parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from server import main
except ImportError:
    from filesystem_mcp.server import main

if __name__ == "__main__":
    main()
