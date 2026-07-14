import logging
from typing import Any, Literal

from .utils import (
    MUTATING,
    _clarification_response,
    _error_response,
    _get_app,
    _get_docker_client,
    _success_response,
)

logger = logging.getLogger(__name__)


@_get_app().tool(annotations=MUTATING, version="2.2.0")
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
    container_id: str | None = None,
    image: str | None = None,
    name: str | None = None,
    command: str | list[str] | None = None,
    ports: dict[str, int | str] | None = None,
    volumes: dict[str, dict[str, str]] | None = None,
    environment: dict[str, str] | None = None,
    working_dir: str | None = None,
    user: str | None = None,
    detach: bool = True,
    auto_remove: bool = False,
    network_mode: str | None = None,
    restart_policy: str | None = None,
    timeout: int = 10,
    force: bool = False,
    tty: bool = False,
    stdin: bool = False,
    stdout: bool = True,
    stderr: bool = True,
    stream: bool = False,
    socket: bool = False,
    tail: int | None = 100,
    since: str | None = None,
    until: str | None = None,
    timestamps: bool = False,
    follow: bool = False,
    show_stats: bool = False,
) -> dict[str, Any]:
    """Docker Container Lifecycle operations.

    Operations: list_containers, get_container, create_container, start_container,
    stop_container, restart_container, remove_container, container_exec, container_logs,
    container_stats.

    Args:
        operation: Operation to perform (required)
        container_id: Target container ID or name
        image: Image for create_container
        name: Container name
        command: Command for container_exec
        ports: Port mappings dict
        volumes: Volume mounts dict
        environment: Env variables dict
        working_dir: Work dir in container
        detach: Run in background. Default: True
        auto_remove: Remove when stopped. Default: False
        timeout: Stop/restart timeout secs. Default: 10
        force: Force removal. Default: False
        tail: Log lines. Default: 100
        since/until: Log time range strings
        timestamps: Include timestamps in logs. Default: False
        show_stats: Include stats in listing. Default: False
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
            return _clarification_response("container_id", f"container_id is required for {operation}")

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
    filters: dict[str, list[str]] | None = None,
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
                    logger.warning("Failed to get container stats", exc_info=True)

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
                    "activity": "high" if running_count > 10 else "medium" if running_count > 0 else "low",
                },
            },
            next_steps=["container_ops(operation='get_container', container_id='<id>')"],
            related_operations=["infra_ops(operation='list_images')"],
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
                logger.warning("Failed to get container stats", exc_info=True)

        return _success_response({"container": info})
    except Exception as e:
        return _error_response(str(e), "docker_error")


async def _create_container(
    image: str,
    command: str | list[str] | None = None,
    name: str | None = None,
    ports: dict[str, int | str] | None = None,
    volumes: dict[str, dict[str, str]] | None = None,
    environment: dict[str, str] | None = None,
    working_dir: str | None = None,
    detach: bool = True,
    auto_remove: bool = False,
    network_mode: str | None = None,
    restart_policy: str | None = None,
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
        return _success_response({"container_id": container.id, "container_name": container.name, "status": "created"})
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
    command: str | list[str],
    detach: bool = False,
    tty: bool = False,
    stdin: bool = False,
    stdout: bool = True,
    stderr: bool = True,
    stream: bool = False,
    socket: bool = False,
    environment: dict[str, str] | None = None,
    working_dir: str | None = None,
    user: str | None = None,
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
    tail: int | None = 100,
    since: str | None = None,
    until: str | None = None,
    timestamps: bool = False,
    follow: bool = False,
) -> dict[str, Any]:
    try:
        client = _get_docker_client()
        container = client.containers.get(container_id)
        logs = container.logs(tail=tail, since=since, until=until, timestamps=timestamps, follow=follow, stream=False)
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
        return _success_response({"container_id": container_id, "stats": _parse_container_stats(stats)})
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
                "percentage": round(memory_stats.get("usage", 0) / max(memory_stats.get("limit", 1), 1) * 100, 2),
            },
            "cpu": {
                "usage": cpu_stats.get("cpu_usage", {}).get("total_usage", 0),
                "system_cpu_usage": cpu_stats.get("system_cpu_usage", 0),
            },
            "networks": networks,
        }
    except Exception:
        return {"error": "Failed to parse stats"}
