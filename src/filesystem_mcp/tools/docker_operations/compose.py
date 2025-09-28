"""
Docker Compose operations for the Filesystem MCP.

This module provides Docker Compose lifecycle management including
deployment, scaling, monitoring, and cleanup operations.
"""

import logging
import subprocess
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict

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


# Pydantic models for compose operations
class DockerOperationStatus(str, Enum):
    """Status enumeration for Docker operations."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class ComposeServiceInfo(BaseModel):
    """Information about a Docker Compose service."""
    name: str
    image: str
    command: Optional[str] = None
    ports: List[str] = Field(default_factory=list)
    volumes: List[str] = Field(default_factory=list)
    environment: Dict[str, str] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    restart: Optional[str] = None
    networks: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ComposeProjectInfo(BaseModel):
    """Information about a Docker Compose project."""
    name: str
    working_dir: str
    config_files: List[str] = Field(default_factory=list)
    services: Dict[str, ComposeServiceInfo] = Field(default_factory=dict)
    networks: Dict[str, Any] = Field(default_factory=dict)
    volumes: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class ComposeResponse(BaseModel):
    """Response model for compose operations."""
    status: DockerOperationStatus
    project: Optional[ComposeProjectInfo] = None
    output: str = ""
    error: Optional[str] = None
    exit_code: int = 0

    model_config = ConfigDict(from_attributes=True)


def _run_compose_command(
    command: List[str],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: int = 300
) -> tuple[int, str, str]:
    """
    Run a docker-compose command and return the results.

    Args:
        command: Command arguments (without 'docker compose')
        cwd: Working directory for the command
        env: Environment variables
        timeout: Command timeout in seconds

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    try:
        # Build the full command
        full_command = ['docker', 'compose'] + command

        logger.info(f"Running: {' '.join(full_command)} in {cwd or '.'}")

        # Run the command
        result = subprocess.run(
            full_command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return result.returncode, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return -1, "", "docker command not found"
    except Exception as e:
        return -1, "", f"Command execution failed: {str(e)}"


def _parse_compose_config(compose_file: str, cwd: str) -> Optional[ComposeProjectInfo]:
    """
    Parse docker-compose configuration.

    Args:
        compose_file: Path to compose file
        cwd: Working directory

    Returns:
        ComposeProjectInfo if parsing successful, None otherwise
    """
    try:
        import yaml

        compose_path = Path(cwd) / compose_file
        if not compose_path.exists():
            return None

        with open(compose_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if not config:
            return None

        services = {}
        if 'services' in config:
            for service_name, service_config in config['services'].items():
                # Parse service information
                service_info = ComposeServiceInfo(
                    name=service_name,
                    image=service_config.get('image', ''),
                    command=service_config.get('command'),
                    ports=service_config.get('ports', []),
                    volumes=service_config.get('volumes', []),
                    environment=service_config.get('environment', {}),
                    depends_on=service_config.get('depends_on', []),
                    restart=service_config.get('restart'),
                    networks=service_config.get('networks', [])
                )
                services[service_name] = service_info

        return ComposeProjectInfo(
            name=config.get('name', Path(cwd).name),
            working_dir=cwd,
            config_files=[compose_file],
            services=services,
            networks=config.get('networks', {}),
            volumes=config.get('volumes', {})
        )

    except Exception as e:
        logger.warning(f"Failed to parse compose config {compose_file}: {e}")
        return None


@_get_app().tool()
async def compose_up(
    path: str = ".",
    services: Optional[List[str]] = None,
    detach: bool = True,
    build: bool = False,
    scale: Optional[Dict[str, int]] = None,
    timeout: int = 300
) -> dict:
    """Start Docker Compose services.

    Starts services defined in docker-compose.yml with optional scaling and building.

    Args:
        path: Path to directory containing docker-compose.yml
        services: List of specific services to start (default: all)
        detach: Run in detached mode (background)
        build: Build images before starting
        scale: Scale services (e.g., {"web": 3, "worker": 2})
        timeout: Command timeout in seconds

    Returns:
        Dictionary containing operation result and output

    Error Handling:
        Returns error information if compose file not found or startup fails
    """
    try:
        from pathlib import Path

        compose_path = Path(path).resolve()
        if not compose_path.exists():
            return ComposeResponse(
                status=DockerOperationStatus.ERROR,
                error=f"Path '{path}' not found"
            )

        # Check for compose file
        compose_files = ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']
        compose_file = None
        for cf in compose_files:
            if (compose_path / cf).exists():
                compose_file = cf
                break

        if not compose_file:
            return ComposeResponse(
                status=DockerOperationStatus.ERROR,
                error="No docker-compose file found (docker-compose.yml, docker-compose.yaml, compose.yml, or compose.yaml)"
            )

        # Build command
        command = ['up']
        if detach:
            command.append('-d')
        if build:
            command.append('--build')
        if scale:
            for service, count in scale.items():
                command.extend(['--scale', f"{service}={count}"])
        if services:
            command.extend(services)

        # Run command
        exit_code, stdout, stderr = _run_compose_command(
            command,
            cwd=str(compose_path),
            timeout=timeout
        )

        # Parse project info if successful
        project = None
        if exit_code == 0:
            project = _parse_compose_config(compose_file, str(compose_path))

        return ComposeResponse(
            status=DockerOperationStatus.SUCCESS if exit_code == 0 else DockerOperationStatus.ERROR,
            project=project,
            output=stdout + stderr,
            exit_code=exit_code,
            error=stderr if exit_code != 0 else None
        )

    except Exception as e:
        return ComposeResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to start compose services: {str(e)}"
        )


@_get_app().tool()
async def compose_down(
    path: str = ".",
    remove_orphans: bool = True,
    volumes: bool = False,
    timeout: int = 300
) -> dict:
    """Stop and remove Docker Compose services.

    Stops services and removes containers, networks, and optionally volumes.

    Args:
        path: Path to directory containing docker-compose.yml
        remove_orphans: Remove containers for services not in compose file
        volumes: Remove named volumes declared in the volumes section
        timeout: Command timeout in seconds

    Returns:
        Dictionary containing operation result and output

    Error Handling:
        Returns error information if compose file not found or shutdown fails
    """
    try:
        from pathlib import Path

        compose_path = Path(path).resolve()
        if not compose_path.exists():
            return ComposeResponse(
                status=DockerOperationStatus.ERROR,
                error=f"Path '{path}' not found"
            )

        # Build command
        command = ['down']
        if remove_orphans:
            command.append('--remove-orphans')
        if volumes:
            command.append('--volumes')

        # Run command
        exit_code, stdout, stderr = _run_compose_command(
            command,
            cwd=str(compose_path),
            timeout=timeout
        )

        return ComposeResponse(
            status=DockerOperationStatus.SUCCESS if exit_code == 0 else DockerOperationStatus.ERROR,
            output=stdout + stderr,
            exit_code=exit_code,
            error=stderr if exit_code != 0 else None
        )

    except Exception as e:
        return ComposeResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to stop compose services: {str(e)}"
        )


