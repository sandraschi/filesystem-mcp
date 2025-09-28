"""
Docker container management operations for the Filesystem MCP.

This module provides comprehensive container lifecycle management including
creation, execution, monitoring, and removal operations.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

import docker
from docker.errors import DockerException, APIError, NotFound, ContainerError

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


# Pydantic models for container operations
class PortMapping(BaseModel):
    """Port mapping configuration for containers."""
    container_port: int
    host_ip: str = "0.0.0.0"
    host_port: int
    protocol: str = "tcp"

    model_config = ConfigDict(from_attributes=True)


class VolumeMount(BaseModel):
    """Volume mount configuration for containers."""
    source: str
    target: str
    read_only: bool = False
    type: str = "volume"

    model_config = ConfigDict(from_attributes=True)


class ContainerInfo(BaseModel):
    """Comprehensive container information."""
    id: str
    name: str
    image: str
    status: str
    state: str
    created: datetime
    ports: List[PortMapping] = Field(default_factory=list)
    mounts: List[VolumeMount] = Field(default_factory=list)
    command: str
    entrypoint: Optional[str] = None
    working_dir: Optional[str] = None
    environment: Dict[str, str] = Field(default_factory=dict)
    labels: Dict[str, str] = Field(default_factory=dict)
    network_mode: str
    restart_policy: str
    cpu_usage: Optional[float] = None
    memory_usage: Optional[int] = None
    network_settings: Dict[str, Any] = Field(default_factory=dict)
    host_config: Dict[str, Any] = Field(default_factory=dict)
    env_vars: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class DockerOperationStatus(str, Enum):
    """Status enumeration for Docker operations."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class ContainerListResponse(BaseModel):
    """Response model for container listing operations."""
    status: DockerOperationStatus
    containers: List[ContainerInfo] = Field(default_factory=list)
    total: int = 0
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ContainerResponse(BaseModel):
    """Response model for single container operations."""
    status: DockerOperationStatus
    container: Optional[ContainerInfo] = None
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ContainerCreateRequest(BaseModel):
    """Request model for container creation."""
    image: str
    name: Optional[str] = None
    command: Optional[Union[str, List[str]]] = None
    ports: Dict[str, Union[int, List[int]]] = Field(default_factory=dict)
    volumes: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    environment: Dict[str, str] = Field(default_factory=dict)
    working_dir: Optional[str] = None
    detach: bool = True
    auto_remove: bool = False
    network_mode: Optional[str] = None
    restart_policy: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ContainerExecRequest(BaseModel):
    """Request model for container command execution."""
    container_id: str
    command: Union[str, List[str]]
    detach: bool = False
    tty: bool = False
    stdin: bool = False
    stdout: bool = True
    stderr: bool = True
    stream: bool = False
    socket: bool = False

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


