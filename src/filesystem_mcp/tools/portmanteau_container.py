import logging
from typing import Any, Literal, Optional, Union

from .utils import (
    _clarification_response,
    _error_response,
    _get_app,
    _get_docker_client,
    _success_response,
)

logger = logging.getLogger(__name__)


@_get_app().tool()
async def container_ops(
    operation: Literal[
        "list_containers",
        "get_container",
        "create_container",
        "start_container",
        "stop_container",
        "restart_container",
        "remove_container",
        "container_exec",
        "container_logs",
        "container_stats",
    ],
    container_id: Optional[str] = None,
    image: Optional[str] = None,
    name: Optional[str] = None,
    command: Optional[Union[str, list[str]]] = None,
    ports: Optional[dict[str, Union[int, str]]] = None,
    volumes: Optional[dict[str, dict[str, str]]] = None,
    environment: Optional[dict[str, str]] = None,
    working_dir: Optional[str] = None,
    user: Optional[str] = None,
    detach: bool = True,
    auto_remove: bool = False,
    network_mode: Optional[str] = None,
    restart_policy: Optional[str] = None,
    timeout: int = 10,
    force: bool = False,
    tty: bool = False,
    stdin: bool = False,
    stdout: bool = True,
    stderr: bool = True,
    stream: bool = False,
    socket: bool = False,
    tail: Optional[int] = 100,
    since: Optional[str] = None,
    until: Optional[str] = None,
    timestamps: bool = False,
    follow: bool = False,
    show_stats: bool = False,
) -> dict[str, Any]:
    """Docker Container Lifecycle operations.

    Args:
        operation (Literal, required): Available container operations:
            - "list_containers": List Docker containers with filtering
            - "get_container": Get detailed info (requires: container_id)
            - "create_container": Create new container (requires: image)
            - "start_container": Start stopped container (requires: container_id)
            - "stop_container": Stop running container (requires: container_id)
            - "restart_container": Restart container (requires: container_id)
            - "remove_container": Remove container (requires: container_id)
            - "container_exec": Run command in container (requires: container_id, command)
            - "container_logs": Stream logs (requires: container_id)
            - "container_stats": Resource statistics (requires: container_id)

        --- CORE IDENTIFIERS ---

        container_id (str | None): Target container ID or name
        image (str | None): Image for creation
        name (str | None): Container name

        --- CONTAINER CONFIGURATION ---

        command (str | List[str] | None): Command to run
        ports (Dict | None): Port mappings
        volumes (Dict | None): Volume mounts
        environment (Dict | None): Env variables
        working_dir (str | None): Work dir in container
        user (str | None): Run as user
        detach (bool): Run in background. Default: True
        auto_remove (bool): Remove when stopped. Default: False
        network_mode (str | None): Network mode
        restart_policy (str | None): Restart policy

        --- RUNTIME & LOGGING ---

        timeout (int): Stop/restart timeout. Default: 10
        force (bool): Force removal. Default: False
        tty/stdin/stdout/stderr (bool): Exec options
        tail (int | None): Log lines. Default: 100
        since/until (str | None): Log time range
        timestamps (bool): Include timestamps in logs. Default: False
        follow (bool): Follow log stream. Default: False
        show_stats (bool): Include stats in listing. Default: False
    """
    try:
        if not operation:
            return _clarification_response(
                "operation", "No operation specified", ["list_containers", "create_container"]
            )

        if (
            operation
            in [
                "get_container",
                "start_container",
                "stop_container",
                "restart_container",
                "remove_container",
                "container_logs",
                "container_stats",
            ]
            and not container_id
        ):
            return _clarification_response(
                "container_id", f"container_id is required for {operation}"
            )

        if operation == "list_containers":
            return await _list_containers(all_containers=True, show_stats=show_stats)
        elif operation == "get_container":
            return await _get_container(container_id, show_stats)
        elif operation == "create_container":
            if not image:
                return _clarification_response("image", "image is required for create_container")
            return await _create_container(
                image,
                command,
                name,
                ports,
                volumes,
                environment,
                working_dir,
                detach,
                auto_remove,
                network_mode,
                restart_policy,
            )
        elif operation == "start_container":
            return await _start_container(container_id)
        elif operation == "stop_container":
            return await _stop_container(container_id, timeout)
        elif operation == "restart_container":
            return await _restart_container(container_id, timeout)
        elif operation == "remove_container":
            return await _remove_container(container_id, force)
        elif operation == "container_exec":
            if not command:
                return _clarification_response("command", "command is required for container_exec")
            return await _container_exec(
                container_id,
                command,
                detach,
                tty,
                stdin,
                stdout,
                stderr,
                stream,
                socket,
                environment,
                working_dir,
                user,
            )
        elif operation == "container_logs":
            return await _container_logs(container_id, tail, since, until, timestamps, follow)
        elif operation == "container_stats":
            return await _container_stats(container_id)
        else:
            return _error_response(f"Unknown operation: {operation}", "unsupported_operation")
    except Exception as e:
        logger.error(f"Container operation '{operation}' failed: {e}", exc_info=True)
        return _error_response(str(e), "internal_error")


