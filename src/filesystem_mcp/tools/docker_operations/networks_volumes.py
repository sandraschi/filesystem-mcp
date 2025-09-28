"""
Docker network and volume management operations for the Filesystem MCP.

This module provides comprehensive network and volume lifecycle management
including creation, configuration, and removal operations.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

import docker
from docker.errors import DockerException, APIError, NotFound

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


# Pydantic models for network and volume operations
class DockerNetworkInfo(BaseModel):
    """Comprehensive Docker network information."""
    id: str
    name: str
    driver: str
    scope: str
    created: Optional[datetime] = None
    enable_ipv6: bool = False
    ipam: Dict[str, Any] = Field(default_factory=dict)
    internal: bool = False
    attachable: bool = False
    ingress: bool = False
    containers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    options: Dict[str, str] = Field(default_factory=dict)
    labels: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class DockerVolumeInfo(BaseModel):
    """Comprehensive Docker volume information."""
    name: str
    driver: str
    mountpoint: str
    created: Optional[datetime] = None
    labels: Dict[str, str] = Field(default_factory=dict)
    options: Dict[str, str] = Field(default_factory=dict)
    scope: str = "local"

    model_config = ConfigDict(from_attributes=True)


class DockerOperationStatus(str, Enum):
    """Status enumeration for Docker operations."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class NetworkListResponse(BaseModel):
    """Response model for network listing operations."""
    status: DockerOperationStatus
    networks: List[DockerNetworkInfo] = Field(default_factory=list)
    total: int = 0
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VolumeListResponse(BaseModel):
    """Response model for volume listing operations."""
    status: DockerOperationStatus
    volumes: List[DockerVolumeInfo] = Field(default_factory=list)
    total: int = 0
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NetworkResponse(BaseModel):
    """Response model for single network operations."""
    status: DockerOperationStatus
    network: Optional[DockerNetworkInfo] = None
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VolumeResponse(BaseModel):
    """Response model for single volume operations."""
    status: DockerOperationStatus
    volume: Optional[DockerVolumeInfo] = None
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NetworkCreateRequest(BaseModel):
    """Request model for network creation."""
    name: str
    driver: str = "bridge"
    options: Dict[str, str] = Field(default_factory=dict)
    ipam: Optional[Dict[str, Any]] = None
    internal: bool = False
    attachable: bool = False
    ingress: bool = False
    labels: Dict[str, str] = Field(default_factory=dict)
    enable_ipv6: bool = False

    model_config = ConfigDict(from_attributes=True)


class VolumeCreateRequest(BaseModel):
    """Request model for volume creation."""
    name: str
    driver: str = "local"
    driver_opts: Dict[str, str] = Field(default_factory=dict)
    labels: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


def get_docker_client():
    """Get Docker client with proper error handling."""
    try:
        client = docker.from_env()
        # Test the connection
        client.ping()
        return client
    except DockerException as e:
        logger.error(f"Failed to connect to Docker daemon: {e}")
        raise Exception("Docker daemon is not running or not accessible") from e


@_get_app().tool()
async def list_networks(
    filters: Optional[Dict[str, Any]] = None
) -> dict:
    """List Docker networks with detailed information and filtering options.

    Retrieves comprehensive information about Docker networks including
    configuration, connected containers, and network settings.

    Args:
        filters: Dictionary of filters to apply (e.g., {"driver": ["bridge"]})

    Returns:
        Dictionary containing network list and metadata

    Error Handling:
        Returns error information if Docker daemon is not accessible
    """
    try:
        client = get_docker_client()
        networks = client.networks.list(filters=filters or {})

        network_list = []
        for network in networks:
            try:
                network_list.append(_parse_network_info(network))
            except Exception as e:
                logger.warning(f"Failed to parse network {network.id}: {e}")

        return NetworkListResponse(
            status=DockerOperationStatus.SUCCESS,
            networks=network_list,
            total=len(network_list)
        )

    except Exception as e:
        return NetworkListResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to list networks: {str(e)}"
        )


@_get_app().tool()
async def get_network(network_id: str) -> dict:
    """Get detailed information about a specific Docker network.

    Retrieves comprehensive information about a network including its
    configuration, connected containers, and IPAM settings.

    Args:
        network_id: Network ID or name

    Returns:
        Dictionary containing network information and metadata

    Error Handling:
        Returns error information if network not found or Docker daemon inaccessible
    """
    try:
        client = get_docker_client()
        network = client.networks.get(network_id)

        network_info = _parse_network_info(network)

        return NetworkResponse(
            status=DockerOperationStatus.SUCCESS,
            network=network_info
        )

    except NotFound:
        return NetworkResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Network '{network_id}' not found"
        )
    except Exception as e:
        return NetworkResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to get network info: {str(e)}"
        )


