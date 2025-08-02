"""
Docker operations for the Filesystem MCP.

This module provides comprehensive Docker container and image management,
Docker Compose support, and volume/network management with FastMCP 2.10 compatibility.
"""
import io
import json
import logging
import os
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, BinaryIO, Generator
import asyncio
import io
import json
import logging
import os
import shlex
import subprocess
import tempfile
import time
from datetime import datetime
from enum import Enum
from pathlib import Path

import docker
from docker import APIClient
from docker.errors import DockerException, APIError, NotFound, ImageNotFound, ContainerError
from docker.models.containers import Container
from docker.models.images import Image
from docker.models.networks import Network
from docker.models.volumes import Volume
from fastapi import HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field, HttpUrl, validator, root_validator

from ..models import MCPTool

# Set up logging
logger = logging.getLogger(__name__)

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
    RESTARTING = "restarting"
    RECREATING = "recreating"
    ATTACHING = "attaching"
    DETACHING = "detaching"
    IMPORTING = "importing"
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
    """Base model for Docker operations with common fields."""
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
    """Request model for listing containers."""
    all: bool = Field(
        False,
        description="Show all containers (default shows just running)"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Filter containers using Docker's filter syntax"
    )


class ContainerListResponse(DockerBaseModel):
    """Response model for listing containers."""
    containers: List[ContainerInfo] = Field(
        default_factory=list,
        description="List of container information"
    )
    total: int = Field(0, description="Total number of containers")


# ===================================================================
# Image Models
# ===================================================================

class ImageInfo(DockerBaseModel):
    """Detailed information about a Docker image."""
    image_id: str = Field(..., description="Image ID")
    repo_tags: List[str] = Field(default_factory=list, description="Repository tags")
    repo_digests: List[str] = Field(default_factory=list, description="Repository digests")
    created: datetime = Field(..., description="Creation timestamp")
    size: int = Field(..., description="Size in bytes")
    virtual_size: int = Field(..., description="Virtual size in bytes")
    labels: Dict[str, str] = Field(default_factory=dict, description="Image labels")
    os: str = Field("linux", description="Operating system")
    architecture: str = Field("amd64", description="CPU architecture")


class ImageListRequest(BaseModel):
    """Request model for listing images."""
    all: bool = Field(
        False,
        description="Show all images (default hides intermediate images)"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Filter images using Docker's filter syntax"
    )


class ImageListResponse(DockerBaseModel):
    """Response model for listing images."""
    images: List[ImageInfo] = Field(
        default_factory=list,
        description="List of image information"
    )
    total: int = Field(0, description="Total number of images")


# ===================================================================
# Docker Compose Models
# ===================================================================

class ComposeServiceInfo(BaseModel):
    """Information about a Docker Compose service."""
    name: str = Field(..., description="Service name")
    container_name: Optional[str] = Field(None, description="Container name")
    command: Optional[str] = Field(None, description="Command")
    state: str = Field(..., description="Service state")
    status: str = Field(..., description="Service status")
    ports: List[str] = Field(default_factory=list, description="Published ports")


class ComposeProjectInfo(DockerBaseModel):
    """Information about a Docker Compose project."""
    name: str = Field(..., description="Project name")
    working_dir: str = Field(..., description="Project directory")
    config_files: List[str] = Field(
        default_factory=list,
        description="Compose configuration files"
    )
    services: List[ComposeServiceInfo] = Field(
        default_factory=list,
        description="Project services"
    )
    networks: List[str] = Field(
        default_factory=list,
        description="Project networks"
    )
    volumes: List[str] = Field(
        default_factory=list,
        description="Project volumes"
    )


# ===================================================================
# Volume Models
# ===================================================================

class VolumeInfo(DockerBaseModel):
    """Information about a Docker volume."""
    name: str = Field(..., description="Volume name")
    driver: str = Field("local", description="Volume driver")
    mountpoint: str = Field(..., description="Path where the volume is mounted")
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Volume labels"
    )
    options: Dict[str, str] = Field(
        default_factory=dict,
        description="Volume options"
    )
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    used_by: List[str] = Field(
        default_factory=list,
        description="Containers using this volume"
    )


# ===================================================================
# Network Models
# ===================================================================

