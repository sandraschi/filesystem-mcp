"""
Filesystem MCP tools package.

This package contains all the tools for the Filesystem MCP server.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

# Import tool modules
from . import file_operations, repo_operations
from .register_tools import register_tools

# Re-export public functions
__all__ = [
    'file_operations',
    'repo_operations',
    'register_tools'
]

def get_tools() -> List[Dict[str, Any]]:
    """
    Get all available tools in the filesystem MCP.
    
    This is maintained for backward compatibility. New code should use
    the FastMCP 2.10 tool registration system.
    
    Returns:
        List[Dict]: A list of tool definitions.
    """
    # This is now just a compatibility wrapper
    tools = []
    
    # Import tool modules to ensure all tools are registered
    from . import file_operations, repo_operations
    
    # Get all functions from tool modules
    import inspect
    for module in [file_operations, repo_operations]:
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if hasattr(obj, '_mcp_tool'):
                tools.append({
                    'name': obj.__name__,
                    'description': obj.__doc__ or 'No description available',
                    'module': module.__name__
                })
    
    return tools