@_get_app().tool()
async def compose_ps(
    path: str = ".",
    services: Optional[List[str]] = None,
    all_services: bool = False,
    timeout: int = 60
) -> dict:
    """List Docker Compose services and their status.

    Shows the status of services defined in docker-compose.yml.

    Args:
        path: Path to directory containing docker-compose.yml
        services: List of specific services to show (default: all)
        all_services: Show all services including stopped ones
        timeout: Command timeout in seconds

    Returns:
        Dictionary containing service status information

    Error Handling:
        Returns error information if compose file not found or command fails
    """
    try:
        from pathlib import Path

        compose_path = Path(path).resolve()
        if not compose_path.exists():
            return ComposeResponse(
                status=DockerOperationStatus.ERROR,
                error=f"Path '{path}' not found"
            )

        # Build command
        command = ['ps']
        if all_services:
            command.append('--all')
        if services:
            command.extend(services)

        # Run command
        exit_code, stdout, stderr = _run_compose_command(
            command,
            cwd=str(compose_path),
            timeout=timeout
        )

        # Parse the output to extract service information
        services_info = {}
        if exit_code == 0 and stdout:
            lines = stdout.strip().split('\n')
            if len(lines) > 1:  # Skip header
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            service_name = parts[0]
                            status = ' '.join(parts[1:-2])
                            ports = parts[-2] if len(parts) > 4 else ''
                            services_info[service_name] = {
                                'status': status,
                                'ports': ports,
                                'command': parts[-1] if len(parts) > 4 else ''
                            }

        return {
            "status": DockerOperationStatus.SUCCESS if exit_code == 0 else DockerOperationStatus.ERROR,
            "services": services_info,
            "output": stdout + stderr,
            "exit_code": exit_code,
            "error": stderr if exit_code != 0 else None
        }

    except Exception as e:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Failed to list compose services: {str(e)}"
        }


