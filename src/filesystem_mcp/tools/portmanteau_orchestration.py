import asyncio
import logging
from typing import Any, Literal, Optional

from .utils import (
    _clarification_response,
    _error_response,
    _get_app,
    _success_response,
)

logger = logging.getLogger(__name__)


async def _run_compose_command(
    path: str, command_args: list[str], timeout: int = 300
) -> dict[str, Any]:
    """Execute a Docker Compose command using subprocess."""
    try:
        # Construct the base command
        # Use -f to specify the path if it's a file, or just let docker compose find it in the directory
        cmd = ["docker", "compose"]
        if path.endswith((".yml", ".yaml")):
            cmd.extend(["-f", path])
        else:
            cmd.extend(["--project-directory", path])

        cmd.extend(command_args)

        # Run the command asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            return _error_response(
                f"Command timed out after {timeout}s: {' '.join(cmd)}", "timeout_error"
            )

        output = stdout.decode().strip()
        error_output = stderr.decode().strip()

        if process.returncode != 0:
            return _error_response(
                f"Docker Compose failed: {error_output}",
                "compose_error",
                diagnostic_info={"stdout": output, "exit_code": process.returncode},
            )

        return _success_response(
            {"output": output, "stderr": error_output}, operation="compose"
        )
    except Exception as e:
        logger.error(f"Failed to run compose command: {e}")
        return _error_response(str(e), "internal_error")


@_get_app().tool()
async def orch_ops(
    operation: Literal[
        "compose_up",
        "compose_down",
        "compose_ps",
        "compose_logs",
        "compose_config",
        "compose_restart",
    ],
    path: str = ".",
    services: Optional[list[str]] = None,
    detach: bool = True,
    build: bool = False,
    scale: Optional[dict[str, int]] = None,
    remove_orphans: bool = True,
    volumes_prune: bool = False,
    all_services: bool = False,
    validate: bool = True,
    tail: Optional[int] = 100,
    since: Optional[str] = None,
    until: Optional[str] = None,
    timestamps: bool = False,
    follow: bool = False,
    timeout: int = 300,
) -> dict[str, Any]:
    """Docker Compose Orchestration operations.

    Args:
        operation (Literal, required): Available compose operations:
            - "compose_up": Start stack (requires: path)
            - "compose_down": Stop stack (requires: path)
            - "compose_ps": List services (requires: path)
            - "compose_logs": View logs (requires: path)
            - "compose_config": Validate config (requires: path)
            - "compose_restart": Restart stack (requires: path)

        --- PATH & SERVICES ---

        path (str): Path to compose file or project root. Default: "."
        services (List[str] | None): Specific services to target

        --- RUNTIME OPTIONS ---

        detach (bool): Run in background. Default: True
        build (bool): Build before start. Default: False
        scale (Dict | None): Service replicas
        remove_orphans (bool): Cleanup extra containers. Default: True
        volumes_prune (bool): Delete volumes on down. Default: False
        all_services (bool): Include stopped in ps. Default: False
        validate (bool): Check syntax. Default: True

        --- LOGGING & TIMEOUT ---

        tail (int | None): Log lines. Default: 100
        since/until (str | None): Log time range
        timestamps (bool): Include timestamps in logs. Default: False
        follow (bool): Follow log stream. Default: False
        timeout (int): Operation timeout. Default: 300
    """
    try:
        if not operation:
            return _clarification_response(
                ["No operation specified. Choose from: compose_up, compose_down, etc."],
                options={
                    "operation": [
                        "compose_up",
                        "compose_down",
                        "compose_ps",
                        "compose_logs",
                        "compose_config",
                        "compose_restart",
                    ]
                },
            )

        cmd_args = []
        if operation == "compose_up":
            cmd_args = ["up"]
            if detach:
                cmd_args.append("-d")
            if build:
                cmd_args.append("--build")
            if scale:
                for svc, count in scale.items():
                    cmd_args.extend(["--scale", f"{svc}={count}"])
            if services:
                cmd_args.extend(services)
        elif operation == "compose_down":
            cmd_args = ["down"]
            if remove_orphans:
                cmd_args.append("--remove-orphans")
            if volumes_prune:
                cmd_args.append("--volumes")
        elif operation == "compose_ps":
            cmd_args = ["ps"]
            if all_services:
                cmd_args.append("--all")
            cmd_args.extend(["--format", "json"])
            if services:
                cmd_args.extend(services)
        elif operation == "compose_logs":
            cmd_args = ["logs"]
            if follow:
                cmd_args.append("-f")
            if tail:
                cmd_args.extend(["--tail", str(tail)])
            if since:
                cmd_args.extend(["--since", since])
            if until:
                cmd_args.extend(["--until", until])
            if timestamps:
                cmd_args.append("-t")
            if services:
                cmd_args.extend(services)
        elif operation == "compose_config":
            cmd_args = ["config"]
            if not validate:
                cmd_args.append("--no-interpolate")
        elif operation == "compose_restart":
            cmd_args = ["restart"]
            if services:
                cmd_args.extend(services)
        else:
            return _error_response(
                f"Unknown operation: {operation}", "unsupported_operation"
            )

        return await _run_compose_command(path, cmd_args, timeout)

    except Exception as e:
        logger.error(
            f"Orchestration operation '{operation}' failed: {e}", exc_info=True
        )
        return _error_response(str(e), "internal_error")