@_get_app().tool()
async def get_container(
    container_id: str,
    show_stats: bool = False
) -> dict:
    """Get detailed information about a specific Docker container.

    Retrieves comprehensive information about a container including its configuration,
    status, resource usage, network settings, and mounted volumes.

    Args:
        container_id: Container ID or name
        show_stats: Whether to include real-time resource statistics

    Returns:
        Dictionary containing container information and metadata

    Error Handling:
        Returns error information if container not found or Docker daemon inaccessible
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)

        container_info = _parse_container_info(container, show_stats)

        return ContainerResponse(
            status=DockerOperationStatus.SUCCESS,
            container=container_info
        )

    except NotFound:
        return ContainerResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Container '{container_id}' not found"
        )
    except Exception as e:
        return ContainerResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to get container info: {str(e)}"
        )


@_get_app().tool()
async def create_container(
    image: str,
    name: Optional[str] = None,
    command: Optional[Union[str, List[str]]] = None,
    ports: Optional[Dict[str, Union[int, List[int]]]] = None,
    volumes: Optional[Dict[str, Dict[str, str]]] = None,
    environment: Optional[Dict[str, str]] = None,
    working_dir: Optional[str] = None,
    detach: bool = True,
    auto_remove: bool = False,
    network_mode: Optional[str] = None,
    restart_policy: Optional[str] = None
) -> dict:
    """Create a new Docker container with custom configuration.

    Creates a container with specified image, configuration, port mappings,
    volume mounts, environment variables, and other settings.

    Args:
        image: Docker image to use
        name: Optional container name
        command: Command to run in container
        ports: Port mapping configuration
        volumes: Volume mount configuration
        environment: Environment variables
        working_dir: Working directory in container
        detach: Run container in background
        auto_remove: Auto-remove container when stopped
        network_mode: Network mode (bridge, host, etc.)
        restart_policy: Restart policy (no, always, on-failure, etc.)

    Returns:
        Dictionary containing creation result and container info

    Error Handling:
        Returns error information if creation fails or image not found
    """
    try:
        client = get_docker_client()

        # Prepare container configuration
        container_config = {
            'image': image,
            'detach': detach,
            'auto_remove': auto_remove,
        }

        if name:
            container_config['name'] = name
        if command:
            container_config['command'] = command
        if working_dir:
            container_config['working_dir'] = working_dir
        if environment:
            container_config['environment'] = environment

        # Handle port mappings
        if ports:
            port_bindings = {}
            for container_port, host_port in ports.items():
                if isinstance(host_port, list):
                    port_bindings[container_port] = [{'HostPort': str(p)} for p in host_port]
                else:
                    port_bindings[container_port] = str(host_port)
            container_config['ports'] = list(ports.keys())
            container_config['port_bindings'] = port_bindings

        # Handle volume mounts
        if volumes:
            container_config['volumes'] = list(volumes.keys())
            binds = []
            for host_path, vol_config in volumes.items():
                bind_str = host_path
                if vol_config.get('mode'):
                    bind_str += f":{vol_config['mode']}"
                binds.append(bind_str)
            container_config['binds'] = binds

        # Network and restart policies
        if network_mode:
            container_config['network_mode'] = network_mode
        if restart_policy:
            container_config['restart_policy'] = {'Name': restart_policy}

        # Create the container
        container = client.containers.create(**container_config)

        # Parse the created container info
        container_info = _parse_container_info(container)

        return ContainerResponse(
            status=DockerOperationStatus.SUCCESS,
            container=container_info
        )

    except ImageNotFound:
        return ContainerResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Image '{image}' not found locally or in registry"
        )
    except Exception as e:
        return ContainerResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to create container: {str(e)}"
        )


@_get_app().tool()
async def start_container(container_id: str) -> dict:
    """Start a stopped Docker container.

    Starts a container that was previously created but is currently stopped.

    Args:
        container_id: Container ID or name to start

    Returns:
        Dictionary containing operation result

    Error Handling:
        Returns error information if container not found or start fails
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)

        if container.status == 'running':
            return ContainerResponse(
                status=DockerOperationStatus.WARNING,
                container=_parse_container_info(container),
                error="Container is already running"
            )

        container.start()

        # Refresh container info
        container.reload()
        container_info = _parse_container_info(container)

        return ContainerResponse(
            status=DockerOperationStatus.SUCCESS,
            container=container_info
        )

    except NotFound:
        return ContainerResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Container '{container_id}' not found"
        )
    except Exception as e:
        return ContainerResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to start container: {str(e)}"
        )


@_get_app().tool()
async def stop_container(
    container_id: str,
    timeout: int = 10
) -> dict:
    """Stop a running Docker container.

    Stops a running container gracefully with optional timeout.

    Args:
        container_id: Container ID or name to stop
        timeout: Seconds to wait before force-killing (default: 10)

    Returns:
        Dictionary containing operation result

    Error Handling:
        Returns error information if container not found or stop fails
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)

        if container.status != 'running':
            return ContainerResponse(
                status=DockerOperationStatus.WARNING,
                container=_parse_container_info(container),
                error=f"Container is not running (status: {container.status})"
            )

        container.stop(timeout=timeout)

        # Refresh container info
        container.reload()
        container_info = _parse_container_info(container)

        return ContainerResponse(
            status=DockerOperationStatus.SUCCESS,
            container=container_info
        )

    except NotFound:
        return ContainerResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Container '{container_id}' not found"
        )
    except Exception as e:
        return ContainerResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to stop container: {str(e)}"
        )


@_get_app().tool()
async def restart_container(
    container_id: str,
    timeout: int = 10
) -> dict:
    """Restart a Docker container.

    Restarts a container by stopping and starting it again.

    Args:
        container_id: Container ID or name to restart
        timeout: Seconds to wait for graceful stop (default: 10)

    Returns:
        Dictionary containing operation result

    Error Handling:
        Returns error information if container not found or restart fails
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)

        container.restart(timeout=timeout)

        # Refresh container info
        container.reload()
        container_info = _parse_container_info(container)

        return ContainerResponse(
            status=DockerOperationStatus.SUCCESS,
            container=container_info
        )

    except NotFound:
        return ContainerResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Container '{container_id}' not found"
        )
    except Exception as e:
        return ContainerResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to restart container: {str(e)}"
        )


