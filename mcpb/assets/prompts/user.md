# Filesystem MCP User Guide

## Overview

Filesystem MCP is a comprehensive FastMCP 3.4+ server that provides file system operations, Docker container management, Git repository management, and system monitoring through a unified set of tools. Every operation returns structured JSON responses with success status, error messages, and actionable recovery suggestions.

The server exposes 23 tools organised into 4 domains: filesystem (file_ops, dir_ops, search_ops), Docker (container_ops, infra_ops, compose_up/down/ps/logs/config/restart), Git repository (repo_ops, git_create_branch, git_switch_branch, and more), and system monitoring (monitor_get_*, host_ops). Portmanteau tools use an `operation` enum parameter to select the specific action.

---

## 1. File Operations (file_ops)

The `file_ops` portmanteau tool handles all file-level operations: reading, writing, editing, deleting, moving, copying, and metadata inspection. Write operations (write_file, edit_file, move_file, copy_file) use per-path `asyncio.Lock` with atomic `os.replace()` to prevent data corruption under concurrent access from multiple clients.

### 1.1 Reading Files

Use `read_file` to retrieve the full contents of a file:

```
file_ops(operation="read_file", path="D:/Dev/repos/myproject/config.json")
```

Returns: content, size, line count, encoding, file metadata, and recommendations (e.g. "use read_file_lines for large files").

### 1.2 Writing Files

Write content to a new or existing file. Backups are created automatically unless `no_backup=True`:

```
file_ops(operation="write_file", path="D:/Dev/repos/myproject/notes.md", content="# My Notes\nCreated by MCP.")
```

Returns: path, size, encoding, and backup_path if a previous version existed.

### 1.3 Editing Files (Replace Text)

The `edit_file` operation supports single-replacement, regex-based replacement, multi-occurrence replacement, indentation-normalised matching, and atomic batch edits via the `replacements` list parameter:

```
# Simple string replacement
file_ops(operation="edit_file", path="D:/config.json", old_string="version: 1", new_string="version: 2")

# Regex replacement
file_ops(operation="edit_file", path="D:/config.json", old_string=r"debug:\s*(true|false)", new_string="debug: true", is_regex=True)

# Batch multi-chunk edit (atomic)
file_ops(operation="edit_file", path="D:/app.py", replacements=[{"old_string": "foo()", "new_string": "bar()"}, {"old_string": "old_import", "new_string": "new_import"}])
```

Each edit creates a timestamped `.bak` backup. Post-write verification reads back the content and confirms the write was correct. If verification fails, the original file is restored from the backup.

### 1.4 Moving and Copying

```
file_ops(operation="move_file", path="D:/source.txt", destination_path="D:/archive/source.txt", overwrite=False)
file_ops(operation="copy_file", path="D:/source.txt", destination_path="D:/backups/source.txt", overwrite=False)
```

Both operations honour the overwrite flag and create parent directories automatically.

### 1.5 Deleting Files

```
file_ops(operation="delete_file", path="D:/temp/old.log")
```

Permanently removes a file. Returns the file name and size. Use with caution — there is no trash/recycle bin integration.

### 1.6 Reading Specific Lines

```
file_ops(operation="read_file_lines", path="D:/large.log", offset=0, limit=50)
```

Returns only the requested line range. Ideal for large files where loading everything would be wasteful.

### 1.7 Reading Multiple Files

```
file_ops(operation="read_multiple_files", file_paths=["D:/a.py", "D:/b.py", "D:/c.py"], max_file_size_mb=5.0)
```

Batch-reads up to the size limit per file. Results include success/failure per file, with skipped entries for oversized files.

### 1.8 File Existence and Metadata

```
file_ops(operation="file_exists", path="D:/config.json", check_type="file")
file_ops(operation="get_file_info", path="D:/config.json", include_content=True, max_content_size=1048576)
```

`file_exists` returns whether the path exists and matches the expected type (file vs any). `get_file_info` returns size, timestamps (modified/created/accessed), permissions, symlink status, and optionally the file content.

### 1.9 Head and Tail

```
file_ops(operation="head_file", path="D:/large.log", lines=5)
file_ops(operation="tail_file", path="D:/large.log", lines=20)
```

Efficiently reads the first or last N lines without reading the entire file. Tail reads backwards from EOF in blocks for O(N) performance regardless of file size.

### 1.10 Undo Edit