@_get_app().tool()
async def compose_logs(
    path: str = ".",
    services: Optional[List[str]] = None,
    follow: bool = False,
    tail: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    timestamps: bool = False,
    timeout: int = 60
) -> dict:
    """View Docker Compose service logs.

    Retrieves logs from services defined in docker-compose.yml with filtering options.

    Args:
        path: Path to directory containing docker-compose.yml
        services: List of specific services to show logs for
        follow: Follow log output (stream mode)
        tail: Number of lines to show from end
        since: Show logs since timestamp
        until: Show logs until timestamp
        timestamps: Include timestamps in output
        timeout: Command timeout in seconds

    Returns:
        Dictionary containing log output and metadata

    Error Handling:
        Returns error information if compose file not found or logs unavailable
    """
    try:
        from pathlib import Path

        compose_path = Path(path).resolve()
        if not compose_path.exists():
            return {
                "status": DockerOperationStatus.ERROR,
                "error": f"Path '{path}' not found"
            }

        # Build command
        command = ['logs']
        if follow:
            command.append('--follow')
        if tail:
            command.extend(['--tail', str(tail)])
        if since:
            command.extend(['--since', since])
        if until:
            command.extend(['--until', until])
        if timestamps:
            command.append('--timestamps')
        if services:
            command.extend(services)

        # Run command
        exit_code, stdout, stderr = _run_compose_command(
            command,
            cwd=str(compose_path),
            timeout=timeout
        )

        return {
            "status": DockerOperationStatus.SUCCESS if exit_code == 0 else DockerOperationStatus.ERROR,
            "logs": stdout,
            "error": stderr if exit_code != 0 else None,
            "exit_code": exit_code,
            "follow": follow,
            "tail": tail,
            "since": since,
            "until": until,
            "timestamps": timestamps,
            "services": services
        }

    except Exception as e:
        return {
            "status": DockerOperationStatus.ERROR,
            "error": f"Failed to get compose logs: {str(e)}"
        }


@_get_app().tool()
async def compose_config(
    path: str = ".",
    validate: bool = True,
    timeout: int = 60
) -> dict:
    """Validate and view Docker Compose configuration.

    Parses and validates docker-compose.yml files, showing the resolved configuration.

    Args:
        path: Path to directory containing docker-compose.yml
        validate: Validate configuration syntax and references
        timeout: Command timeout in seconds

    Returns:
        Dictionary containing configuration information

    Error Handling:
        Returns error information if compose file not found or invalid
    """
    try:
        from pathlib import Path

        compose_path = Path(path).resolve()
        if not compose_path.exists():
            return ComposeResponse(
                status=DockerOperationStatus.ERROR,
                error=f"Path '{path}' not found"
            )

        # Build command
        command = ['config']
        if validate:
            command.append('--validate')

        # Run command
        exit_code, stdout, stderr = _run_compose_command(
            command,
            cwd=str(compose_path),
            timeout=timeout
        )

        # Try to parse the configuration
        project = None
        if exit_code == 0:
            # Find compose file
            compose_files = ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']
            compose_file = None
            for cf in compose_files:
                if (compose_path / cf).exists():
                    compose_file = cf
                    break

            if compose_file:
                project = _parse_compose_config(compose_file, str(compose_path))

        return ComposeResponse(
            status=DockerOperationStatus.SUCCESS if exit_code == 0 else DockerOperationStatus.ERROR,
            project=project,
            output=stdout,
            error=stderr if exit_code != 0 else None,
            exit_code=exit_code
        )

    except Exception as e:
        return ComposeResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to get compose config: {str(e)}"
        )


@_get_app().tool()
async def compose_restart(
    path: str = ".",
    services: Optional[List[str]] = None,
    timeout: int = 300
) -> dict:
    """Restart Docker Compose services.

    Restarts services defined in docker-compose.yml.

    Args:
        path: Path to directory containing docker-compose.yml
        services: List of specific services to restart (default: all)
        timeout: Command timeout in seconds

    Returns:
        Dictionary containing operation result

    Error Handling:
        Returns error information if compose file not found or restart fails
    """
    try:
        from pathlib import Path

        compose_path = Path(path).resolve()
        if not compose_path.exists():
            return ComposeResponse(
                status=DockerOperationStatus.ERROR,
                error=f"Path '{path}' not found"
            )

        # Build command
        command = ['restart']
        if services:
            command.extend(services)

        # Run command
        exit_code, stdout, stderr = _run_compose_command(
            command,
            cwd=str(compose_path),
            timeout=timeout
        )

        return ComposeResponse(
            status=DockerOperationStatus.SUCCESS if exit_code == 0 else DockerOperationStatus.ERROR,
            output=stdout + stderr,
            exit_code=exit_code,
            error=stderr if exit_code != 0 else None
        )

    except Exception as e:
        return ComposeResponse(
            status=DockerOperationStatus.ERROR,
            error=f"Failed to restart compose services: {str(e)}"
        )
