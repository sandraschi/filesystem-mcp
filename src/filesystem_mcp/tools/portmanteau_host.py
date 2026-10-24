import logging
import platform
import sys
from datetime import UTC, datetime
from typing import Any, Literal

from .utils import (
    READ_ONLY,
    _clarification_response,
    _error_response,
    _get_app,
    _success_response,
)

logger = logging.getLogger(__name__)


# ── Help data: every tool, every operation ─────────────────────────────────────

_TOOL_HELP = {
    "file_ops": {
        "category": "filesystem",
        "description": "Comprehensive file operations with enhanced conversational responses.",
        "operations": {
            "read_file": "Read complete file contents. Params: path, encoding(opt)",
            "write_file": "Write content to file with auto-backup. "
            "Params: path, content, encoding(opt), no_backup(opt)",
            "edit_file": "Replace unique string in file. Params: path, old_string, new_string, replace_all (or allow_multiple) for all occurrences",
            "move_file": "Move/rename file. Params: path, destination_path, overwrite(opt)",
            "read_file_lines": "Read specific line range. Params: path, offset(opt), limit(opt)",
            "read_multiple_files": "Batch read multiple files. Params: file_paths, max_file_size_mb(opt)",
            "file_exists": "Check file existence. Params: path, check_type(opt: file|any)",
            "get_file_info": "Detailed metadata. Params: path, include_content(opt), max_content_size(opt)",
            "head_file": "Read first N lines. Params: path, lines(opt, default 10)",
            "tail_file": "Read last N lines. Params: path, lines(opt, default 10)",
            "get_file_hash": "Streamed hash. Params: path, hash_algorithm(opt: md5|sha1|sha256)",
            "append_file": "Locked append. Params: path, content, encoding(opt), ensure_newline(opt)",
            "touch_file": "Create empty or bump mtime. Params: path, create_parents(opt)",
            "compress": "Zip/tar a file or dir. Params: path, destination_path(opt), archive_format(opt), overwrite(opt)",
            "decompress": "Extract archive. Params: path, destination_path(opt), overwrite(opt)",
        },
        "examples": {
            "basic": "file_ops(operation='read_file', path='D:/myfile.txt')",
            "intermediate": "file_ops(operation='edit_file', path='D:/config.json', "
            "old_string='old_value', new_string='new_value')",
            "advanced": "file_ops(operation='read_multiple_files', "
            "file_paths=['D:/a.py','D:/b.py'], max_file_size_mb=5.0)",
        },
    },
    "dir_ops": {
        "category": "filesystem",
        "description": "Directory structure and management operations.",
        "operations": {
            "list_directory": "List directory contents with metadata. "
            "Params: path, recursive(opt), include_hidden(opt)",
            "create_directory": "Create new directory. Params: path, create_parents(opt), exist_ok(opt)",
            "remove_directory": "Remove directory. Params: path, recursive(opt)",
            "directory_tree": "Visual tree of directory. "
            "Params: path, max_depth(opt), pattern(opt), output_format(opt: text|json)",
            "calculate_directory_size": "Get total size. Params: path",
            "find_empty_directories": "Locate empty dirs. Params: path",
            "copy_tree": "Copy dir tree. Params: path, destination_path, engine(opt: auto|shutil|robocopy), mirror(opt, robocopy-only), dry_run(opt), overwrite(opt), timeout(opt)",
            "move_directory": "Move/rename dir. Params: path, destination_path, overwrite(opt)",
        },
        "examples": {
            "basic": "dir_ops(operation='list_directory', path='D:/Dev/repos')",
            "intermediate": "dir_ops(operation='directory_tree', path='D:/project', max_depth=3)",
            "advanced": "dir_ops(operation='list_directory', path='D:/Dev', recursive=True, include_hidden=True)",
        },
    },
    "search_ops": {
        "category": "filesystem",
        "description": "Content analysis, grep, and file comparison operations.",
        "operations": {
            "grep_file": "Regex search in file. Params: path, search_pattern, "
            "case_sensitive(opt), max_matches(opt), context_lines(opt)",
            "count_pattern": "Count pattern occurrences. Params: path, search_pattern",
            "search_files": "Find files by name/glob. Params: path, search_pattern, recursive(opt)",
            "extract_log_lines": "Filter log lines by level/time. Params: path, start_time(opt), "
            "end_time(opt), log_levels(opt), max_lines(opt)",
            "compare_files": "Diff two files. Params: path, path2",
            "find_duplicate_files": "Hash-based duplicate detection. Params: path, min_size(opt), "
            "hash_algorithm(opt), max_duplicates(opt)",
            "find_large_files": "Locate large files. Params: path, min_size_mb(opt), max_results(opt)",
            "find_todos": "TODO/FIXME comments. Params: path, recursive(opt), search_pattern(opt regex override)",
            "find_symbols": "def/class/function/const definitions. Params: path, recursive(opt), search_pattern(opt filter)",
            "validate_json": "Parse JSON, report structure or first syntax error. Params: path",
            "analyze_project": "Detect project type/markers/frameworks. Params: path, max_results(opt)",
            "run_linter": "ruff check only. Params: path, fix(opt), read-only unless fix=True",
            "validate_config": "Validate json/yaml/toml/ini by extension. Params: path",
        },
        "examples": {
            "basic": "search_ops(operation='grep_file', path='D:/myfile.py', search_pattern='TODO')",
            "intermediate": "search_ops(operation='search_files', path='D:/Dev/repos', "
            "search_pattern='*.py', recursive=True)",
            "advanced": "search_ops(operation='extract_log_lines', path='D:/app.log', "
            "log_levels=['ERROR','CRITICAL'], start_time='2026-02-20')",
        },
    },
    "container_ops": {
        "category": "docker",
        "description": "Docker container lifecycle management.",
        "operations": {
            "list_containers": "List containers with optional stats. Params: show_stats(opt)",
            "get_container": "Detailed container info. Params: container_id",
            "create_container": "Create container. Params: image, name(opt), ports(opt), "
            "volumes(opt), environment(opt), detach(opt)",
            "start_container": "Start stopped container. Params: container_id",
            "stop_container": "Stop running container. Params: container_id, timeout(opt)",
            "restart_container": "Restart container. Params: container_id, timeout(opt)",
            "remove_container": "Remove container. Params: container_id, force(opt)",
            "container_exec": "Run command in container. Params: container_id, command",
            "container_logs": "Stream container logs. Params: container_id, tail(opt), since(opt), timestamps(opt)",
            "container_stats": "Resource statistics. Params: container_id",
        },
        "examples": {
            "basic": "container_ops(operation='list_containers')",
            "intermediate": "container_ops(operation='container_logs', container_id='myapp', "
            "tail=100, timestamps=True)",
        },
    },
    "infra_ops": {
        "category": "docker",
        "description": "Docker images, networks, and volumes management.",
        "operations": {
            "list_images": "List local images. Params: all_images(opt)",
            "get_image": "Image metadata. Params: image",
            "pull_image": "Download image. Params: image, tag(opt)",
            "build_image": "Build from Dockerfile. Params: path, dockerfile(opt), tag(opt), nocache(opt)",
            "remove_image": "Delete image. Params: image, force(opt)",
            "prune_images": "Cleanup unused images.",
            "list_networks": "List Docker networks.",
            "create_network": "Create network. Params: name, driver(opt)",
            "remove_network": "Delete network. Params: network_id, force(opt)",
            "prune_networks": "Cleanup unused networks.",
            "list_volumes": "List Docker volumes.",
            "create_volume": "Create volume. Params: volume_name, driver(opt)",
            "remove_volume": "Delete volume. Params: volume_name, force(opt)",
            "prune_volumes": "Cleanup unused volumes.",
        },
        "examples": {
            "basic": "infra_ops(operation='list_images')",
            "intermediate": "infra_ops(operation='pull_image', image='python', tag='3.13-slim')",
        },
    },
    "compose_up": {
        "category": "docker",
        "description": "Docker Compose: start services (docker compose up).",
        "operations": {"compose_up": "path, services(opt), detach, build, scale(opt), timeout(opt)"},
        "examples": {"basic": "compose_up(path='D:/myproject')"},
    },
    "compose_down": {
        "category": "docker",
        "description": "Docker Compose: stop stack and remove containers (down).",
        "operations": {"compose_down": "path, remove_orphans, volumes_prune (destructive to volumes)"},
        "examples": {"basic": "compose_down(path='D:/myproject')"},
    },
    "compose_ps": {
        "category": "docker",
        "description": "Docker Compose: list services as JSON.",
        "operations": {"compose_ps": "path, services(opt), all_services"},
        "examples": {"basic": "compose_ps(path='D:/myproject')"},
    },
    "compose_logs": {
        "category": "docker",
        "description": "Docker Compose: service logs.",
        "operations": {"compose_logs": "path, services(opt), tail, since, until, timestamps, follow"},
        "examples": {"basic": "compose_logs(path='D:/myproject', tail=50)"},
    },
    "compose_config": {
        "category": "docker",
        "description": "Docker Compose: render/validate configuration.",
        "operations": {"compose_config": "path, validate"},
        "examples": {"basic": "compose_config(path='D:/myproject')"},
    },
    "compose_restart": {
        "category": "docker",
        "description": "Docker Compose: restart services.",
        "operations": {"compose_restart": "path, services(opt)"},
        "examples": {"basic": "compose_restart(path='D:/myproject')"},
    },
    "monitor_get_system_status": {
        "category": "system",
        "description": "OS/CPU/memory snapshot; optional disk, network, process sample.",
        "operations": {"monitor_get_system_status": "include_processes, include_disk, include_network, max_processes"},
        "examples": {"basic": "monitor_get_system_status()"},
    },
    "monitor_get_resource_usage": {
        "category": "system",
        "description": "Quick CPU/RAM/disk and boot time.",
        "operations": {"monitor_get_resource_usage": "(no params)"},
        "examples": {"basic": "monitor_get_resource_usage()"},
    },
    "monitor_get_process_info": {
        "category": "system",
        "description": "Process list; filter_pattern is substring on process name (not regex).",
        "operations": {"monitor_get_process_info": "max_processes, filter_pattern, sort_by, sort_order"},
        "examples": {"basic": "monitor_get_process_info(filter_pattern='python')"},
    },
    "monitor_get_performance_metrics": {
        "category": "system",
        "description": "CPU times, memory, swap, disk and net I/O counters.",
        "operations": {"monitor_get_performance_metrics": "(no params)"},
        "examples": {"basic": "monitor_get_performance_metrics()"},
    },
    "monitor_get_memory_info": {
        "category": "system",
        "description": "Virtual and swap memory details.",
        "operations": {"monitor_get_memory_info": "(no params)"},
        "examples": {"basic": "monitor_get_memory_info()"},
    },
    "monitor_get_cpu_info": {
        "category": "system",
        "description": "Core counts, frequency, per-CPU usage.",
        "operations": {"monitor_get_cpu_info": "(no params)"},
        "examples": {"basic": "monitor_get_cpu_info()"},
    },
    "monitor_get_disk_usage": {
        "category": "system",
        "description": "Per-partition disk usage.",
        "operations": {"monitor_get_disk_usage": "(no params)"},
        "examples": {"basic": "monitor_get_disk_usage()"},
    },
    "monitor_get_network_info": {
        "category": "system",
        "description": "Network I/O counters and interface addresses.",
        "operations": {"monitor_get_network_info": "(no params)"},
        "examples": {"basic": "monitor_get_network_info()"},
    },
    "host_ops": {
        "category": "system",
        "description": "Host system context: info, environment, help, and user details.",
        "operations": {
            "get_help": "This help system. Params: category(opt), tool_name(opt), "
            "level(opt: basic|intermediate|advanced)",
            "get_system_info": "OS, node, release, Python version.",
            "get_environment_info": "Environment variables and PATH.",
            "get_security_info": "Current user and permissions.",
            "get_hardware_info": "CPU count and total RAM (via psutil).",
            "get_software_info": "Python version and loaded module count.",
            "get_time_info": "Local and UTC time with timezone.",
            "get_locale_info": "System language and encoding.",
            "get_user_info": "Username and home directory.",
            "get_session_info": "Process ID and hostname.",
            "get_service_status": "Check availability of system services.",
            "get_log_info": "Access system logs (if permitted).",
        },
        "examples": {
            "basic": "host_ops(operation='get_system_info')",
            "intermediate": "host_ops(operation='get_help', category='filesystem', level='intermediate')",
        },
    },
    "agentic_file_workflow": {
        "category": "sampling",
        "description": "LLM-orchestrated file workflows using ctx.sample() "
        "(no sampling.tools - Claude Desktop compatible).",
        "operations": {
            "agentic_file_workflow": (
                "Execute a high-level file workflow. "
                "Gathers filesystem context server-side, calls ctx.sample() with context + prompt, "
                "returns structured WorkflowResult. "
                "Params: workflow_prompt (required), available_tools (hint list)"
            ),
        },
        "notes": [
            "Requires a client that supports basic sampling (Claude Desktop, VS Code, Cline).",
            "Does NOT require sampling.tools capability - uses no-tools sampling pattern.",
            "Auto-detects Windows paths (e.g. D:\\Dev\\repos\\...) in workflow_prompt and pre-lists them.",
        ],
        "examples": {
            "basic": (
                "agentic_file_workflow("
                "workflow_prompt='List all Python files in D:\\Dev\\repos\\myproject and count LOC', "
                "available_tools=['file_ops','search_ops'])"
            ),
        },
    },
}