```
file_ops(operation="undo_edit", path="D:/config.json")
```

Reverts the most recent edit by restoring the newest `.bak` backup. Only works if the original edit created a backup (i.e. `no_backup` was not set).

---

## 2. Directory Operations (dir_ops)

The `dir_ops` portmanteau tool handles directory listing, creation, removal, tree visualisation, and size analysis.

### 2.1 List Directory Contents

```
dir_ops(operation="list_directory", path="D:/Dev/repos", recursive=True, include_hidden=True)
```

Returns every file and subdirectory with name, path, type, size, modified timestamp, and permissions. Skips hidden files by default. Respects `max_files` cap (default 1000).

### 2.2 Directory Tree

```
dir_ops(operation="directory_tree", path="D:/Dev/repos/myproject", max_depth=3, pattern="*.py")
```

Generates a visual tree using Unicode box-drawing characters. The `pattern` parameter filters by glob (e.g. only Python files). Useful for understanding project structure at a glance.

### 2.3 Create Directory

```
dir_ops(operation="create_directory", path="D:/Dev/repos/myproject/new_folder", create_parents=True, exist_ok=True)
```

Creates one or more directories. `create_parents=True` ensures intermediate directories are created. `exist_ok=True` silently returns success if the directory already exists.

### 2.4 Remove Directory

```
dir_ops(operation="remove_directory", path="D:/Dev/repos/myproject/old_folder", recursive=False)
```

Removes a directory. Non-recursive removal fails if the directory is not empty. Use `recursive=True` to remove a directory and all its contents — this is destructive and irreversible.

### 2.5 Calculate Directory Size

```
dir_ops(operation="calculate_directory_size", path="D:/Dev/repos/myproject")
```

Walks the entire directory tree and returns total size in bytes (and human-readable format) plus total file count.

### 2.6 Find Empty Directories

```
dir_ops(operation="find_empty_directories", path="D:/Dev/repos/myproject", recursive=True)
```

Scans the directory tree and returns a list of all directories that contain no files or subdirectories.

---

## 3. Search and Content Analysis (search_ops)

The `search_ops` portmanteau tool provides content search (grep), file name pattern matching, log extraction, file comparison, and duplicate detection.

### 3.1 Grep File or Directory

```
search_ops(operation="grep_file", path="D:/Dev/repos/myproject/src", search_pattern="def ", recursive=True, case_sensitive=False, max_matches=50, context_lines=2)
```

Searches text content using regex patterns. When the path is a directory, it recursively searches every text file. Skips binary files, files larger than 5 MB, and common VCS/cache directories (.git, node_modules, __pycache__, .venv, target, dist, etc.). Returns matches with line numbers, matched text, and optional surrounding context.

### 3.2 Count Pattern Occurrences

```
search_ops(operation="count_pattern", path="D:/Dev/repos/myproject/src/server.py", search_pattern="async def")
```

Returns the number of regex matches in a single file without returning the matching lines.

### 3.3 Search Files by Name

```
search_ops(operation="search_files", path="D:/Dev/repos/myproject", search_pattern="*.ts", recursive=True)
```

Finds files whose names match a glob pattern (fnmatch). Returns path, name, size, and modified timestamp for each match.

### 3.4 Extract Log Lines

```
search_ops(operation="extract_log_lines", path="D:/Dev/repos/myproject/server.log", log_levels=["ERROR", "CRITICAL"], start_time="2026-06-01T00:00:00", end_time="2026-06-30T23:59:59", max_lines=100)
```

Filters log files by log level, time range, and optional search patterns. Detects ISO 8601 timestamps and log level keywords (DEBUG, INFO, WARN, WARNING, ERROR, FATAL, CRITICAL, TRACE). Supports both include and exclude pattern lists.

### 3.5 Compare Two Files

```
search_ops(operation="compare_files", path="D:/file1.txt", path2="D:/file2.txt")
```

Performs a unified diff comparison using Python's difflib. Returns whether files are identical, and the full diff output if they differ.

### 3.6 Find Duplicate Files

```
search_ops(operation="find_duplicate_files", path="D:/Dev/repos/myproject", recursive=True, min_size=1024, hash_algorithm="sha256", max_duplicates=10)
```

Finds duplicate files by content hash (MD5 or SHA-256). Skips files smaller than `min_size` bytes. The `max_duplicates` parameter stops scanning once enough duplicate groups have been found.

### 3.7 Find Large Files