class NetworkInfo(DockerBaseModel):
    """Information about a Docker network."""
    name: str = Field(..., description="Network name")
    id: str = Field(..., description="Network ID")
    driver: str = Field("bridge", description="Network driver")
    scope: str = Field("local", description="Network scope")
    enable_ipv6: bool = Field(False, description="IPv6 enabled")
    internal: bool = Field(False, description="Internal network")
    attachable: bool = Field(False, description="Allow manual container attachment")
    ingress: bool = Field(False, description="Ingress network")
    ipam: Dict[str, Any] = Field(
        default_factory=dict,
        description="IPAM configuration"
    )
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Network labels"
    )
    options: Dict[str, str] = Field(
        default_factory=dict,
        description="Network options"
    )
    created: Optional[datetime] = Field(None, description="Creation timestamp")


# ===================================================================
# Docker Client Management
# ===================================================================

def get_docker_client() -> DockerClient:
    """
    Get a Docker client instance.
    
    Returns:
        DockerClient: A Docker client instance.
        
    Raises:
        HTTPException: If Docker daemon is not available.
    """
    try:
        client = docker.from_env()
        # Test the connection
        client.ping()
        return client
    except Exception as e:
        error_msg = f"Failed to connect to Docker daemon: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_msg
        )


# ===================================================================
# Container Management Models
# ===================================================================

class ContainerActionRequest(BaseModel):
    """Base request model for container actions."""
    container_id: str = Field(..., description="Container ID or name")
    timeout: Optional[int] = Field(
        None,
        description="Timeout in seconds to wait for the container to stop before killing it"
    )
    force: bool = Field(
        False,
        description="Force the action (e.g., kill instead of stop)"
    )


class ContainerCreateRequest(BaseModel):
    """Request model for creating a container."""
    image: str = Field(..., description="Name of the image to use")
    name: Optional[str] = Field(None, description="Name for the container")
    command: Optional[Union[str, List[str]]] = Field(
        None,
        description="Command to run in the container"
    )
    entrypoint: Optional[Union[str, List[str]]] = Field(
        None,
        description="Entrypoint for the container"
    )
    environment: Optional[Dict[str, str]] = Field(
        None,
        description="Environment variables to set in the container"
    )
    ports: Optional[Dict[str, Union[int, str, Dict[str, str]]]] = Field(
        None,
        description="Port bindings (e.g., {'8000/tcp': 80})"
    )
    volumes: Optional[Dict[str, Dict[str, str]]] = Field(
        None,
        description="Volume bindings (e.g., {'/host/path': {'bind': '/container/path', 'mode': 'rw'}})"
    )
    network_mode: Optional[str] = Field(
        None,
        description="Networking mode (e.g., 'bridge', 'host', 'none')"
    )
    network: Optional[str] = Field(
        None,
        description="Network to connect the container to"
    )
    detach: bool = Field(
        True,
        description="Run container in the background"
    )
    auto_remove: bool = Field(
        False,
        description="Automatically remove the container when it exits"
    )
    tty: bool = Field(
        False,
        description="Allocate a pseudo-TTY"
    )
    stdin_open: bool = Field(
        False,
        description="Keep STDIN open even if not attached"
    )
    labels: Optional[Dict[str, str]] = Field(
        None,
        description="Labels to add to the container"
    )
    working_dir: Optional[str] = Field(
        None,
        description="Working directory inside the container"
    )
    user: Optional[str] = Field(
        None,
        description="Username or UID (format: <name|uid>[:<group|gid>])"
    )
    cap_add: Optional[List[str]] = Field(
        None,
        description="Add Linux capabilities"
    )
    cap_drop: Optional[List[str]] = Field(
        None,
        description="Drop Linux capabilities"
    )
    privileged: bool = Field(
        False,
        description="Give extended privileges to this container"
    )
    restart_policy: Optional[Dict[str, Any]] = Field(
        None,
        description="Restart policy (e.g., {'Name': 'on-failure', 'MaximumRetryCount': 5})"
    )
    mem_limit: Optional[Union[str, int]] = Field(
        None,
        description="Memory limit (e.g., '1g', 1073741824)"
    )
    memswap_limit: Optional[Union[str, int]] = Field(
        None,
        description="Total memory limit (memory + swap)"
    )
    cpus: Optional[float] = Field(
        None,
        description="Number of CPUs (e.g., 0.5, 1.5)"
    )
    cpu_shares: Optional[int] = Field(
        None,
        description="CPU shares (relative weight)"
    )
    cpu_quota: Optional[int] = Field(
        None,
        description="Limit CPU CFS quota"
    )
    cpu_period: Optional[int] = Field(
        None,
        description="Limit CPU CFS period"
    )
    cpuset_cpus: Optional[str] = Field(
        None,
        description="CPUs in which to allow execution (0-3, 0,1)"
    )
    cpuset_mems: Optional[str] = Field(
        None,
        description="Memory nodes (MEMs) in which to allow execution (0-3, 0,1)"
    )
    shm_size: Optional[Union[str, int]] = Field(
        None,
        description="Size of /dev/shm (e.g., '1g', 1073741824)"
    )
    tmpfs: Optional[Dict[str, str]] = Field(
        None,
        description="Mount tmpfs directories (e.g., {'/run': 'size=1g'})"
    )
    read_only: bool = Field(
        False,
        description="Mount the container's root filesystem as read only"
    )
    security_opt: Optional[List[str]] = Field(
        None,
        description="Security options (e.g., ['seccomp=unconfined'])"
    )
    storage_opt: Optional[Dict[str, Any]] = Field(
        None,
        description="Storage driver options"
    )
    log_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Logging configuration"
    )
    extra_hosts: Optional[Dict[str, str]] = Field(
        None,
        description="Additional host:IP mappings"
    )