_CATEGORIES = {
    "filesystem": ["file_ops", "dir_ops", "search_ops"],
    "docker": [
        "container_ops",
        "infra_ops",
        "compose_up",
        "compose_down",
        "compose_ps",
        "compose_logs",
        "compose_config",
        "compose_restart",
    ],
    "system": [
        "monitor_get_system_status",
        "monitor_get_resource_usage",
        "monitor_get_process_info",
        "monitor_get_performance_metrics",
        "monitor_get_memory_info",
        "monitor_get_cpu_info",
        "monitor_get_disk_usage",
        "monitor_get_network_info",
        "host_ops",
    ],
    "sampling": ["agentic_file_workflow"],
}


# ── Tool registration ──────────────────────────────────────────────────────────


@_get_app().tool(annotations=READ_ONLY, version="2.2.0")
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
    ]
    | None = None,
    category: str | None = None,
    tool_name: str | None = None,
    level: str = "basic",
) -> dict[str, Any]:
    """Host System Context (Info, Env, Help, User).

    Operations: get_help, get_system_info, get_environment_info, get_security_info,
    get_hardware_info, get_software_info, get_time_info, get_locale_info,
    get_user_info, get_session_info, get_service_status, get_log_info.

    Args: See Parameters block.

    ## Return Format
    {"success": bool, "action": str, "message": str, "result": {...}}
    - result for get_system_info: {"platform", "python", "machine", "cpu_cores", "memory_total"}
    - result for get_environment_info: {"variables": {...}}

    ## Examples
    host_ops(operation="get_help", category="filesystem")
    host_ops(operation="get_system_info", detailed=True)
    host_ops(operation="get_environment_info")
    """
    try:
        if not operation:
            return _clarification_response(
                "operation",
                "No operation specified",
                ["get_system_info", "get_environment_info"],
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


# ── Help implementation ────────────────────────────────────────────────────────


async def _get_help(category, tool_name, level):
    try:
        _GIT_REDIRECT = (
            "Git operations moved to git-github-mcp (gitops). "
            "Use git_ops(operation='status', repo_path='...') / github_ops for GitHub."
        )
        # ── tool_name drill-down ───────────────────────────────────────────────
        if tool_name:
            tool_key = tool_name.lower().strip()
            if tool_key in ("repo_ops", "repository") or tool_key.startswith("git_"):
                return _error_response(
                    f"{tool_key!r} moved out of filesystem-mcp. {_GIT_REDIRECT}",
                    "moved",
                    [_GIT_REDIRECT],
                )
            info = _TOOL_HELP.get(tool_key)
            if not info:
                return _error_response(
                    f"Unknown tool: {tool_name!r}. Valid tools: {', '.join(sorted(_TOOL_HELP))}",
                    "not_found",
                )
            result = {
                "tool": tool_key,
                "category": info["category"],
                "description": info["description"],
                "operations": info["operations"],
            }
            if level in ("intermediate", "advanced") and "notes" in info:
                result["notes"] = info["notes"]
            if "examples" in info:
                example_levels = (
                    ["basic"]
                    if level == "basic"
                    else ["basic", "intermediate"]
                    if level == "intermediate"
                    else list(info["examples"].keys())
                )
                result["examples"] = {k: v for k, v in info["examples"].items() if k in example_levels}
            return _success_response(result)

        # ── category drill-down ────────────────────────────────────────────────
        if category:
            cat_key = category.lower().strip()
            if cat_key == "repository":
                return _error_response(
                    f"Category 'repository' moved out of filesystem-mcp. {_GIT_REDIRECT}",
                    "moved",
                    [_GIT_REDIRECT],
                )
            if cat_key not in _CATEGORIES:
                return _error_response(
                    f"Unknown category: {category!r}. Valid categories: {', '.join(sorted(_CATEGORIES))}",
                    "not_found",
                )
            tools_in_cat = _CATEGORIES[cat_key]
            result = {
                "category": cat_key,
                "tools": {},
            }
            for t in tools_in_cat:
                info = _TOOL_HELP[t]
                entry = {"description": info["description"]}
                if level == "basic":
                    entry["operations"] = list(info["operations"].keys())
                else:
                    entry["operations"] = info["operations"]
                if level == "advanced" and "examples" in info:
                    entry["examples"] = info["examples"]
                result["tools"][t] = entry
            return _success_response(result)

        # ── overview ───────────────────────────────────────────────────────────
        overview: dict[str, Any] = {
            "level": level,
            "server": "filesystem-mcp v2.2.0",
            "categories": {},
        }
        for cat, tools in _CATEGORIES.items():
            cat_entry: dict[str, Any] = {}
            for t in tools:
                info = _TOOL_HELP[t]
                if level == "basic":
                    cat_entry[t] = info["description"]
                else:
                    cat_entry[t] = {
                        "description": info["description"],
                        "operation_count": len(info["operations"]),
                        "operations": list(info["operations"].keys()),
                    }
            overview["categories"][cat] = cat_entry

        overview["usage_tip"] = (
            "Use host_ops(operation='get_help', category='<cat>') to drill into a category, "
            "or host_ops(operation='get_help', tool_name='<tool>') for a specific tool."
        )
        return _success_response(overview)

    except Exception as e:
        return _error_response(str(e), "internal_error")


# ── System info helpers ────────────────────────────────────────────────────────


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
                "uid": getattr(os, "getuid", lambda: None)(),
                "gid": getattr(os, "getgid", lambda: None)(),
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
        return _success_response({"python_version": sys.version, "loaded_modules_count": len(sys.modules)})
    except Exception as e:
        return _error_response(str(e), "internal_error")


async def _get_time_info():
    try:
        now = datetime.now()
        return _success_response(
            {
                "local": now.isoformat(),
                "utc": datetime.now(UTC).isoformat(),
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

        return _success_response(
            {
                "pid": os.getpid(),
                "ppid": os.getppid() if hasattr(os, "getppid") else None,
            }
        )
    except Exception as e:
        return _error_response(str(e), "internal_error")


async def _get_service_status():
    return _success_response({"status": "Checking not supported on this platform"})


async def _get_log_info():
    return _success_response({"status": "Log access restricted"})