@_get_app().tool()
async def create_network(
    name: str,
    driver: str = "bridge",
    options: Optional[Dict[str, str]] = None,
    ipam: Optional[Dict[str, Any]] = None,
    internal: bool = False,
    attachable: bool = False,
    ingress: bool = False,
    labels: Optional[Dict[str, str]] = None,
    enable_ipv6: bool = False
) -> dict:
    """Create a new Docker network with custom configuration.

    Creates a network with specified driver, IPAM configuration, and options.

    Args:
        name: Network name
        driver: Network driver (bridge, overlay, etc.)
        options: Driver-specific options
        ipam: IP Address Management configuration
        internal: Restrict external access
        attachable: Enable manual container attachment
        ingress: Create swarm routing mesh network
        labels: Network labels
        enable_ipv6: Enable IPv6 networking

    Returns:
        Dictionary containing creation result and network info

    Error Handling:
        Returns error information if creation fails
    """
    try:
        client = get_docker_client()

        # Prepare network configuration
        network_config = {
            'name': name,
            'driver': driver,
            'internal': internal,
            'attachable': attachable,
            'ingress': ingress,
            'enable_ipv6': enable_ipv6
        }

        if options:
            network_config['options'] = options
        if ipam:
            network_config['ipam'] = ipam
        if labels:
            network_config['labels'] = labels

        # Create the network
        network = client.networks.create(**network_config)

        # Parse the created network info
        network_info = _parse_network_info(network)

        return NetworkResponse(
            status=DockerOperationStatus.SUCCESS,
            network=network_info
        )

    except Exception as e:
        return NetworkResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to create network: {str(e)}"
        )


@_get_app().tool()
async def remove_network(network_id: str) -> dict:
    """Remove a Docker network.

    Removes a network. The network must not have any connected containers.

    Args:
        network_id: Network ID or name to remove

    Returns:
        Dictionary containing removal result

    Error Handling:
        Returns error information if network not found or removal fails
    """
    try:
        client = get_docker_client()
        network = client.networks.get(network_id)

        network.remove()

        return {
            "status": DockerOperationStatus.SUCCESS,
            "message": f"Network '{network_id}' removed successfully",
            "network_id": network_id
        }

    except NotFound:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Network '{network_id}' not found"
        }
    except Exception as e:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Failed to remove network: {str(e)}"
        }


@_get_app().tool()
async def prune_networks(
    filters: Optional[Dict[str, Any]] = None
) -> dict:
    """Prune unused Docker networks.

    Removes networks that are not used by any containers.

    Args:
        filters: Additional filters for network pruning

    Returns:
        Dictionary containing pruning results

    Error Handling:
        Returns error information if pruning fails
    """
    try:
        client = get_docker_client()

        # Prune networks
        result = client.networks.prune(filters=filters or {})

        return {
            "status": DockerOperationStatus.SUCCESS,
            "message": "Successfully pruned unused networks",
            "networks_deleted": result.get('NetworksDeleted', []),
            "space_reclaimed": result.get('SpaceReclaimed', 0)
        }

    except Exception as e:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Failed to prune networks: {str(e)}"
        }


@_get_app().tool()
async def list_volumes(
    filters: Optional[Dict[str, Any]] = None
) -> dict:
    """List Docker volumes with detailed information and filtering options.

    Retrieves comprehensive information about Docker volumes including
    their drivers, mount points, and configuration.

    Args:
        filters: Dictionary of filters to apply (e.g., {"driver": ["local"]})

    Returns:
        Dictionary containing volume list and metadata

    Error Handling:
        Returns error information if Docker daemon is not accessible
    """
    try:
        client = get_docker_client()
        volumes = client.volumes.list(filters=filters or {})

        volume_list = []
        for volume in volumes:
            try:
                volume_list.append(_parse_volume_info(volume))
            except Exception as e:
                logger.warning(f"Failed to parse volume {volume.name}: {e}")

        return VolumeListResponse(
            status=DockerOperationStatus.SUCCESS,
            volumes=volume_list,
            total=len(volume_list)
        )

    except Exception as e:
        return VolumeListResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to list volumes: {str(e)}"
        )


@_get_app().tool()
async def get_volume(volume_name: str) -> dict:
    """Get detailed information about a specific Docker volume.

    Retrieves comprehensive information about a volume including its
    driver, mount point, and configuration.

    Args:
        volume_name: Volume name

    Returns:
        Dictionary containing volume information and metadata

    Error Handling:
        Returns error information if volume not found or Docker daemon inaccessible
    """
    try:
        client = get_docker_client()
        volume = client.volumes.get(volume_name)

        volume_info = _parse_volume_info(volume)

        return VolumeResponse(
            status=DockerOperationStatus.SUCCESS,
            volume=volume_info
        )

    except NotFound:
        return VolumeResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Volume '{volume_name}' not found"
        )
    except Exception as e:
        return VolumeResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to get volume info: {str(e)}"
        )