async def _list_containers(
    all_containers: bool = False,
    filters: Optional[dict[str, list[str]]] = None,
    show_stats: bool = False,
) -> dict[str, Any]:
    """List containers with FULL metadata and status analysis."""
    try:
        client = _get_docker_client()
        containers = client.containers.list(all=all_containers, filters=filters)

        container_list = []
        for container in containers:
            info = {
                "id": container.id,
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else container.image.id,
                "status": container.status,
                "created": container.attrs.get("Created"),
                "ports": container.ports,
            }

            if show_stats:
                try:
                    stats = container.stats(stream=False)
                    info["stats"] = _parse_container_stats(stats)
                except Exception:
                    pass

            container_list.append(info)

        # Analysis logic
        running_count = sum(1 for c in container_list if c.get("status", "").startswith("running"))
        stopped_count = len(container_list) - running_count

        recommendations = []
        if len(container_list) == 0:
            recommendations.append(
                "No containers found - consider creating containers or checking Docker daemon status"
            )
        elif len(container_list) > 20:
            recommendations.append("Many containers detected - consider using filters")

        return _success_response(
            {
                "containers": container_list,
                "total": len(container_list),
                "running": running_count,
                "stopped": stopped_count,
                "recommendations": recommendations,
                "summary": {
                    "health_status": "healthy" if running_count >= stopped_count else "attention_needed",
                    "activity": "high" if running_count > 10 else "medium" if running_count > 0 else "low"
                }
            },
            next_steps=["container_ops(operation='get_container', container_id='<id>')"],
            related_ops=["infra_ops(operation='list_images')"],
        )
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _get_container(container_id: str, show_stats: bool = False) -> dict[str, Any]:
    """Get FULL container details."""
    try:
        client = _get_docker_client()
        container = client.containers.get(container_id)

        info = {
            "id": container.id,
            "name": container.name,
            "image": container.image.tags[0] if container.image.tags else container.image.id,
            "status": container.status,
            "created": container.attrs.get("Created"),
            "config": container.attrs.get("Config", {}),
            "network_settings": container.attrs.get("NetworkSettings", {}),
            "mounts": container.attrs.get("Mounts", []),
        }

        if show_stats:
            try:
                stats = container.stats(stream=False)
                info["stats"] = _parse_container_stats(stats)
            except Exception:
                pass

        return _success_response({"container": info})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _create_container(
    image: str,
    command: Optional[Union[str, list[str]]] = None,
    name: Optional[str] = None,
    ports: Optional[dict[str, Union[int, str]]] = None,
    volumes: Optional[dict[str, dict[str, str]]] = None,
    environment: Optional[dict[str, str]] = None,
    working_dir: Optional[str] = None,
    detach: bool = True,
    auto_remove: bool = False,
    network_mode: Optional[str] = None,
    restart_policy: Optional[str] = None,
) -> dict[str, Any]:
    """Create container with FULL configuration options."""
    try:
        client = _get_docker_client()
        config = {"image": image, "detach": detach, "auto_remove": auto_remove}

        if command:
            config["command"] = command if isinstance(command, list) else command.split()
        if name:
            config["name"] = name
        if ports:
            config["ports"] = ports
        if volumes:
            config["volumes"] = volumes
        if environment:
            config["environment"] = environment
        if working_dir:
            config["working_dir"] = working_dir
        if network_mode:
            config["network_mode"] = network_mode
        if restart_policy:
            config["restart_policy"] = {"Name": restart_policy}

        container = client.containers.create(**config)
        return _success_response(
            {"container_id": container.id, "container_name": container.name, "status": "created"}
        )
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _start_container(container_id: str) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        container = client.containers.get(container_id)
        container.start()
        return _success_response({"container_id": container_id, "status": "started"})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _stop_container(container_id: str, timeout: int = 10) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        container = client.containers.get(container_id)
        container.stop(timeout=timeout)
        return _success_response({"container_id": container_id, "status": "stopped"})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _restart_container(container_id: str, timeout: int = 10) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        container = client.containers.get(container_id)
        container.restart(timeout=timeout)
        return _success_response({"container_id": container_id, "status": "restarted"})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _remove_container(container_id: str, force: bool = False) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        container = client.containers.get(container_id)
        container.remove(force=force)
        return _success_response({"container_id": container_id, "status": "removed"})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _container_exec(
    container_id: str,
    command: Union[str, list[str]],
    detach: bool = False,
    tty: bool = False,
    stdin: bool = False,
    stdout: bool = True,
    stderr: bool = True,
    stream: bool = False,
    socket: bool = False,
    environment: Optional[dict[str, str]] = None,
    working_dir: Optional[str] = None,
    user: Optional[str] = None,
) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        container = client.containers.get(container_id)

        exec_config = {
            "cmd": command if isinstance(command, list) else command.split(),
            "detach": detach,
            "tty": tty,
            "stdin": stdin,
            "stdout": stdout,
            "stderr": stderr,
            "stream": stream,
            "socket": socket,
        }

        if environment:
            exec_config["environment"] = environment
        if working_dir:
            exec_config["working_dir"] = working_dir
        if user:
            exec_config["user"] = user

        result = container.exec_run(**exec_config)
        return _success_response(
            {
                "container_id": container_id,
                "exit_code": result.exit_code,
                "output": result.output.decode() if isinstance(result.output, bytes) else str(result.output),
            }
        )
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _container_logs(
    container_id: str,
    tail: Optional[int] = 100,
    since: Optional[str] = None,
    until: Optional[str] = None,
    timestamps: bool = False,
    follow: bool = False,
) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        container = client.containers.get(container_id)
        logs = container.logs(
            tail=tail, since=since, until=until, timestamps=timestamps, follow=follow, stream=False
        )
        return _success_response(
            {
                "container_id": container_id,
                "logs": logs.decode() if isinstance(logs, bytes) else str(logs),
                "tail": tail,
                "timestamps": timestamps,
            }
        )
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _container_stats(container_id: str) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        container = client.containers.get(container_id)
        stats = container.stats(stream=False)
        return _success_response(
            {"container_id": container_id, "stats": _parse_container_stats(stats)}
        )
    except Exception as e:
        return _error_response(str(e), "docker_error")


def _parse_container_stats(stats_data: dict[str, Any]) -> dict[str, Any]:
    """FULL Docker stats parsing logic."""
    try:
        memory_stats = stats_data.get("memory_stats", {})
        cpu_stats = stats_data.get("cpu_stats", {})
        networks = stats_data.get("networks", {})

        return {
            "memory": {
                "usage": memory_stats.get("usage", 0),
                "limit": memory_stats.get("limit", 0),
                "percentage": round(
                    memory_stats.get("usage", 0) / max(memory_stats.get("limit", 1), 1) * 100, 2
                ),
            },
            "cpu": {
                "usage": cpu_stats.get("cpu_usage", {}).get("total_usage", 0),
                "system_cpu_usage": cpu_stats.get("system_cpu_usage", 0),
            },
            "networks": networks,
        }
    except Exception:
        return {"error": "Failed to parse stats"}