```
search_ops(operation="find_large_files", path="D:/Dev/repos/myproject", min_size_mb=50, recursive=True, max_results=20)
```

Locates files above a size threshold. Results are sorted largest first. Useful for cleaning up disk space.

---

## 4. Docker Container Management (container_ops)

The `container_ops` portmanteau tool manages the full lifecycle of Docker containers: listing, creating, starting, stopping, restarting, removing, executing commands, streaming logs, and monitoring resource usage.

### 4.1 List Containers

```
container_ops(operation="list_containers", show_stats=True)
```

Lists all containers (running and stopped) with name, image, status, created timestamp, and port mappings. When `show_stats=True`, includes memory and CPU usage.

### 4.2 Get Container Details

```
container_ops(operation="get_container", container_id="my-app", show_stats=True)
```

Returns full configuration (image, environment variables, network settings, mounts) and optional live resource statistics.

### 4.3 Create Container

```
container_ops(operation="create_container", image="nginx:latest", name="web-server", ports={"80/tcp": 8080}, environment={"NGINX_HOST": "localhost"}, detach=True)
```

Creates a container without starting it. Supports port mappings, volume mounts, environment variables, working directory, network mode, restart policies, and auto-removal on stop.

### 4.4 Start, Stop, Restart

```
container_ops(operation="start_container", container_id="web-server")
container_ops(operation="stop_container", container_id="web-server", timeout=10)
container_ops(operation="restart_container", container_id="web-server", timeout=10)
```

Standard lifecycle operations. The timeout controls the grace period before forced SIGKILL.

### 4.5 Remove Container

```
container_ops(operation="remove_container", container_id="web-server", force=True)
```

Removes a container. The `force` flag kills a running container before removal.

### 4.6 Execute Command

```
container_ops(operation="container_exec", container_id="my-db", command="psql -U admin -c 'SELECT version()'")
```

Runs a command inside a running container. Supports custom working directory, user, environment variables, TTY, and stdin/stdout/stderr streaming.

### 4.7 Container Logs

```
container_ops(operation="container_logs", container_id="web-server", tail=100, timestamps=True, since="2026-06-01T00:00:00")
```

Fetches container logs with optional tail count, since/until time filters, and timestamps.

### 4.8 Container Stats

```
container_ops(operation="container_stats", container_id="web-server")
```

Returns a live snapshot of memory usage, CPU usage, and network I/O for the specified container.

---

## 5. Docker Infrastructure (infra_ops)

The `infra_ops` portmanteau tool manages Docker images, networks, and volumes.

### 5.1 Image Operations

List, inspect, pull, build, and remove Docker images:

```
infra_ops(operation="list_images", all_images=True)
infra_ops(operation="get_image", image="python:3.13-slim")
infra_ops(operation="pull_image", image="python", tag="3.13-slim", platform="linux/amd64")
infra_ops(operation="build_image", path="D:/Dev/repos/myproject", dockerfile="Dockerfile", tag="myapp:latest", nocache=False)
infra_ops(operation="remove_image", image="myapp:latest", force=False)
infra_ops(operation="prune_images")
```

`build_image` returns the image ID and build logs. `prune_images` removes unused dangling images.

### 5.2 Network Operations

```
infra_ops(operation="list_networks")
infra_ops(operation="get_network", network_id="bridge")
infra_ops(operation="create_network", name="my-net", driver="bridge", internal=False, enable_ipv6=False)
infra_ops(operation="remove_network", network_id="my-net")
infra_ops(operation="prune_networks")
```

Network creation supports custom IPAM configuration, labels, and attachable/ingress modes.

### 5.3 Volume Operations

```
infra_ops(operation="list_volumes")
infra_ops(operation="get_volume", volume_name="my-data")
infra_ops(operation="create_volume", volume_name="my-data", driver="local", driver_opts={"type": "nfs"})
infra_ops(operation="remove_volume", volume_name="my-data", force=False)
infra_ops(operation="prune_volumes")
```

Volumes persist data independently of container lifecycles.

---

## 6. Docker Compose (compose_up, compose_down, compose_ps, compose_logs, compose_config, compose_restart)

Docker Compose tools are independent tools (not portmanteau) for managing multi-container applications.

### 6.1 Start Services

```
compose_up(path="D:/Dev/repos/myproject", detach=True, build=False, scale={"web": 3, "worker": 2})
```

