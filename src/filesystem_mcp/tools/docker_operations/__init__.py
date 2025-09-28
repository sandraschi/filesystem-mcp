"""
Docker operations for the Filesystem MCP - FastMCP 2.12 compliant.

This module provides comprehensive Docker container and image management,
Docker Compose support, and volume/network management with FastMCP 2.12 patterns.

Docker operations are organized into separate modules:
- containers.py: Container lifecycle management
- images.py: Image management and building
- networks_volumes.py: Network and volume operations
- compose.py: Docker Compose operations

All tools are registered using the @_get_app().tool() decorator pattern for maximum compatibility.
"""

# Import all Docker tools from organized modules
from .containers import *
from .images import *
from .networks_volumes import *
from .compose import *

# Export the main client function for backward compatibility
from .containers import get_docker_client

__all__ = [
    # Container operations
    'list_containers', 'get_container', 'create_container', 'start_container',
    'stop_container', 'restart_container', 'remove_container', 'container_exec',
    'container_logs', 'container_stats',

    # Image operations
    'list_images', 'get_image', 'pull_image', 'build_image', 'remove_image', 'prune_images',

    # Network & Volume operations
    'list_networks', 'get_network', 'create_network', 'remove_network', 'prune_networks',
    'list_volumes', 'get_volume', 'create_volume', 'remove_volume', 'prune_volumes',

    # Compose operations
    'compose_up', 'compose_down', 'compose_ps', 'compose_logs',
    'compose_config', 'compose_restart',

    # Utility functions
    'get_docker_client'
]

# Docker tools are implemented in separate modules for better organization

