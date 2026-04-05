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


# ── Help data: every tool, every operation ─────────────────────────────────────

_TOOL_HELP = {
    "file_ops": {
        "category": "filesystem",
        "description": "Comprehensive file operations with enhanced conversational responses.",
        "operations": {
            "read_file":          "Read complete file contents. Params: path, encoding(opt)",
            "write_file":         "Write content to file with auto-backup. Params: path, content, encoding(opt), no_backup(opt)",
            "edit_file":          "Replace unique string in file. Params: path, old_string, new_string",
            "move_file":          "Move/rename file. Params: path, destination_path, overwrite(opt)",
            "read_file_lines":    "Read specific line range. Params: path, offset(opt), limit(opt)",
            "read_multiple_files":"Batch read multiple files. Params: file_paths, max_file_size_mb(opt)",
            "file_exists":        "Check file existence. Params: path, check_type(opt: file|any)",
            "get_file_info":      "Detailed metadata. Params: path, include_content(opt), max_content_size(opt)",
            "head_file":          "Read first N lines. Params: path, lines(opt, default 10)",
            "tail_file":          "Read last N lines. Params: path, lines(opt, default 10)",
        },
        "examples": {
            "basic":        "file_ops(operation='read_file', path='D:/myfile.txt')",
            "intermediate": "file_ops(operation='edit_file', path='D:/config.json', old_string='old_value', new_string='new_value')",
            "advanced":     "file_ops(operation='read_multiple_files', file_paths=['D:/a.py','D:/b.py'], max_file_size_mb=5.0)",
        },
    },
    "dir_ops": {
        "category": "filesystem",
        "description": "Directory structure and management operations.",
        "operations": {
            "list_directory":          "List directory contents with metadata. Params: path, recursive(opt), include_hidden(opt)",
            "create_directory":        "Create new directory. Params: path, create_parents(opt), exist_ok(opt)",
            "remove_directory":        "Remove directory. Params: path, recursive(opt)",
            "directory_tree":          "Visual tree of directory. Params: path, max_depth(opt), pattern(opt), output_format(opt: text|json)",
            "calculate_directory_size":"Get total size. Params: path",
            "find_empty_directories":  "Locate empty dirs. Params: path",
        },
        "examples": {
            "basic":        "dir_ops(operation='list_directory', path='D:/Dev/repos')",
            "intermediate": "dir_ops(operation='directory_tree', path='D:/project', max_depth=3)",
            "advanced":     "dir_ops(operation='list_directory', path='D:/Dev', recursive=True, include_hidden=True)",
        },
    },
    "search_ops": {
        "category": "filesystem",
        "description": "Content analysis, grep, and file comparison operations.",
        "operations": {
            "grep_file":           "Regex search in file. Params: path, search_pattern, case_sensitive(opt), max_matches(opt), context_lines(opt)",
            "count_pattern":       "Count pattern occurrences. Params: path, search_pattern",
            "search_files":        "Find files by name/glob. Params: path, search_pattern, recursive(opt)",
            "extract_log_lines":   "Filter log lines by level/time. Params: path, start_time(opt), end_time(opt), log_levels(opt), max_lines(opt)",
            "compare_files":       "Diff two files. Params: path, path2",
            "find_duplicate_files":"Hash-based duplicate detection. Params: path, min_size(opt), hash_algorithm(opt), max_duplicates(opt)",
            "find_large_files":    "Locate large files. Params: path, min_size_mb(opt), max_results(opt)",
        },
        "examples": {
            "basic":        "search_ops(operation='grep_file', path='D:/myfile.py', search_pattern='TODO')",
            "intermediate": "search_ops(operation='search_files', path='D:/Dev/repos', search_pattern='*.py', recursive=True)",
            "advanced":     "search_ops(operation='extract_log_lines', path='D:/app.log', log_levels=['ERROR','CRITICAL'], start_time='2026-02-20')",
        },
    },
    "container_ops": {
        "category": "docker",
        "description": "Docker container lifecycle management.",
        "operations": {
            "list_containers":  "List containers with optional stats. Params: show_stats(opt)",
            "get_container":    "Detailed container info. Params: container_id",
            "create_container": "Create container. Params: image, name(opt), ports(opt), volumes(opt), environment(opt), detach(opt)",
            "start_container":  "Start stopped container. Params: container_id",
            "stop_container":   "Stop running container. Params: container_id, timeout(opt)",
            "restart_container":"Restart container. Params: container_id, timeout(opt)",
            "remove_container": "Remove container. Params: container_id, force(opt)",
            "container_exec":   "Run command in container. Params: container_id, command",
            "container_logs":   "Stream container logs. Params: container_id, tail(opt), since(opt), timestamps(opt)",
            "container_stats":  "Resource statistics. Params: container_id",
        },
        "examples": {
            "basic":        "container_ops(operation='list_containers')",
            "intermediate": "container_ops(operation='container_logs', container_id='myapp', tail=100, timestamps=True)",
        },
    },
    "infra_ops": {
        "category": "docker",
        "description": "Docker images, networks, and volumes management.",
        "operations": {
            "list_images":   "List local images. Params: all_images(opt)",
            "get_image":     "Image metadata. Params: image",
            "pull_image":    "Download image. Params: image, tag(opt)",
            "build_image":   "Build from Dockerfile. Params: path, dockerfile(opt), tag(opt), nocache(opt)",
            "remove_image":  "Delete image. Params: image, force(opt)",
            "prune_images":  "Cleanup unused images.",
            "list_networks": "List Docker networks.",
            "create_network":"Create network. Params: name, driver(opt)",
            "remove_network":"Delete network. Params: network_id, force(opt)",
            "prune_networks":"Cleanup unused networks.",
            "list_volumes":  "List Docker volumes.",
            "create_volume": "Create volume. Params: volume_name, driver(opt)",
            "remove_volume": "Delete volume. Params: volume_name, force(opt)",
            "prune_volumes": "Cleanup unused volumes.",
        },
        "examples": {
            "basic":        "infra_ops(operation='list_images')",
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
    "repo_ops": {
        "category": "repository",
        "description": "Git core repository operations (status, commits, history).",
        "operations": {
            "clone_repo":       "Clone repository. Params: repo_url, target_dir",
            "get_repo_status":  "Staged/unstaged status. Params: repo_path",
            "commit_changes":   "Commit changes. Params: repo_path, message, add_all(opt), paths(opt)",
            "read_repo":        "Read repo structure. Params: repo_path, max_depth(opt)",
            "get_repo_info":    "General repo metadata. Params: repo_path",
            "get_commit_history":"Log of commits. Params: repo_path, max_commits(opt), author(opt), since(opt)",
            "show_commit":      "Detail for one commit. Params: repo_path, commit1 (hash)",
            "diff_changes":     "Show differences. Params: repo_path, commit1(opt), commit2(opt)",
            "blame_file":       "Line-by-line modification info. Params: repo_path, file_path",
            "get_file_history": "History for file. Params: repo_path, file_path",
            "revert_commit":    "Undo a commit. Params: repo_path, commit1 (hash)",
            "reset_to_commit":  "Move HEAD to hash. Params: repo_path, commit1 (hash), force(opt)",
            "cherry_pick":      "Apply hash to current branch. Params: repo_path, commit1 (hash)",
        },
        "examples": {
            "basic":        "repo_ops(operation='get_repo_status', repo_path='D:/Dev/repos/myproject')",
            "intermediate": "repo_ops(operation='commit_changes', repo_path='D:/Dev/repos/myproject', message='fix: update config', add_all=True)",
        },
    },
    "git_create_branch": {
        "category": "repository",
        "description": "Create a local branch at HEAD (does not switch).",
        "operations": {"git_create_branch": "repo_path, branch_name"},
        "examples": {"basic": "git_create_branch(repo_path='D:/Dev/repos/r', branch_name='feature/x')"},
    },
    "git_rename_branch": {
        "category": "repository",
        "description": "Rename a branch (git branch -m).",
        "operations": {"git_rename_branch": "repo_path, branch_name (old), target_branch (new)"},
        "examples": {"basic": "git_rename_branch(repo_path='...', branch_name='old', target_branch='new')"},
    },
    "git_switch_branch": {
        "category": "repository",
        "description": "Check out an existing branch.",
        "operations": {"git_switch_branch": "repo_path, branch_name"},
        "examples": {"basic": "git_switch_branch(repo_path='...', branch_name='main')"},
    },
    "git_merge_branch": {
        "category": "repository",
        "description": "Merge source_branch into current (or into target_branch if set).",
        "operations": {"git_merge_branch": "repo_path, source_branch, target_branch(opt)"},
        "examples": {"basic": "git_merge_branch(repo_path='...', source_branch='feature/x')"},
    },
    "git_delete_branch": {
        "category": "repository",
        "description": "Delete a local branch; force_delete for -D.",
        "operations": {"git_delete_branch": "repo_path, branch_name, force_delete"},
        "examples": {"basic": "git_delete_branch(repo_path='...', branch_name='old', force_delete=False)"},
    },
    "git_list_branches": {
        "category": "repository",
        "description": "List local branches and active branch.",
        "operations": {"git_list_branches": "repo_path"},
        "examples": {"basic": "git_list_branches(repo_path='...')"},
    },
    "git_create_tag": {
        "category": "repository",
        "description": "Create a tag.",
        "operations": {"git_create_tag": "repo_path, tag_name, tag_message(opt)"},
        "examples": {"basic": "git_create_tag(repo_path='...', tag_name='v1.0')"},
    },
    "git_list_tags": {
        "category": "repository",
        "description": "List tags.",
        "operations": {"git_list_tags": "repo_path"},
        "examples": {"basic": "git_list_tags(repo_path='...')"},
    },
    "git_delete_tag": {
        "category": "repository",
        "description": "Delete a local tag.",
        "operations": {"git_delete_tag": "repo_path, tag_name"},
        "examples": {"basic": "git_delete_tag(repo_path='...', tag_name='v1.0')"},
    },
    "git_push_changes": {
        "category": "repository",
        "description": "Push to remote; force_push overwrites non-FF when True.",
        "operations": {"git_push_changes": "repo_path, remote_name, push_branch(opt), force_push"},
        "examples": {"basic": "git_push_changes(repo_path='...', remote_name='origin')"},
    },
    "git_pull_changes": {
        "category": "repository",
        "description": "Pull from remote.",
        "operations": {"git_pull_changes": "repo_path, remote_name, pull_branch(opt)"},
        "examples": {"basic": "git_pull_changes(repo_path='...')"},
    },
    "git_fetch_updates": {
        "category": "repository",
        "description": "Fetch remote refs (no merge).",
        "operations": {"git_fetch_updates": "repo_path, remote_name"},
        "examples": {"basic": "git_fetch_updates(repo_path='...')"},
    },
    "git_list_remotes": {
        "category": "repository",
        "description": "List remotes.",
        "operations": {"git_list_remotes": "repo_path"},
        "examples": {"basic": "git_list_remotes(repo_path='...')"},
    },
    "git_add_remote": {
        "category": "repository",
        "description": "Add a remote.",
        "operations": {"git_add_remote": "repo_path, remote_name, remote_url"},
        "examples": {"basic": "git_add_remote(repo_path='...', remote_name='origin', remote_url='https://...')"},
    },
    "git_remove_remote": {
        "category": "repository",
        "description": "Remove a remote.",
        "operations": {"git_remove_remote": "repo_path, remote_name"},
        "examples": {"basic": "git_remove_remote(repo_path='...', remote_name='old')"},
    },
    "git_stash_changes": {
        "category": "repository",
        "description": "Stash working tree changes.",
        "operations": {"git_stash_changes": "repo_path, stash_message(opt)"},
        "examples": {"basic": "git_stash_changes(repo_path='...')"},
    },
    "git_apply_stash": {
        "category": "repository",
        "description": "Apply stash by index.",
        "operations": {"git_apply_stash": "repo_path, stash_index"},
        "examples": {"basic": "git_apply_stash(repo_path='...', stash_index=0)"},
    },
    "git_list_stashes": {
        "category": "repository",
        "description": "List stash entries.",
        "operations": {"git_list_stashes": "repo_path"},
        "examples": {"basic": "git_list_stashes(repo_path='...')"},
    },
    "git_resolve_conflicts": {
        "category": "repository",
        "description": "List unmerged paths after a failed merge/rebase.",
        "operations": {"git_resolve_conflicts": "repo_path"},
        "examples": {"basic": "git_resolve_conflicts(repo_path='...')"},
    },
    "git_rebase_branch": {
        "category": "repository",
        "description": "Rebase current branch onto source_branch.",
        "operations": {"git_rebase_branch": "repo_path, source_branch"},
        "examples": {"basic": "git_rebase_branch(repo_path='...', source_branch='main')"},
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
            "get_help":            "This help system. Params: category(opt), tool_name(opt), level(opt: basic|intermediate|advanced)",
            "get_system_info":     "OS, node, release, Python version.",
            "get_environment_info":"Environment variables and PATH.",
            "get_security_info":   "Current user and permissions.",
            "get_hardware_info":   "CPU count and total RAM (via psutil).",
            "get_software_info":   "Python version and loaded module count.",
            "get_time_info":       "Local and UTC time with timezone.",
            "get_locale_info":     "System language and encoding.",
            "get_user_info":       "Username and home directory.",
            "get_session_info":    "Process ID and hostname.",
            "get_service_status":  "Check availability of system services.",
            "get_log_info":        "Access system logs (if permitted).",
        },
        "examples": {
            "basic":        "host_ops(operation='get_system_info')",
            "intermediate": "host_ops(operation='get_help', category='filesystem', level='intermediate')",
        },
    },
    "agentic_file_workflow": {
        "category": "sampling",
        "description": "LLM-orchestrated file workflows using ctx.sample() (no sampling.tools — Claude Desktop compatible).",
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
            "Does NOT require sampling.tools capability — uses no-tools sampling pattern.",
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
    "repository": [
        "repo_ops",
        "git_create_branch",
        "git_rename_branch",
        "git_switch_branch",
        "git_merge_branch",
        "git_delete_branch",
        "git_list_branches",
        "git_create_tag",
        "git_list_tags",
        "git_delete_tag",
        "git_push_changes",
        "git_pull_changes",
        "git_fetch_updates",
        "git_list_remotes",
        "git_add_remote",
        "git_remove_remote",
        "git_stash_changes",
        "git_apply_stash",
        "git_list_stashes",
        "git_resolve_conflicts",
        "git_rebase_branch",
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

    Operations: get_help, get_system_info, get_environment_info, get_security_info,
    get_hardware_info, get_software_info, get_time_info, get_locale_info,
    get_user_info, get_session_info, get_service_status, get_log_info.

    Args:
        operation: Operation to perform (required)
        category: Help category filter for get_help
        tool_name: Specific tool name for get_help
        level: Help detail level (basic, advanced). Default: "basic"
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
            return _error_response(
                f"Unknown operation: {operation}", "unsupported_operation"
            )
    except Exception as e:
        logger.error(f"Host context operation '{operation}' failed: {e}", exc_info=True)
        return _error_response(str(e), "internal_error")


# ── Help implementation ────────────────────────────────────────────────────────

async def _get_help(category, tool_name, level):
    try:
        # ── tool_name drill-down ───────────────────────────────────────────────
        if tool_name:
            tool_key = tool_name.lower().strip()
            info = _TOOL_HELP.get(tool_key)
            if not info:
                return _error_response(
                    f"Unknown tool: {tool_name!r}. "
                    f"Valid tools: {', '.join(sorted(_TOOL_HELP))}",
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
                    ["basic"] if level == "basic"
                    else ["basic", "intermediate"] if level == "intermediate"
                    else list(info["examples"].keys())
                )
                result["examples"] = {
                    k: v for k, v in info["examples"].items() if k in example_levels
                }
            return _success_response(result)

        # ── category drill-down ────────────────────────────────────────────────
        if category:
            cat_key = category.lower().strip()
            if cat_key not in _CATEGORIES:
                return _error_response(
                    f"Unknown category: {category!r}. "
                    f"Valid categories: {', '.join(sorted(_CATEGORIES))}",
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
        filtered = {
            k: ("***" if any(s in k.lower() for s in sensitive) else v)
            for k, v in env.items()
        }
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