@_get_app().tool()
async def remove_container(
    container_id: str,
    force: bool = False,
    remove_volumes: bool = False
) -> dict:
    """Remove a Docker container.

    Removes a stopped container. Use force=True to remove running containers.

    Args:
        container_id: Container ID or name to remove
        force: Force removal even if running (default: False)
        remove_volumes: Remove associated volumes (default: False)

    Returns:
        Dictionary containing operation result

    Error Handling:
        Returns error information if container not found or removal fails
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)

        if container.status == 'running' and not force:
            return ContainerResponse(
                status=DockerOperationStatus.ERROR,
                error="Container is running. Use force=True to remove running containers"
            )

        container.remove(force=force, v=remove_volumes)

        return {
            "status": DockerOperationStatus.SUCCESS,
            "message": f"Container '{container_id}' removed successfully",
            "container_id": container_id,
            "force_used": force,
            "volumes_removed": remove_volumes
        }

    except NotFound:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Container '{container_id}' not found"
        }
    except Exception as e:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Failed to remove container: {str(e)}"
        }


@_get_app().tool()
async def container_exec(
    container_id: str,
    command: Union[str, List[str]],
    detach: bool = False,
    tty: bool = False,
    stdin: bool = False,
    stdout: bool = True,
    stderr: bool = True,
    stream: bool = False,
    socket: bool = False,
    environment: Optional[Dict[str, str]] = None,
    working_dir: Optional[str] = None,
    user: Optional[str] = None
) -> dict:
    """Execute a command inside a running Docker container.

    Runs arbitrary commands inside a container with full control over
    execution parameters and output handling.

    Args:
        container_id: Container ID or name
        command: Command to execute (string or list)
        detach: Run command in background
        tty: Allocate pseudo-TTY
        stdin: Keep STDIN open
        stdout: Return STDOUT
        stderr: Return STDERR
        stream: Stream output (not supported in MCP context)
        socket: Return socket instead of streams
        environment: Environment variables for command
        working_dir: Working directory for command
        user: User to run command as

    Returns:
        Dictionary containing execution result and output

    Error Handling:
        Returns error information if container not found or execution fails
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)

        if container.status != 'running':
            return {
                "status": DockerOperationStatus.ERROR,
                "error": f"Container '{container_id}' is not running (status: {container.status})"
            }

        # Prepare execution configuration
        exec_config = {
            'cmd': command if isinstance(command, list) else command.split(),
            'detach': detach,
            'tty': tty,
            'stdin': stdin,
            'stdout': stdout,
            'stderr': stderr,
            'stream': stream,
            'socket': socket,
        }

        if environment:
            exec_config['environment'] = environment
        if working_dir:
            exec_config['working_dir'] = working_dir
        if user:
            exec_config['user'] = user

        # Execute the command
        exec_result = container.exec_run(**exec_config)

        return {
            "status": DockerOperationStatus.SUCCESS,
            "container_id": container_id,
            "command": command,
            "exit_code": exec_result.exit_code,
            "output": exec_result.output.decode('utf-8', errors='replace') if exec_result.output else None,
            "success": exec_result.exit_code == 0
        }

    except NotFound:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Container '{container_id}' not found"
        }
    except Exception as e:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Failed to execute command in container: {str(e)}"
        }


