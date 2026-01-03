import logging
import platform
import sys
from datetime import datetime, timezone
from typing import Any, Literal, Optional

from .utils import (
    _clarification_response,
    _error_response,
    _get_app,
    _success_response,
)

logger = logging.getLogger(__name__)


@_get_app().tool()
async def host_ops(
    operation: Literal[
        "get_help",
        "get_system_info",
        "get_environment_info",
        "get_security_info",
        "get_hardware_info",
        "get_software_info",
        "get_time_info",
        "get_locale_info",
        "get_user_info",
        "get_session_info",
        "get_service_status",
        "get_log_info",
    ],
    category: Optional[str] = None,
    tool_name: Optional[str] = None,
    level: str = "basic",
) -> dict[str, Any]:
    """Host System Context (Info, Env, Help, User).

    Args:
        operation (Literal, required): Available context operations:
            - "get_help": Documentation for tools and categories
            - "get_system_info": OS, node, release, and python version
            - "get_environment_info": Environment variables and paths
            - "get_security_info": Basic user and permission info
            - "get_hardware_info": Machine architecture and processor info
            - "get_software_info": Python executable and loaded modules
            - "get_time_info": Local and UTC time with offsets
            - "get_locale_info": System language and encoding settings
            - "get_user_info": Current username and home directory
            - "get_session_info": Process ID and hostname
            - "get_service_status": Availability of system services
            - "get_log_info": Access to system logs (if permitted)

        --- OPTIONS ---

        category (str | None): Help category filter
        tool_name (str | None): Specific tool documentation
        level (str): Help detail level (basic, advanced). Default: "basic"
    """
    try:
        if not operation:
            return _clarification_response(
                "operation", "No operation specified", ["get_system_info", "get_environment_info"]
            )

        if operation == "get_help":
            return await _get_help(category, tool_name, level)
        elif operation == "get_system_info":
            return await _get_system_info()
        elif operation == "get_environment_info":
            return await _get_environment_info()
        elif operation == "get_security_info":
            return await _get_security_info()
        elif operation == "get_hardware_info":
            return await _get_hardware_info()
        elif operation == "get_software_info":
            return await _get_software_info()
        elif operation == "get_time_info":
            return await _get_time_info()
        elif operation == "get_locale_info":
            return await _get_locale_info()
        elif operation == "get_user_info":
            return await _get_user_info()
        elif operation == "get_session_info":
            return await _get_session_info()
        elif operation == "get_service_status":
            return await _get_service_status()
        elif operation == "get_log_info":
            return await _get_log_info()
        else:
            return _error_response(f"Unknown operation: {operation}", "unsupported_operation")
    except Exception as e:
        logger.error(f"Host context operation '{operation}' failed: {e}", exc_info=True)
        return _error_response(str(e), "internal_error")


async def _get_help(category, tool_name, level):
    try:
        help_info = {
            "level": level,
            "categories": {
                "filesystem": "File system operations (read, write, list, search, etc.)",
                "docker": "Docker container and image management",
                "repository": "Git repository operations",
                "system": "System monitoring and help tools",
            },
        }
        if category == "filesystem":
            help_info["tools"] = {"file_ops": "Unified file ops", "dir_ops": "Directory ops"}
        elif category == "docker":
            help_info["tools"] = {"container_ops": "Container mgmt", "infra_ops": "Images/Nets"}
        elif category == "repository":
            help_info["tools"] = {"repo_ops": "Git core", "git_ops": "Git mgmt"}
        elif category == "system":
            help_info["tools"] = {"monitor_ops": "Monitoring", "host_ops": "Host context"}

        return _success_response(help_info)
    except Exception as e:
        return _error_response(str(e), "internal_error")


async def _get_system_info():
    try:
        return _success_response(
            {
                "os": platform.system(),
                "node": platform.node(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": sys.version,
                "python_executable": sys.executable,
            }
        )
    except Exception as e:
        return _error_response(str(e), "internal_error")


async def _get_environment_info():
    try:
        import os
        env = dict(os.environ)
        sensitive = ["pass", "key", "secret", "token", "auth"]
        filtered = {k: ("***" if any(s in k.lower() for s in sensitive) else v) for k, v in env.items()}
        return _success_response(
            {
                "env": filtered,
                "path": os.environ.get("PATH", "").split(os.pathsep),
                "cwd": os.getcwd(),
            }
        )
    except Exception as e:
        return _error_response(str(e), "internal_error")


async def _get_security_info():
    try:
        import os
        return _success_response(
            {
                "user": os.getlogin() if hasattr(os, "getlogin") else None,
                "uid": os.getuid() if hasattr(os, "getuid") else None,
                "gid": os.getgid() if hasattr(os, "getgid") else None,
            }
        )
    except Exception as e:
        return _error_response(str(e), "internal_error")


async def _get_hardware_info():
    try:
        import psutil
        return _success_response(
            {
                "cpu_count": psutil.cpu_count(logical=True),
                "phys_cpu_count": psutil.cpu_count(logical=False),
                "total_mem": psutil.virtual_memory().total,
            }
        )
    except Exception as e:
        return _error_response(str(e), "internal_error")


async def _get_software_info():
    try:
        return _success_response(
            {"python_version": sys.version, "loaded_modules_count": len(sys.modules)}
        )
    except Exception as e:
        return _error_response(str(e), "internal_error")


async def _get_time_info():
    try:
        now = datetime.now()
        return _success_response(
            {
                "local": now.isoformat(),
                "utc": datetime.now(timezone.utc).isoformat(),
                "timezone": str(now.astimezone().tzinfo),
            }
        )
    except Exception as e:
        return _error_response(str(e), "internal_error")


async def _get_locale_info():
    try:
        import locale
        import os
        return _success_response(
            {
                "locale": locale.getlocale(),
                "encoding": locale.getpreferredencoding(),
                "lang": os.environ.get("LANG"),
            }
        )
    except Exception as e:
        return _error_response(str(e), "internal_error")


async def _get_user_info():
    try:
        import os
        return _success_response(
            {
                "user": os.getlogin() if hasattr(os, "getlogin") else None,
                "home": os.path.expanduser("~"),
            }
        )
    except Exception as e:
        return _error_response(str(e), "internal_error")


async def _get_session_info():
    try:
        import os
        return _success_response({"pid": os.getpid(), "ppid": os.getppid() if hasattr(os, "getppid") else None})
    except Exception as e:
        return _error_response(str(e), "internal_error")


async def _get_service_status():
    return _success_response({"status": "Checking not supported on this platform"})


async def _get_log_info():
    return _success_response({"status": "Log access restricted"})