@_get_app().tool()
async def create_volume(
    name: str,
    driver: str = "local",
    driver_opts: Optional[Dict[str, str]] = None,
    labels: Optional[Dict[str, str]] = None
) -> dict:
    """Create a new Docker volume with custom configuration.

    Creates a volume with specified driver and options for persistent storage.

    Args:
        name: Volume name
        driver: Volume driver (local, etc.)
        driver_opts: Driver-specific options
        labels: Volume labels

    Returns:
        Dictionary containing creation result and volume info

    Error Handling:
        Returns error information if creation fails
    """
    try:
        client = get_docker_client()

        # Prepare volume configuration
        volume_config = {
            'name': name,
            'driver': driver
        }

        if driver_opts:
            volume_config['driver_opts'] = driver_opts
        if labels:
            volume_config['labels'] = labels

        # Create the volume
        volume = client.volumes.create(**volume_config)

        # Parse the created volume info
        volume_info = _parse_volume_info(volume)

        return VolumeResponse(
            status=DockerOperationStatus.SUCCESS,
            volume=volume_info
        )

    except Exception as e:
        return VolumeResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to create volume: {str(e)}"
        )


@_get_app().tool()
async def remove_volume(
    volume_name: str,
    force: bool = False
) -> dict:
    """Remove a Docker volume.

    Removes a volume. Use force=True to remove volumes that are in use.

    Args:
        volume_name: Volume name to remove
        force: Force removal even if volume is in use

    Returns:
        Dictionary containing removal result

    Error Handling:
        Returns error information if volume not found or removal fails
    """
    try:
        client = get_docker_client()
        volume = client.volumes.get(volume_name)

        volume.remove(force=force)

        return {
            "status": DockerOperationStatus.SUCCESS,
            "message": f"Volume '{volume_name}' removed successfully",
            "volume_name": volume_name,
            "force_used": force
        }

    except NotFound:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Volume '{volume_name}' not found"
        }
    except Exception as e:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Failed to remove volume: {str(e)}"
        }


@_get_app().tool()
async def prune_volumes(
    filters: Optional[Dict[str, Any]] = None
) -> dict:
    """Prune unused Docker volumes.

    Removes volumes that are not used by any containers.

    Args:
        filters: Additional filters for volume pruning

    Returns:
        Dictionary containing pruning results and space freed

    Error Handling:
        Returns error information if pruning fails
    """
    try:
        client = get_docker_client()

        # Prune volumes
        result = client.volumes.prune(filters=filters or {})

        return {
            "status": DockerOperationStatus.SUCCESS,
            "message": "Successfully pruned unused volumes",
            "volumes_deleted": result.get('VolumesDeleted', []),
            "space_reclaimed": result.get('SpaceReclaimed', 0)
        }

    except Exception as e:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Failed to prune volumes: {str(e)}"
        }


def _parse_network_info(network) -> DockerNetworkInfo:
    """
    Parse Docker network object into a structured DockerNetworkInfo object.

    Args:
        network: Docker network object

    Returns:
        DockerNetworkInfo with parsed network details
    """
    attrs = network.attrs

    # Parse creation time
    created = None
    if 'Created' in attrs:
        try:
            created_str = attrs['Created']
            if created_str.endswith('Z'):
                created_str = created_str[:-1] + '+00:00'
            created = datetime.fromisoformat(created_str)
        except (ValueError, TypeError):
            pass

    return DockerNetworkInfo(
        id=network.id,
        name=network.name,
        driver=attrs.get('Driver', 'unknown'),
        scope=attrs.get('Scope', 'unknown'),
        created=created,
        enable_ipv6=attrs.get('EnableIPv6', False),
        ipam=attrs.get('IPAM', {}),
        internal=attrs.get('Internal', False),
        attachable=attrs.get('Attachable', False),
        ingress=attrs.get('Ingress', False),
        containers=attrs.get('Containers', {}),
        options=attrs.get('Options', {}),
        labels=attrs.get('Labels', {})
    )


def _parse_volume_info(volume) -> DockerVolumeInfo:
    """
    Parse Docker volume object into a structured DockerVolumeInfo object.

    Args:
        volume: Docker volume object

    Returns:
        DockerVolumeInfo with parsed volume details
    """
    attrs = volume.attrs

    # Parse creation time
    created = None
    if 'CreatedAt' in attrs:
        try:
            created_str = attrs['CreatedAt']
            if created_str.endswith('Z'):
                created_str = created_str[:-1] + '+00:00'
            created = datetime.fromisoformat(created_str)
        except (ValueError, TypeError):
            pass

    return DockerVolumeInfo(
        name=volume.name,
        driver=attrs.get('Driver', 'local'),
        mountpoint=attrs.get('Mountpoint', ''),
        created=created,
        labels=attrs.get('Labels', {}),
        options=attrs.get('Options', {}),
        scope=attrs.get('Scope', 'local')
    )