class ContainerExecRequest(BaseModel):
    """Request model for executing a command in a container."""
    container_id: str = Field(..., description="Container ID or name")
    command: Union[str, List[str]] = Field(..., description="Command to execute")
    detach: bool = Field(
        False,
        description="If true, detach from the exec command"
    )
    tty: bool = Field(
        False,
        description="Allocate a pseudo-TTY"
    )
    stdin: bool = Field(
        False,
        description="Keep STDIN open even if not attached"
    )
    stdout: bool = Field(
        True,
        description="Return STDOUT"
    )
    stderr: bool = Field(
        True,
        description="Return STDERR"
    )
    user: Optional[str] = Field(
        None,
        description="User to run the command as"
    )
    environment: Optional[Dict[str, str]] = Field(
        None,
        description="Environment variables to set for the command"
    )
    workdir: Optional[str] = Field(
        None,
        description="Working directory for the command"
    )
    privileged: bool = Field(
        False,
        description="Run the exec process with extended privileges"
    )


class ContainerLogsRequest(BaseModel):
    """Request model for getting container logs."""
    container_id: str = Field(..., description="Container ID or name")
    follow: bool = Field(
        False,
        description="Follow log output"
    )
    stdout: bool = Field(
        True,
        description="Return STDOUT logs"
    )
    stderr: bool = Field(
        True,
        description="Return STDERR logs"
    )
    since: Optional[Union[int, datetime]] = Field(
        None,
        description="Show logs since this timestamp or relative (e.g., 2m for 2 minutes)"
    )
    until: Optional[Union[int, datetime]] = Field(
        None,
        description="Show logs before this timestamp or relative"
    )
    timestamps: bool = Field(
        False,
        description="Show timestamps"
    )
    tail: Optional[Union[int, str]] = Field(
        "all",
        description="Number of lines to show from the end of the logs"
    )


class ContainerStatsResponse(DockerBaseModel):
    """Response model for container statistics."""
    container_id: str = Field(..., description="Container ID")
    name: str = Field(..., description="Container name")
    read: datetime = Field(..., description="Time when stats were collected")
    cpu_stats: Dict[str, Any] = Field(..., description="CPU usage statistics")
    precpu_stats: Dict[str, Any] = Field(..., description="Previous CPU usage statistics")
    memory_stats: Dict[str, Any] = Field(..., description="Memory usage statistics")
    blkio_stats: Dict[str, Any] = Field(..., description="Block I/O statistics")
    networks: Dict[str, Any] = Field(..., description="Network statistics by interface")
    pids_stats: Dict[str, Any] = Field(..., description="Process ID statistics")
    num_procs: int = Field(..., description="Number of processes")
    storage_stats: Dict[str, Any] = Field(..., description="Storage statistics")
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_percent: float = Field(..., description="Memory usage percentage")
    memory_usage: int = Field(..., description="Memory usage in bytes")
    memory_limit: int = Field(..., description="Memory limit in bytes")
    network_rx: int = Field(..., description="Network received bytes")
    network_tx: int = Field(..., description="Network transmitted bytes")
    block_read: int = Field(..., description="Block read bytes")
    block_write: int = Field(..., description="Block write bytes")
    pids: int = Field(..., description="Number of PIDs")


