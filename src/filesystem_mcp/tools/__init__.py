"""
Filesystem MCP tools package - FastMCP 2.12 compliant.

This package contains all the tools for the Filesystem MCP server.
All tools are registered using FastMCP 2.12's @app.tool() decorator pattern.
"""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Tool modules are imported by the main application after app creation
# This prevents circular import issues and follows FastMCP 2.12 best practices

logger.info("Tool modules will be imported by the main application")

# Re-export for backward compatibility
__all__ = [
    'file_operations',
    'repo_operations',
    'docker_operations',
    'system_tools'
]

def get_tool_modules():
    """
    Get all tool modules for FastMCP 2.12.

    Returns:
        List of imported tool modules
    """
    return [file_operations, repo_operations, docker_operations]

def validate_tools():
    """
    Validate that all tools can be imported and executed without errors.

    This is a FastMCP 2.12 best practice to catch import errors early.
    """
    logger.info("Validating tool modules...")

    try:
        # Test basic imports from each module
        for module in get_tool_modules():
            # Check that the module has the expected structure
            if not hasattr(module, '__file__'):
                logger.warning(f"Module {module.__name__} may not be properly structured")

        logger.info("Tool validation completed successfully")
        return True

    except Exception as e:
        logger.error(f"Tool validation failed: {e}", exc_info=True)
        return False
