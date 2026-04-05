"""Docker Compose tools — one tool per compose subcommand."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .utils import _error_response, _get_app, _success_response

logger = logging.getLogger(__name__)

async def _run_compose_command(
    path: str, command_args: list[str], timeout: int = 300
) -> dict[str, Any]:
    """Execute docker compose with recovery hints on failure."""
    try:
        cmd = ["docker", "compose"]
        if path.endswith((".yml", ".yaml")):
            cmd.extend(["-f", path])
        else:
            cmd.extend(["--project-directory", path])

        cmd.extend(command_args)

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except TimeoutError:
            process.kill()
            return _error_response(
                f"Command timed out after {timeout}s: {' '.join(cmd)}",
                "timeout_error",
                recovery_options=[
                    "Inspect stack health (compose_ps); reduce workload or increase timeout.",
                    "Check for interactive prompts blocking the daemon.",
                ],
            )

        output = stdout.decode().strip()
        error_output = stderr.decode().strip()

        if process.returncode != 0:
            return _error_response(
                f"Docker Compose failed: {error_output}",
                "compose_error",
                recovery_options=[
                    "Read stderr in error and diagnostic_info.stdout; fix compose file or service state.",
                    "Run compose_config to validate YAML; ensure docker daemon is running.",
                    "Intermittent failures (network pulls): often retryable after fixing registry/auth.",
                ],
                diagnostic_info={"stdout": output, "exit_code": process.returncode},
            )

        return _success_response(
            {"output": output, "stderr": error_output},
            operation="compose",
        )
    except Exception as e:
        logger.exception("compose command failed")
        return _error_response(str(e), "internal_error")


_app = _get_app()


@_app.tool()
async def compose_up(
    path: str = ".",
    services: list[str] | None = None,
    detach: bool = True,
    build: bool = False,
    scale: dict[str, int] | None = None,
    timeout: int = 300,
) -> dict[str, Any]:
    """Start Compose services (docker compose up).

    Recovery: If build fails, fix Dockerfile/context; if ports conflict, edit compose or stop conflicting services.

    Idempotency: Re-running up is generally safe; may recreate containers per compose semantics.

    Returns:
        dict: on success, result contains output and stderr strings; on failure, error and recovery_options.
        result.output: command stdout; result.stderr: stderr text.
    """
    cmd_args: list[str] = ["up"]
    if detach:
        cmd_args.append("-d")
    if build:
        cmd_args.append("--build")
    if scale:
        for svc, count in scale.items():
            cmd_args.extend(["--scale", f"{svc}={count}"])
    if services:
        cmd_args.extend(services)
    return await _run_compose_command(path, cmd_args, timeout)


@_app.tool()
async def compose_down(
    path: str = ".",
    remove_orphans: bool = True,
    volumes_prune: bool = False,
    timeout: int = 300,
) -> dict[str, Any]:
    """Stop and remove Compose containers (docker compose down).

    Args:
        volumes_prune: If True, removes anonymous volumes declared in the compose file (data loss risk).

    Recovery: If down fails (e.g. bind mounts in use), stop consumers or use docker CLI for force removal.

    Returns:
        dict: on success, result contains output and stderr strings; on failure, error and recovery_options.
    """
    cmd_args = ["down"]
    if remove_orphans:
        cmd_args.append("--remove-orphans")
    if volumes_prune:
        cmd_args.append("--volumes")
    return await _run_compose_command(path, cmd_args, timeout)


@_app.tool()
async def compose_ps(
    path: str = ".",
    services: list[str] | None = None,
    all_services: bool = False,
    timeout: int = 120,
) -> dict[str, Any]:
    """List compose services as JSON (docker compose ps --format json).

    Returns:
        dict: on success, result contains output and stderr strings; on failure, error and recovery_options.
        result.output: JSON string from docker compose.
    """
    cmd_args = ["ps"]
    if all_services:
        cmd_args.append("--all")
    cmd_args.extend(["--format", "json"])
    if services:
        cmd_args.extend(services)
    return await _run_compose_command(path, cmd_args, timeout)


@_app.tool()
async def compose_logs(
    path: str = ".",
    services: list[str] | None = None,
    tail: int | None = 100,
    since: str | None = None,
    until: str | None = None,
    timestamps: bool = False,
    follow: bool = False,
    timeout: int = 300,
) -> dict[str, Any]:
    """Fetch service logs (docker compose logs).

    Recovery: If logs empty, verify service names with compose_ps.

    Returns:
        dict: on success, result contains output and stderr strings; on failure, error and recovery_options.
    """
    cmd_args = ["logs"]
    if follow:
        cmd_args.append("-f")
    if tail is not None:
        cmd_args.extend(["--tail", str(tail)])
    if since:
        cmd_args.extend(["--since", since])
    if until:
        cmd_args.extend(["--until", until])
    if timestamps:
        cmd_args.append("-t")
    if services:
        cmd_args.extend(services)
    return await _run_compose_command(path, cmd_args, timeout)


@_app.tool()
async def compose_config(
    path: str = ".",
    validate: bool = True,
    timeout: int = 120,
) -> dict[str, Any]:
    """Render and validate compose configuration (docker compose config).

    Args:
        validate: When True (default), interpolated config is validated.

    Returns:
        dict: on success, result contains output and stderr strings; on failure, error and recovery_options.
        result.output: rendered YAML.
    """
    cmd_args = ["config"]
    if not validate:
        cmd_args.append("--no-interpolate")
    return await _run_compose_command(path, cmd_args, timeout)


@_app.tool()
async def compose_restart(
    path: str = ".",
    services: list[str] | None = None,
    timeout: int = 300,
) -> dict[str, Any]:
    """Restart compose services (docker compose restart).

    Returns:
        dict: on success, result contains output and stderr strings; on failure, error and recovery_options.
    """
    cmd_args = ["restart"]
    if services:
        cmd_args.extend(services)
    return await _run_compose_command(path, cmd_args, timeout)
