"""
Docker operations for the Filesystem MCP - FastMCP 2.12 compliant.

This module provides comprehensive Docker container and image management,
Docker Compose support, and volume/network management with FastMCP 2.12 patterns.
All tools are registered using the @_get_app().tool() decorator pattern for maximum compatibility.
"""
import io
import json
import logging
import os
import time
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, BinaryIO, Generator
import asyncio
import shlex
import subprocess
import tempfile

import docker
from docker import APIClient
from docker.errors import DockerException, APIError, NotFound, ImageNotFound, ContainerError
from docker.models.containers import Container
from docker.models.images import Image
from docker.models.networks import Network
from docker.models.volumes import Volume
from pydantic import BaseModel, Field, field_validator, ConfigDict

# Configure structured logging for this module
logger = logging.getLogger(__name__)

# Import app locally in functions to avoid circular imports
def _get_app():
    """Get the app instance locally to avoid circular imports."""
    import sys
    import os
    # Add src to path if not already there
    src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    import filesystem_mcp
    return filesystem_mcp.app

# Type aliases
DockerClient = docker.DockerClient
AnyPath = Union[str, os.PathLike]

# ===================================================================
# Base Models
# ===================================================================

class DockerOperationStatus(str, Enum):
    """Status of a Docker operation."""
    SUCCESS = "success"
    ERROR = "error"
    NOT_FOUND = "not_found"
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    RESTARTING = "restarting"
    DEAD = "dead"
    CREATED = "created"
    EXITED = "exited"
    BUILDING = "building"
    PULLING = "pulling"
    PUSHING = "pushing"
    LOADING = "loading"
    SAVING = "saving"
    IMPORTING = "importing"
    EXPORTING = "exporting"
    TAG = "tagging"
    REMOVING = "removing"
    PRUNING = "pruning"
    EXECUTING = "executing"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"
    KILLING = "killing"
    RENAMING = "renaming"
    UPDATING = "updating"
    ROLLING_BACK = "rolling_back"
    PAUSING = "pausing"
    UNPAUSING = "unpausing"
    RECREATING = "recreating"
    ATTACHING = "attaching"
    DETACHING = "detaching"
    COMMITTING = "committing"
    COPYING = "copying"
    WAITING = "waiting"
    COMPLETE = "complete"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"

class DockerBaseModel(BaseModel):
    """Base model for Docker operations with common fields - FastMCP 2.12 compliant."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: DockerOperationStatus = Field(
        DockerOperationStatus.SUCCESS,
        description="Status of the operation"
    )
    message: Optional[str] = Field(
        None,
        description="Additional information about the operation"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if status is not SUCCESS"
    )

# ===================================================================
# Container Models
# ===================================================================

class ContainerState(str, Enum):
    """Possible states of a Docker container."""
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    RESTARTING = "restarting"
    DEAD = "dead"
    CREATED = "created"
    EXITED = "exited"

class PortMapping(BaseModel):
    """Model for container port mappings."""
    container_port: int = Field(..., description="Port inside the container")
    host_ip: str = Field("0.0.0.0", description="Host IP to bind to")
    host_port: Optional[int] = Field(None, description="Port on the host")
    protocol: str = Field("tcp", description="Port protocol (tcp/udp)")

class VolumeMount(BaseModel):
    """Model for volume mounts in containers."""
    source: str = Field(..., description="Source path or volume name")
    target: str = Field(..., description="Mount path inside the container")
    read_only: bool = Field(False, description="Mount as read-only")
    type: str = Field("volume", description="Type of mount (volume/bind/tmpfs)")

class ContainerInfo(DockerBaseModel):
    """Detailed information about a Docker container."""
    container_id: str = Field(..., description="Container ID")
    name: str = Field(..., description="Container name")
    image: str = Field(..., description="Image name and tag")
    image_id: str = Field(..., description="Image ID")
    command: Optional[str] = Field(None, description="Command used to start the container")
    created: datetime = Field(..., description="Creation timestamp")
    status: str = Field(..., description="Current status")
    state: ContainerState = Field(..., description="Container state")
    ports: List[PortMapping] = Field(default_factory=list, description="Port mappings")
    mounts: List[VolumeMount] = Field(default_factory=list, description="Volume mounts")
    labels: Dict[str, str] = Field(default_factory=dict, description="Container labels")
    network_settings: Dict[str, Any] = Field(default_factory=dict, description="Network settings")
    host_config: Dict[str, Any] = Field(default_factory=dict, description="Host configuration")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Environment variables")

class ContainerListRequest(BaseModel):
    """Request model for listing containers - FastMCP 2.12 compliant."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    all: bool = Field(
        False,
        description="Show all containers (default shows just running)"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Filter containers using Docker's filter syntax"
    )

