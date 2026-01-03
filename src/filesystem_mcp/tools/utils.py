import logging
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


# Shared app instance logic
def _get_app():
    """Get the app instance locally to avoid circular imports."""
    from .. import app

    return app


# Path resolution logic
def _safe_resolve_path(file_path: str) -> Path:
    """Safely resolve a file path with security validation."""
    try:
        # Convert to Path and resolve any symlinks/relative paths
        path_obj = Path(file_path).resolve()

        # Basic security check - prevent access to sensitive system paths
        sensitive_paths = [
            Path("/etc"),
            Path("/proc"),
            Path("/sys"),
            Path("/dev"),
            Path("C:\\Windows\\System32"),
            Path("C:\\Windows\\System"),
        ]

        for sensitive in sensitive_paths:
            try:
                path_obj.relative_to(sensitive)
                raise ValueError(f"Access to system path denied: {sensitive}")
            except ValueError:
                # Path is not within sensitive directory, continue checking
                pass

        return path_obj

    except Exception as e:
        logger.error(f"Path resolution failed for {file_path}: {e}")
        raise ValueError(f"Invalid path: {file_path}") from e


# Size formatting logic
def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    size_index = 0
    size = float(size_bytes)

    while size >= 1024.0 and size_index < len(size_names) - 1:
        size /= 1024.0
        size_index += 1

    if size_index == 0:
        return f"{int(size)} {size_names[size_index]}"
    else:
        return f"{size:.1f} {size_names[size_index]}"


# Docker client shared logic
_docker_client = None


def _get_docker_client():
    """Get Docker client with lazy initialization."""
    global _docker_client
    if _docker_client is None:
        try:
            import docker

            _docker_client = docker.from_env()
        except ImportError as e:
            raise RuntimeError(
                "Docker operations require 'docker' package. Install with: pip install docker"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Docker: {e}") from e
    return _docker_client


# Git shared logic
def _has_upstream(repo):
    """Check if repository has an upstream remote."""
    try:
        repo.git.rev_parse("@{upstream}")
        return True
    except Exception:
        return False


# Enhanced Response Helpers (FastMCP 2.14.1+)
def _clarification_response(param_name: str, reason: str, options: list = None) -> dict:
    """Generate a conversational clarification response."""
    res = {
        "status": "clarification_needed",
        "parameter": param_name,
        "reason": reason,
        "suggested_questions": [
            f"Could you please provide the {param_name}?",
            f"What value should I use for {param_name}?",
        ],
    }
    if options:
        res["clarification_options"] = options
    return res


def _error_response(error: str, error_type: str = "general", recovery_options: list = None) -> dict:
    """Generate a conversational error recovery response."""
    return {
        "success": False,
        "error": error,
        "error_type": error_type,
        "recovery_options": recovery_options
        or ["Check your inputs and try again", "Consult the tool documentation"],
        "diagnostic_info": {
            "timestamp": datetime.now().isoformat(),
            "os": sys.platform,
        },
    }


def _success_response(data: dict, next_steps: list = None, related_ops: list = None) -> dict:
    """Generate a conversational success response with rich metadata."""
    res = {"success": True, **data}
    if next_steps:
        res["next_steps"] = next_steps
    if related_ops:
        res["related_operations"] = related_ops
    return res