Starts Compose services. The `scale` parameter sets service replica counts. `build=True` rebuilds images before starting.

### 6.2 Stop Services

```
compose_down(path="D:/Dev/repos/myproject", remove_orphans=True, volumes_prune=False)
```

Stops and removes containers, networks, and optionally anonymous volumes. The `volumes_prune` flag is destructive — it removes data volumes.

### 6.3 List Services

```
compose_ps(path="D:/Dev/repos/myproject", all_services=True)
```

Lists Compose services as JSON with their status. Use to verify all services are running.

### 6.4 View Logs

```
compose_logs(path="D:/Dev/repos/myproject", tail=50, timestamps=True, since="2026-06-01T00:00:00")
```

Fetches aggregated logs from all (or specified) services.

### 6.5 Validate Configuration

```
compose_config(path="D:/Dev/repos/myproject", validate=True)
```

Renders and validates the Compose file. Fails if there are YAML errors or missing variables.

### 6.6 Restart Services

```
compose_restart(path="D:/Dev/repos/myproject", services=["web", "worker"])
```

Restarts specified services (or all if none specified) without tearing down the stack.

---

## 7. Git Repository Management

Filesystem MCP provides both a portmanteau `repo_ops` tool with 13 operations and individual atomic tools for branch, tag, remote, and stash management.

### 7.1 Repository Operations (repo_ops)

```
# Clone a repository
repo_ops(operation="clone_repo", repo_url="https://github.com/user/repo.git", target_dir="D:/Dev/repos/project")

# Check status
repo_ops(operation="get_repo_status", repo_path="D:/Dev/repos/myproject")

# Commit changes
repo_ops(operation="commit_changes", repo_path="D:/Dev/repos/myproject", message="feat: add new feature", add_all=True)

# View history
repo_ops(operation="get_commit_history", repo_path="D:/Dev/repos/myproject", max_commits=20, author="sandra")

# Show commit details
repo_ops(operation="show_commit", repo_path="D:/Dev/repos/myproject", commit1="abc123")

# Diff changes
repo_ops(operation="diff_changes", repo_path="D:/Dev/repos/myproject", commit1="abc123", commit2="def456")

# Blame a file
repo_ops(operation="blame_file", repo_path="D:/Dev/repos/myproject", file_path="src/server.py")

# File history
repo_ops(operation="get_file_history", repo_path="D:/Dev/repos/myproject", file_path="src/server.py")

# Read repo structure
repo_ops(operation="read_repo", repo_path="D:/Dev/repos/myproject", max_depth=3)

# Revert a commit
repo_ops(operation="revert_commit", repo_path="D:/Dev/repos/myproject", commit1="abc123")

# Reset HEAD
repo_ops(operation="reset_to_commit", repo_path="D:/Dev/repos/myproject", commit1="abc123", force=True)

# Cherry-pick
repo_ops(operation="cherry_pick", repo_path="D:/Dev/repos/myproject", commit1="abc123")
```

### 7.2 Branch Management

Individual atomic tools for branch operations:

```
git_create_branch(repo_path="D:/Dev/repos/myproject", branch_name="feature/new-ui")
git_switch_branch(repo_path="D:/Dev/repos/myproject", branch_name="feature/new-ui")
git_list_branches(repo_path="D:/Dev/repos/myproject")
git_merge_branch(repo_path="D:/Dev/repos/myproject", source_branch="feature/new-ui")
git_delete_branch(repo_path="D:/Dev/repos/myproject", branch_name="feature/new-ui", force_delete=False)
git_rename_branch(repo_path="D:/Dev/repos/myproject", branch_name="old-name", target_branch="new-name")
```

### 7.3 Remote Management

```
git_list_remotes(repo_path="D:/Dev/repos/myproject")
git_add_remote(repo_path="D:/Dev/repos/myproject", remote_name="upstream", remote_url="https://github.com/original/repo.git")
git_remove_remote(repo_path="D:/Dev/repos/myproject", remote_name="old-origin")
git_push_changes(repo_path="D:/Dev/repos/myproject", remote_name="origin", push_branch="main", force_push=False)
git_pull_changes(repo_path="D:/Dev/repos/myproject", remote_name="origin", pull_branch="main")
git_fetch_updates(repo_path="D:/Dev/repos/myproject", remote_name="origin")
```

### 7.4 Stash Management

