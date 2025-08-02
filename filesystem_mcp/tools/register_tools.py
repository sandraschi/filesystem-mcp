"""
Tool registration for Filesystem MCP.

This module handles the registration of all tools with the FastMCP application.
"""

import importlib
import inspect
import pkgutil
from typing import Type, Any, Dict, List

from mcp import FastMCP

def register_tools(app: FastMPC) -> None:
    """
    Register all tools with the FastMCP application.
    
    Args:
        app: The FastMCP application instance
    """
    # Import all tool modules
    from . import file_operations, repo_operations
    
    # Get all functions from tool modules
    tool_modules = [file_operations, repo_operations]
    
    for module in tool_modules:
        for name, obj in inspect.getmembers(module):
            # Skip private attributes and non-functions
            if name.startswith('_') or not inspect.isfunction(obj):
                continue
                
            # Check if the function is a tool (has _mcp_tool attribute)
            if hasattr(obj, '_mcp_tool'):
                # Register the tool with FastMCP
                app.add_tool(obj)
                
                # Log the registration
                app.logger.debug(f"Registered tool: {obj.__name__}")
    
    # Log the total number of registered tools
    app.logger.info(f"Registered {len(app.list_tools())} tools")