# ===================================================================
# Container Operations
# ===================================================================

@MCPTool(
    name="list_containers",
    description="List Docker containers with filtering options",
    response_model=ContainerListResponse
)
async def list_containers(
    request: ContainerListRequest = ContainerListRequest()
) -> ContainerListResponse:
    """
    List Docker containers with detailed information and filtering options.
    
    This endpoint provides a comprehensive list of Docker containers with their current
    state, configuration, and resource usage. It supports filtering by various criteria
    such as status, label, name, and more.
    
    Args:
        request: ContainerListRequest with filtering options
        
    Returns:
        ContainerListResponse with list of containers and their details
        
    Raises:
        HTTPException: If there's an error accessing the Docker daemon or processing the request
    """
    try:
        client = get_docker_client()
        
        # Convert filters to format expected by Docker SDK
        filters = {}
        if request.filters:
            for key, value in request.filters.items():
                # Handle special filter types
                if key == 'status':
                    filters['status'] = value
                elif key == 'label':
                    if isinstance(value, list):
                        filters['label'] = value
                    else:
                        filters['label'] = [value]
                elif key == 'name':
                    filters['name'] = [value] if isinstance(value, str) else value
                elif key == 'id':
                    filters['id'] = [value] if isinstance(value, str) else value
                else:
                    filters[key] = value
        
        # Get container list with filters
        containers = client.containers.list(
            all=request.all,
            filters=filters or {}
        )
        
        # Process containers into response format
        container_list = []
        for container in containers:
            try:
                # Get detailed container info
                container.reload()
                container_info = _parse_container_info(container)
                container_list.append(container_info)
            except Exception as e:
                logger.warning(f"Error processing container {container.id}: {str(e)}")
                continue
        
        return ContainerListResponse(
            status=DockerOperationStatus.SUCCESS,
            containers=container_list,
            total=len(container_list),
            message=f"Found {len(container_list)} containers"
        )
        
    except Exception as e:
        error_msg = f"Failed to list containers: {str(e)}"
        logger.exception(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


def _parse_container_info(container: Container) -> ContainerInfo:
    """
    Parse Docker container object into a structured ContainerInfo object.
    
    Args:
        container: Docker container object
        
    Returns:
        ContainerInfo with parsed container details
    """
    attrs = container.attrs
    
    # Parse network settings
    networks = {}
    if 'NetworkSettings' in attrs and 'Networks' in attrs['NetworkSettings']:
        for net_name, net_config in attrs['NetworkSettings']['Networks'].items():
            networks[net_name] = {
                'ip_address': net_config.get('IPAddress'),
                'gateway': net_config.get('Gateway'),
                'aliases': net_config.get('Aliases', []),
                'network_id': net_config.get('NetworkID'),
                'mac_address': net_config.get('MacAddress'),
                'driver_opts': net_config.get('DriverOpts', {})
            }
    
    # Parse port bindings
    ports = []
    if 'NetworkSettings' in attrs and 'Ports' in attrs['NetworkSettings']:
        for container_port, host_ports in attrs['NetworkSettings']['Ports'].items():
            if host_ports:
                for host_mapping in (host_ports if isinstance(host_ports, list) else [host_ports]):
                    port_info = {
                        'container_port': container_port,
                        'host_ip': host_mapping.get('HostIp', '0.0.0.0'),
                        'host_port': host_mapping.get('HostPort')
                    }
                    ports.append(port_info)
    
    # Parse volume mounts
    mounts = []
    if 'Mounts' in attrs:
        for mount in attrs['Mounts']:
            mount_info = {
                'type': mount.get('Type'),
                'source': mount.get('Source'),
                'destination': mount.get('Destination'),
                'mode': mount.get('Mode', ''),
                'read_only': mount.get('RW', False) is False,
                'propagation': mount.get('Propagation', ''),
                'driver': mount.get('Driver', '')
            }
            if 'Name' in mount:
                mount_info['name'] = mount['Name']
            mounts.append(mount_info)
    
    # Parse environment variables
    env_vars = {}
    if 'Config' in attrs and 'Env' in attrs['Config']:
        for env_str in attrs['Config']['Env']:
            if '=' in env_str:
                key, val = env_str.split('=', 1)
                env_vars[key] = val
    
    # Parse labels
    labels = {}
    if 'Config' in attrs and 'Labels' in attrs['Config']:
        labels = attrs['Config']['Labels']
    
    # Parse health check
    health = None
    if 'State' in attrs and 'Health' in attrs['State']:
        health = {
            'status': attrs['State']['Health'].get('Status', '').lower(),
            'failing_streak': attrs['State']['Health'].get('FailingStreak', 0),
            'log': [
                {
                    'start': log.get('Start'),
                    'end': log.get('End'),
                    'exit_code': log.get('ExitCode'),
                    'output': log.get('Output')
                }
                for log in attrs['State']['Health'].get('Log', [])
            ]
        }
    
    # Parse resource limits
    resources = {}
    if 'HostConfig' in attrs:
        resources.update({
            'memory': attrs['HostConfig'].get('Memory'),
            'memory_swap': attrs['HostConfig'].get('MemorySwap'),
            'cpu_shares': attrs['HostConfig'].get('CpuShares'),
            'cpu_quota': attrs['HostConfig'].get('CpuQuota'),
            'cpu_period': attrs['HostConfig'].get('CpuPeriod'),
            'cpuset_cpus': attrs['HostConfig'].get('CpusetCpus'),
            'cpuset_mems': attrs['HostConfig'].get('CpusetMems'),
            'oom_kill_disable': attrs['HostConfig'].get('OomKillDisable'),
            'oom_score_adj': attrs['HostConfig'].get('OomScoreAdj'),
            'pids_limit': attrs['HostConfig'].get('PidsLimit'),
            'ulimits': attrs['HostConfig'].get('Ulimits')
        })
    
    # Parse restart policy
    restart_policy = {}
    if 'HostConfig' in attrs and 'RestartPolicy' in attrs['HostConfig']:
        restart_policy = {
            'name': attrs['HostConfig']['RestartPolicy'].get('Name', ''),
            'maximum_retry_count': attrs['HostConfig']['RestartPolicy'].get('MaximumRetryCount', 0)
        }
    
    # Get container stats
    stats = {}
    try:
        stats = container.stats(stream=False)
    except Exception as e:
        logger.warning(f"Failed to get stats for container {container.id}: {str(e)}")
    
    # Create container info object
    container_info = ContainerInfo(
        id=container.id,
        name=container.name,
        image=container.image.tags[0] if container.image.tags else container.image.id,
        image_id=container.image.id,
        command=' '.join(container.attrs['Config']['Cmd']) if container.attrs['Config'].get('Cmd') else None,
        created=datetime.fromisoformat(attrs['Created'].replace('Z', '+00:00')),
        status=container.status,
        state=ContainerState(container.status.lower()),
        ports=ports,
        mounts=mounts,
        networks=networks,
        labels=labels,
        environment=env_vars,
        health=health,
        resources=resources,
        restart_policy=restart_policy,
        stats=stats,
        host_config=attrs.get('HostConfig', {}),
        network_settings=attrs.get('NetworkSettings', {})
    )
    
    return container_info


@MCPTool(
    name="container_exec",
    description="Execute a command in a running container",
    response_model=DockerOperationResponse
)
async def container_exec(
    request: ContainerExecRequest
) -> DockerOperationResponse:
    """
    Execute a command inside a running container.
    
    Args:
        request: ContainerExecRequest with command and execution options
        
    Returns:
        DockerOperationResponse with command output and status
    """
    try:
        client = get_docker_client()
        container = client.containers.get(request.container_id)
        
        # Create the exec instance
        exec_id = container.client.api.exec_create(
            container.id,
            cmd=request.command,
            stdout=request.stdout,
            stderr=request.stderr,
            stdin=request.stdin,
            tty=request.tty,
            privileged=request.privileged,
            user=request.user,
            environment=request.environment,
            workdir=request.workdir
        )
        
        # Execute the command and capture output
        output = container.client.api.exec_start(
            exec_id,
            detach=request.detach,
            tty=request.tty,
            stream=request.detach or request.tty,
            socket=True if request.detach or request.tty else False
        )
        
        # For detached or TTY, return immediately
        if request.detach or request.tty:
            return DockerOperationResponse(
                status=DockerOperationStatus.SUCCESS,
                message=f"Command execution started in container {request.container_id}",
                data={"exec_id": exec_id}
            )
        
        # For non-detached, non-TTY, wait for and return output
        result = output.decode('utf-8')
        return DockerOperationResponse(
            status=DockerOperationStatus.SUCCESS,
            message=f"Command executed successfully in container {request.container_id}",
            data={"output": result}
        )
        
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Container {request.container_id} not found"
        )
    except Exception as e:
        error_msg = f"Failed to execute command in container {request.container_id}: {str(e)}"
        logger.exception(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@MCPTool(
    name="container_logs",
    description="Get logs from a container",
    response_model=DockerOperationResponse
)
async def container_logs(
    request: ContainerLogsRequest
) -> DockerOperationResponse:
    """
    Retrieve logs from a container.
    
    Args:
        request: ContainerLogsRequest with log retrieval options
        
    Returns:
        DockerOperationResponse with container logs
    """
    try:
        client = get_docker_client()
        container = client.containers.get(request.container_id)
        
        # Convert since/until to timestamps if they're datetime objects
        since = request.since.timestamp() if isinstance(request.since, datetime) else request.since
        until = request.until.timestamp() if isinstance(request.until, datetime) else request.until
        
        # Get logs from container
        logs = container.logs(
            stdout=request.stdout,
            stderr=request.stderr,
            stream=False,
            follow=False,
            timestamps=request.timestamps,
            tail=request.tail,
            since=since,
            until=until
        )
        
        # Decode logs to string
        log_output = logs.decode('utf-8')
        
        return DockerOperationResponse(
            status=DockerOperationStatus.SUCCESS,
            message=f"Retrieved logs for container {request.container_id}",
            data={"logs": log_output}
        )
        
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Container {request.container_id} not found"
        )
    except Exception as e:
        error_msg = f"Failed to get logs for container {request.container_id}: {str(e)}"
        logger.exception(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@MCPTool(
    name="container_stats",
    description="Get real-time statistics from a container",
    response_model=ContainerStatsResponse
)
async def container_stats(
    container_id: str = Field(..., description="Container ID or name"),
    stream: bool = Field(False, description="Stream stats continuously")
) -> ContainerStatsResponse:
    """
    Get real-time statistics from a container.
    
    Args:
        container_id: ID or name of the container
        stream: If True, stream stats continuously (not implemented yet)
        
    Returns:
        ContainerStatsResponse with container statistics
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)
        
        # Get container stats
        stats = container.stats(stream=False)
        
        # Calculate CPU percentage
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        cpu_percent = 0.0
        
        if system_delta > 0 and cpu_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage'] or [1]) * 100.0
        
        # Calculate memory usage and limit
        memory_usage = stats['memory_stats'].get('usage', 0)
        memory_limit = stats['memory_stats'].get('limit', 1)  # Avoid division by zero
        memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0.0
        
        # Network stats
        network_rx = 0
        network_tx = 0
        
        if 'networks' in stats:
            for if_name, net in stats['networks'].items():
                network_rx += net.get('rx_bytes', 0)
                network_tx += net.get('tx_bytes', 0)
        
        # Block I/O stats
        block_read = 0
        block_write = 0
        
        if 'blkio_stats' in stats and 'io_service_bytes_recursive' in stats['blkio_stats']:
            for entry in stats['blkio_stats']['io_service_bytes_recursive']:
                if entry['op'] == 'Read':
                    block_read += entry['value']
                elif entry['op'] == 'Write':
                    block_write += entry['value']
        
        # Create response
        return ContainerStatsResponse(
            container_id=container_id,
            name=container.name,
            read=datetime.now(),
            cpu_stats=stats.get('cpu_stats', {}),
            precpu_stats=stats.get('precpu_stats', {}),
            memory_stats=stats.get('memory_stats', {}),
            blkio_stats=stats.get('blkio_stats', {}),
            networks=stats.get('networks', {}),
            pids_stats=stats.get('pids_stats', {}),
            num_procs=len(stats.get('pids_stats', {}).get('current', [])),
            storage_stats=stats.get('storage_stats', {}),
            cpu_percent=round(cpu_percent, 2),
            memory_percent=round(memory_percent, 2),
            memory_usage=memory_usage,
            memory_limit=memory_limit,
            network_rx=network_rx,
            network_tx=network_tx,
            block_read=block_read,
            block_write=block_write,
            pids=stats.get('pids_stats', {}).get('current', 0)
        )
        
    except NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Container {container_id} not found"
        )
    except Exception as e:
        error_msg = f"Failed to get stats for container {container_id}: {str(e)}"
        logger.exception(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
    """
    List Docker containers with detailed information.
    
    Args:
        request: ContainerListRequest with filtering options.
        
    Returns:
        ContainerListResponse with list of containers and status.
    """
    try:
        client = get_docker_client()
        containers = client.containers.list(
            all=request.all,
            filters=request.filters or {}
        )
        
        container_info_list = []
        for container in containers:
            container_info = _parse_container_info(container)
            container_info_list.append(container_info)
        
        return ContainerListResponse(
            status=DockerOperationStatus.SUCCESS,
            containers=container_info_list,
            total=len(container_info_list)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to list containers: {str(e)}"
        logger.exception(error_msg)
        return ContainerListResponse(
            status=DockerOperationStatus.ERROR,
            error=error_msg
        )


def _parse_container_info(container: Container) -> ContainerInfo:
    """
    Parse container information into a ContainerInfo object.
    
    Args:
        container: Docker container object.
        
    Returns:
        ContainerInfo with container details.
    """
    attrs = container.attrs
    
    # Parse port mappings
    ports = []
    for container_port, host_ports in attrs.get('NetworkSettings', {}).get('Ports', {}).items():
        if host_ports:
            for host_port_info in host_ports:
                port_mapping = PortMapping(
                    container_port=container_port,
                    host_ip=host_port_info.get('HostIp', '0.0.0.0'),
                    host_port=int(host_port_info.get('HostPort', 0)),
                    protocol=container_port.split('/')[-1] if '/' in container_port else 'tcp'
                )
                ports.append(port_mapping)
    
    # Parse volume mounts
    mounts = []
    for mount in attrs.get('Mounts', []):
        volume_mount = VolumeMount(
            source=mount.get('Source', ''),
            target=mount.get('Destination', ''),
            read_only=mount.get('Mode', '').lower() == 'ro',
            type=mount.get('Type', 'volume')
        )
        mounts.append(volume_mount)
    
    # Parse environment variables
    env_vars = {}
    for env_var in attrs.get('Config', {}).get('Env', []):
        if '=' in env_var:
            key, value = env_var.split('=', 1)
            env_vars[key] = value
    
    # Create container info
    return ContainerInfo(
        container_id=container.id,
        name=container.name,
        image=container.image.tags[0] if container.image.tags else container.image.id,
        image_id=container.image.id,
        command=' '.join(container.attrs['Config']['Cmd']) if container.attrs['Config'].get('Cmd') else None,
        created=datetime.fromisoformat(attrs['Created'].replace('Z', '+00:00')),
        status=container.status,
        state=ContainerState(container.status.lower()),
        ports=ports,
        mounts=mounts,
        labels=attrs.get('Config', {}).get('Labels', {}),
        network_settings=attrs.get('NetworkSettings', {}),
        host_config=attrs.get('HostConfig', {}),
        env_vars=env_vars
    )


# ===================================================================
# Image Operations
# ===================================================================

@MCPTool(
    name="list_images",
    description="List Docker images with filtering options",
    response_model=ImageListResponse
)
async def list_images(
    request: ImageListRequest = ImageListRequest()
) -> ImageListResponse:
    """
    List Docker images with detailed information.
    
    Args:
        request: ImageListRequest with filtering options.
        
    Returns:
        ImageListResponse with list of images and status.
    """
    try:
        client = get_docker_client()
        images = client.images.list(
            all=request.all,
            filters=request.filters or {}
        )
        
        image_info_list = []
        for image in images:
            image_info = _parse_image_info(image)
            image_info_list.append(image_info)
        
        return ImageListResponse(
            status=DockerOperationStatus.SUCCESS,
            images=image_info_list,
            total=len(image_info_list)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to list images: {str(e)}"
        logger.exception(error_msg)
        return ImageListResponse(
            status=DockerOperationStatus.ERROR,
            error=error_msg
        )


def _parse_image_info(image: Image) -> ImageInfo:
    """
    Parse image information into an ImageInfo object.
    
    Args:
        image: Docker image object.
        
    Returns:
        ImageInfo with image details.
    """
    attrs = image.attrs
    
    return ImageInfo(
        image_id=image.id,
        repo_tags=image.tags,
        repo_digests=image.attrs.get('RepoDigests', []),
        created=datetime.fromisoformat(attrs['Created'].replace('Z', '+00:00')),
        size=attrs.get('Size', 0),
        virtual_size=attrs.get('VirtualSize', 0),
        labels=attrs.get('Config', {}).get('Labels', {}),
        os=attrs.get('Os', 'linux'),
        architecture=attrs.get('Architecture', 'amd64')
    )


# ===================================================================
# Docker Compose Operations
# ===================================================================

@MCPTool(
    name="compose_ps",
    description="List containers for a Docker Compose project",
    response_model=ComposeProjectInfo
)
async def compose_ps(
    project_dir: str = ".",
    project_name: Optional[str] = None
) -> ComposeProjectInfo:
    """
    List containers for a Docker Compose project.
    
    Args:
        project_dir: Path to the Docker Compose project directory.
        project_name: Optional project name (defaults to directory name).
        
    Returns:
        ComposeProjectInfo with project services and their status.
    """
    try:
        # This is a placeholder implementation
        # In a real implementation, you would use the Docker SDK or subprocess
        # to interact with docker-compose or docker compose
        
        # For now, return a mock response
        return ComposeProjectInfo(
            name=project_name or os.path.basename(os.path.abspath(project_dir)),
            working_dir=os.path.abspath(project_dir),
            config_files=["docker-compose.yml"],
            services=[],
            networks=[],
            volumes=[]
        )
        
    except Exception as e:
        error_msg = f"Failed to list Compose project: {str(e)}"
        logger.exception(error_msg)
        return ComposeProjectInfo(
            name=project_name or "unknown",
            working_dir=os.path.abspath(project_dir),
            status=DockerOperationStatus.ERROR,
            error=error_msg
        )


# ===================================================================
# Volume Operations
# ===================================================================

@MCPTool(
    name="list_volumes",
    description="List Docker volumes",
    response_model=List[VolumeInfo]
)
async def list_volumes() -> List[VolumeInfo]:
    """
    List all Docker volumes.
    
    Returns:
        List of VolumeInfo objects.
    """
    try:
        client = get_docker_client()
        volumes = client.volumes.list()
        
        volume_info_list = []
        for volume in volumes:
            volume_info = _parse_volume_info(volume)
            volume_info_list.append(volume_info)
        
        return volume_info_list
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to list volumes: {str(e)}"
        logger.exception(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


def _parse_volume_info(volume: Volume) -> VolumeInfo:
    """
    Parse volume information into a VolumeInfo object.
    
    Args:
        volume: Docker volume object.
        
    Returns:
        VolumeInfo with volume details.
    """
    attrs = volume.attrs
    
    return VolumeInfo(
        name=volume.name,
        driver=attrs.get('Driver', 'local'),
        mountpoint=attrs.get('Mountpoint', ''),
        labels=attrs.get('Labels', {}),
        options=attrs.get('Options', {}),
        created_at=datetime.fromisoformat(attrs['CreatedAt'].replace('Z', '+00:00')) if 'CreatedAt' in attrs else None,
        used_by=attrs.get('UsageData', {}).get('RefCount', [])
    )


# ===================================================================
# Network Operations
# ===================================================================

@MCPTool(
    name="list_networks",
    description="List Docker networks",
    response_model=List[NetworkInfo]
)
async def list_networks() -> List[NetworkInfo]:
    """
    List all Docker networks.
    
    Returns:
        List of NetworkInfo objects.
    """
    try:
        client = get_docker_client()
        networks = client.networks.list()
        
        network_info_list = []
        for network in networks:
            network_info = _parse_network_info(network)
            network_info_list.append(network_info)
        
        return network_info_list
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to list networks: {str(e)}"
        logger.exception(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


def _parse_network_info(network: Network) -> NetworkInfo:
    """
    Parse network information into a NetworkInfo object.
    
    Args:
        network: Docker network object.
        
    Returns:
        NetworkInfo with network details.
    """
    attrs = network.attrs
    
    return NetworkInfo(
        name=network.name,
        id=network.id,
        driver=attrs.get('Driver', 'bridge'),
        scope=attrs.get('Scope', 'local'),
        enable_ipv6=attrs.get('EnableIPv6', False),
        internal=attrs.get('Internal', False),
        attachable=attrs.get('Attachable', False),
        ingress=attrs.get('Ingress', False),
        ipam=attrs.get('IPAM', {}),
        labels=attrs.get('Labels', {}),
        options=attrs.get('Options', {}),
        created=datetime.fromisoformat(attrs['Created'].replace('Z', '+00:00')) if 'Created' in attrs else None
    )
