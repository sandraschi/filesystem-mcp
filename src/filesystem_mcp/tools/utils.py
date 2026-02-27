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
                # If relative_to succeeds without raising, path IS within sensitive dir
                raise PermissionError(f"Access to system path denied: {sensitive}")
            except ValueError:
                # ValueError means path is NOT within sensitive dir - safe to continue
                continue

        return path_obj

    except PermissionError:
        raise
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


# Enhanced Response Patterns (FastMCP 2.14.3+)

def _success_response(
    result: dict,
    operation: str = None,
    execution_time_ms: int = None,
    quality_metrics: dict = None,
    recommendations: list = None,
    next_steps: list = None,
    related_operations: list = None
) -> dict:
    """Generate a rich success response with conversational metadata."""
    response = {
        "success": True,
        "operation": operation or "completed",
        "result": result,
        "timestamp": datetime.now().isoformat(),
        "quality_metrics": quality_metrics or {},
        "recommendations": recommendations or [],
        "next_steps": next_steps or [],
        "related_operations": related_operations or [],
    }

    if execution_time_ms is not None:
        response["execution_time_ms"] = execution_time_ms

    return response


def _error_response(
    error: str,
    error_type: str = "general",
    recovery_options: list = None,
    diagnostic_info: dict = None,
    suggested_fixes: list = None,
    alternative_approaches: list = None,
    estimated_resolution_time: str = None
) -> dict:
    """Generate an intelligent error response with recovery guidance."""
    response = {
        "success": False,
        "error": error,
        "error_type": error_type,
        "timestamp": datetime.now().isoformat(),
    }

    if recovery_options:
        response["recovery_options"] = recovery_options
    else:
        response["recovery_options"] = [
            "Check your inputs and try again",
            "Consult the tool documentation for correct usage",
            "Verify file/directory permissions and paths"
        ]

    if diagnostic_info:
        response["diagnostic_info"] = diagnostic_info
    else:
        response["diagnostic_info"] = {
            "timestamp": datetime.now().isoformat(),
            "platform": sys.platform,
            "python_version": sys.version.split()[0],
        }

    if suggested_fixes:
        response["suggested_fixes"] = suggested_fixes

    if alternative_approaches:
        response["alternative_approaches"] = alternative_approaches

    if estimated_resolution_time:
        response["estimated_resolution_time"] = estimated_resolution_time

    return response


def _clarification_response(
    ambiguities,
    options: dict = None,
    suggested_questions: list = None,
    preserved_context: dict = None,
    estimated_completion: str = None
) -> dict:
    """Generate a clarification response for ambiguous requests.

    Accepts ambiguities as either a list (new style) or positional string args
    for backward compatibility with old call sites.
    """
    # Handle old-style positional call: _clarification_response("field", "message", [...options])
    # In that case ambiguities is a string, options might be a string (message), suggested_questions might be a list
    if isinstance(ambiguities, str):
        # Old-style: _clarification_response("field_name", "description", ["opt1", ...])
        field = ambiguities
        description = options if isinstance(options, str) else ""
        old_options_list = suggested_questions if isinstance(suggested_questions, list) else []
        ambiguities_list = [f"{field}: {description}"] if description else [field]
        options = {"available": old_options_list} if old_options_list else None
        suggested_questions = None
    else:
        ambiguities_list = ambiguities

    response = {
        "status": "clarification_needed",
        "ambiguities": ambiguities_list,
        "timestamp": datetime.now().isoformat(),
    }

    if options:
        response["options"] = options

    if suggested_questions:
        response["suggested_questions"] = suggested_questions
    else:
        response["suggested_questions"] = [
            "Could you please clarify what you'd like me to do?",
            "What specific operation are you looking for?",
            "Would you like me to show you the available options?"
        ]

    if preserved_context:
        response["preserved_context"] = preserved_context

    if estimated_completion:
        response["estimated_completion"] = estimated_completion

    return response


def _progress_response(
    operation: str,
    current: int,
    total: int,
    phase: str = None,
    estimated_completion: str = None,
    details: dict = None
) -> dict:
    """Generate a progress update response for long-running operations."""
    return {
        "status": "in_progress",
        "operation": operation,
        "progress": {
            "current": current,
            "total": total,
            "percentage": (current / total * 100) if total > 0 else 0,
        },
        "phase": phase,
        "estimated_completion": estimated_completion,
        "details": details or {},
        "timestamp": datetime.now().isoformat(),
    }


def _interactive_response(
    message: str,
    options: list,
    context: dict = None,
    follow_up_operations: list = None
) -> dict:
    """Generate an interactive response requiring user choice."""
    response = {
        "status": "interactive",
        "message": message,
        "options": options,
        "timestamp": datetime.now().isoformat(),
    }

    if context:
        response["context"] = context

    if follow_up_operations:
        response["follow_up_operations"] = follow_up_operations

    return response