```
git_stash_changes(repo_path="D:/Dev/repos/myproject", stash_message="WIP: refactoring in progress")
git_list_stashes(repo_path="D:/Dev/repos/myproject")
git_apply_stash(repo_path="D:/Dev/repos/myproject", stash_index=0)
```

### 7.5 Tag Management

```
git_create_tag(repo_path="D:/Dev/repos/myproject", tag_name="v1.0.0", tag_message="Release 1.0.0")
git_list_tags(repo_path="D:/Dev/repos/myproject")
git_delete_tag(repo_path="D:/Dev/repos/myproject", tag_name="v1.0.0")
```

### 7.6 Conflict Resolution

```
git_resolve_conflicts(repo_path="D:/Dev/repos/myproject")
git_rebase_branch(repo_path="D:/Dev/repos/myproject", source_branch="main")
```

---

## 8. System Monitoring

Standalone atomic tools prefixed with `monitor_get_` for reading system metrics.

### 8.1 System Status

```
monitor_get_system_status(include_processes=True, include_disk=True, include_network=True, max_processes=10)
```

Comprehensive snapshot: OS, release, CPU count and usage, memory details, disk usage, top processes by CPU, and network I/O counters.

### 8.2 Resource Usage

```
monitor_get_resource_usage()
```

Quick view of CPU percentage, memory usage, root disk usage, and boot time.

### 8.3 Process Information

```
monitor_get_process_info(max_processes=20, filter_pattern="python", sort_by="cpu_percent", sort_order="desc")
```

Lists running processes with optional name filter (case-insensitive substring match, not regex). Sorts by CPU, memory, or name.

### 8.4 CPU Information

```
monitor_get_cpu_info()
```

Returns physical and logical core counts, CPU frequency, and per-core usage percentages.

### 8.5 Memory Information

```
monitor_get_memory_info()
```

Detailed breakdown of virtual memory (total, available, used, percent) and swap memory.

### 8.6 Disk Usage

```
monitor_get_disk_usage()
```

Per-partition disk usage showing device, mountpoint, total space, used space, free space, and usage percentage. Skips partitions that raise PermissionError.

### 8.7 Network Information

```
monitor_get_network_info()
```

Network I/O counters (bytes sent/received, packets), per-interface addresses and stats.

### 8.8 Performance Metrics

```
monitor_get_performance_metrics()
```

Detailed CPU times, virtual memory, swap, disk I/O, and network I/O counters in a single call.

---

## 9. Host Context (host_ops)

The `host_ops` portmanteau tool provides system information, environment inspection, security context, and help documentation.

### 9.1 System Information

```
host_ops(operation="get_system_info")
host_ops(operation="get_hardware_info")
host_ops(operation="get_software_info")
host_ops(operation="get_time_info")
host_ops(operation="get_locale_info")
```

Returns OS details, CPU/memory specs, Python version, current time (local and UTC), locale settings, and encoding.

### 9.2 Environment and User

```
host_ops(operation="get_environment_info")
host_ops(operation="get_user_info")
host_ops(operation="get_session_info")
host_ops(operation="get_security_info")
```

Environment variables (passwords/tokens masked), current user, home directory, process ID, and security context.

### 9.3 Help System

```
host_ops(operation="get_help")
host_ops(operation="get_help", category="filesystem", level="intermediate")
host_ops(operation="get_help", tool_name="file_ops", level="advanced")
```

Hierarchical documentation system. Returns tool descriptions, operation lists, examples, and usage notes. Levels: basic (overview), intermediate (operations), advanced (examples + notes).

### 9.4 Service Status

```
host_ops(operation="get_service_status")
host_ops(operation="get_log_info")
```

---

## 10. Agentic File Workflow

The `agentic_file_workflow` tool uses FastMCP sampling (ctx.sample) to let the LLM orchestrate multi-step file operations autonomously:

```
agentic_file_workflow(workflow_prompt="Find all Python files in D:/Dev/repos/myproject/src, count total lines of code, and identify files over 500 lines that should be refactored.", available_tools=["file_ops", "search_ops", "dir_ops"])
```

This tool gathers filesystem context server-side, then calls back to the LLM for analysis. Compatible with Claude Desktop and any client that supports basic sampling. Does NOT require the sampling.tools capability.

---

## 11. Concurrency Lock Status

```
get_lock_status()
```

Returns which file paths currently have active write locks. Useful for diagnosing concurrent write contention between multiple connected clients (Claude Desktop, Cursor, opencode simultaneously).