class ContainerListResponse(DockerBaseModel):
    """Response model for listing containers - FastMCP 2.12 compliant."""
    containers: List[ContainerInfo] = Field(
        default_factory=list,
        description="List of container information"
    )
    total: int = Field(0, description="Total number of containers")

# ===================================================================
# Docker Operations
# ===================================================================

def get_docker_client() -> DockerClient:
    """
    Get a Docker client instance.
    
    Returns:
        DockerClient: A Docker client instance.
        
    Raises:
        Exception: If Docker daemon is not available.
    """
    try:
        client = docker.from_env()
        # Test the connection
        client.ping()
        return client
    except DockerException as e:
        logger.error(f"Failed to connect to Docker daemon: {e}")
        raise Exception("Docker daemon is not running or not accessible") from e

@_get_app().tool()
async def list_containers(
    all_containers: bool = False,
    filters: Optional[Dict[str, Any]] = None
) -> dict:
    """List Docker containers with detailed information and filtering options.

    This tool provides comprehensive information about Docker containers including
    their status, configuration, resource usage, and network settings. It includes
    proper error handling and structured logging for debugging.

    Args:
        all_containers: If True, show all containers (default shows just running)
        filters: Dictionary of filters to apply (e.g., {"status": ["running"]})

    Returns:
        Dictionary containing container list and metadata

    Error Handling:
        Returns error information if Docker daemon is not accessible or containers cannot be listed
    """
    try:
        client = get_docker_client()
        containers = client.containers.list(
            all=all_containers,
            filters=filters or {}
        )
        
        container_list = []
        for container in containers:
            try:
                container_list.append(_parse_container_info(container))
            except Exception as e:
                logger.warning(f"Failed to parse container {container.id}: {e}")
        
        return ContainerListResponse(
            status=DockerOperationStatus.SUCCESS,
            containers=container_list,
            total=len(container_list)
        )
    except Exception as e:
        return ContainerListResponse(
            status=DockerOperationStatus.ERROR,
            error=str(e)
        )

def _parse_container_info(container: Container) -> ContainerInfo:
    """
    Parse Docker container object into a structured ContainerInfo object.
    
    Args:
        container: Docker container object
        
    Returns:
        ContainerInfo with parsed container details
    """
    container.reload()  # Ensure we have the latest state
    
    # Parse port mappings
    ports = []
    for container_port, host_ports in container.ports.items():
        if not host_ports:
            continue
            
        port_parts = container_port.split('/')
        container_port_num = int(port_parts[0])
        protocol = port_parts[1] if len(port_parts) > 1 else 'tcp'
        
        if isinstance(host_ports, list):
            for host_mapping in host_ports:
                ports.append(PortMapping(
                    container_port=container_port_num,
                    host_ip=host_mapping.get('HostIp', '0.0.0.0'),
                    host_port=int(host_mapping['HostPort']),
                    protocol=protocol
                ))
        elif isinstance(host_ports, dict):
            ports.append(PortMapping(
                container_port=container_port_num,
                host_ip=host_ports.get('HostIp', '0.0.0.0'),
                host_port=int(host_ports['HostPort']),
                protocol=protocol
            ))
    
    # Parse volume mounts
    mounts = []
    for mount in container.attrs.get('Mounts', []):
        mounts.append(VolumeMount(
            source=mount.get('Source', ''),
            target=mount.get('Destination', ''),
            read_only=mount.get('Mode', '').lower() == 'ro',
            type=mount.get('Type', 'volume')
        ))
    
    # Parse environment variables
    env_vars = {}
    for env in container.attrs.get('Config', {}).get('Env', []):
        if '=' in env:
            key, value = env.split('=', 1)
            env_vars[key] = value
    
    return ContainerInfo(
        container_id=container.id,
        name=container.name,
        image=container.image.tags[0] if container.image.tags else container.image.id,
        image_id=container.image.id,
        command=' '.join(container.attrs['Config']['Cmd']) if container.attrs['Config'].get('Cmd') else None,
        created=container.attrs['Created'],
        status=container.status,
        state=ContainerState(container.status.lower()),
        ports=ports,
        mounts=mounts,
        labels=container.labels,
        network_settings=container.attrs.get('NetworkSettings', {}),
        host_config=container.attrs.get('HostConfig', {}),
        env_vars=env_vars
    )

# Add more MCP tool decorators to other functions as needed

if __name__ == "__main__":
    # Example usage
    # Test code removed - use proper test suite in tests/ directory
    pass