@_get_app().tool()
async def container_logs(
    container_id: str,
    tail: int = 100,
    since: Optional[str] = None,
    until: Optional[str] = None,
    timestamps: bool = False,
    follow: bool = False
) -> dict:
    """Get logs from a Docker container.

    Retrieves container logs with filtering and formatting options.

    Args:
        container_id: Container ID or name
        tail: Number of lines to show from end (default: 100)
        since: Show logs since timestamp (RFC3339 format)
        until: Show logs until timestamp (RFC3339 format)
        timestamps: Include timestamps in output
        follow: Follow log output (stream mode)

    Returns:
        Dictionary containing log output and metadata

    Error Handling:
        Returns error information if container not found or logs unavailable
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)

        # Prepare log options
        log_options = {
            'tail': tail,
            'timestamps': timestamps,
            'follow': follow
        }

        if since:
            log_options['since'] = since
        if until:
            log_options['until'] = until

        # Get logs
        logs = container.logs(**log_options)

        # Decode logs
        if isinstance(logs, bytes):
            log_output = logs.decode('utf-8', errors='replace')
        else:
            log_output = str(logs)

        return {
            "status": DockerOperationStatus.SUCCESS,
            "container_id": container_id,
            "logs": log_output,
            "tail": tail,
            "timestamps": timestamps,
            "follow": follow,
            "since": since,
            "until": until
        }

    except NotFound:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Container '{container_id}' not found"
        }
    except Exception as e:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Failed to get container logs: {str(e)}"
        }


@_get_app().tool()
async def container_stats(container_id: str) -> dict:
    """Get real-time resource usage statistics for a container.

    Retrieves CPU, memory, network, and disk usage statistics.

    Args:
        container_id: Container ID or name

    Returns:
        Dictionary containing resource statistics and metadata

    Error Handling:
        Returns error information if container not found or stats unavailable
    """
    try:
        client = get_docker_client()
        container = client.containers.get(container_id)

        if container.status != 'running':
            return {
                "status": DockerOperationStatus.ERROR,
                "error": f"Container '{container_id}' is not running (status: {container.status})"
            }

        # Get statistics
        stats = container.stats(stream=False)

        # Parse key metrics
        cpu_usage = None
        memory_usage = None

        if 'cpu_stats' in stats and 'precpu_stats' in stats:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']

            if system_delta > 0:
                cpu_usage = (cpu_delta / system_delta) * 100.0

        if 'memory_stats' in stats:
            memory_usage = stats['memory_stats'].get('usage')

        network_stats = stats.get('networks', {})

        return {
            "status": DockerOperationStatus.SUCCESS,
            "container_id": container_id,
            "cpu_usage_percent": cpu_usage,
            "memory_usage_bytes": memory_usage,
            "memory_limit_bytes": stats.get('memory_stats', {}).get('limit'),
            "network_stats": network_stats,
            "timestamp": datetime.now().isoformat()
        }

    except NotFound:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Container '{container_id}' not found"
        }
    except Exception as e:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Failed to get container stats: {str(e)}"
        }


def _parse_container_info(container, show_stats: bool = False) -> ContainerInfo:
    """
    Parse Docker container object into a structured ContainerInfo object.

    Args:
        container: Docker container object
        show_stats: Whether to include real-time statistics

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
    config_env = container.attrs.get('Config', {}).get('Env', [])
    for env_var in config_env:
        if '=' in env_var:
            key, value = env_var.split('=', 1)
            env_vars[key] = value

    # Get basic stats if requested
    cpu_usage = None
    memory_usage = None
    if show_stats and container.status == 'running':
        try:
            stats = container.stats(stream=False)
            if 'cpu_stats' in stats and 'precpu_stats' in stats:
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                if system_delta > 0:
                    cpu_usage = (cpu_delta / system_delta) * 100.0

            if 'memory_stats' in stats:
                memory_usage = stats['memory_stats'].get('usage')
        except Exception:
            pass  # Stats are optional

    return ContainerInfo(
        id=container.id,
        name=container.name,
        image=container.image.tags[0] if container.image.tags else container.image.id,
        status=container.status,
        state=container.attrs.get('State', {}).get('Status', 'unknown'),
        created=datetime.fromisoformat(container.attrs['Created'].replace('Z', '+00:00')),
        ports=ports,
        mounts=mounts,
        command=' '.join(container.attrs.get('Config', {}).get('Cmd', [])),
        entrypoint=container.attrs.get('Config', {}).get('Entrypoint'),
        working_dir=container.attrs.get('Config', {}).get('WorkingDir'),
        environment=container.attrs.get('Config', {}).get('Env', {}),
        labels=container.labels or {},
        network_mode=container.attrs.get('HostConfig', {}).get('NetworkMode', 'default'),
        restart_policy=container.attrs.get('HostConfig', {}).get('RestartPolicy', {}).get('Name', 'no'),
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        network_settings=container.attrs.get('NetworkSettings', {}),
        host_config=container.attrs.get('HostConfig', {}),
        env_vars=env_vars
    )
