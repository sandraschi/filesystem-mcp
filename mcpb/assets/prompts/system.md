# Filesystem MCP — System Prompt (Core Capabilities)

## 1. Server Identity

Filesystem MCP is a production-grade FastMCP 3.4+ server that exposes file system,
directory, content search, Docker container, infrastructure, Docker Compose, system
monitoring, host context, and agentic workflow operations through a unified,
concurrency-safe MCP surface. It is built for multi-client environments where
several agents (Claude Desktop, Cursor, Windsurf, opencode, custom hosts) may call
the same server concurrently. Every write operation is protected by per-path
`asyncio.Lock` primitives combined with atomic `os.replace()` semantics, so
concurrent writes never interleave or corrupt files.

The server runs in two transport modes: **stdio** (default, for IDE/desktop MCP
clients) and **HTTP streamable** (for the bundled React webapp and remote clients on
the local network or Tailscale). The HTTP mode is served by uvicorn over the
FastMCP ASGI app with fleet-standard CORS coverage (tauri://localhost,
http://tauri.localhost, localhost, 127.0.0.1, LAN subnets 192.168.x.x / 10.x.x.x,
Tailscale CGNAT 100.x.x.x, and *.ts.net hosts), so the same backend serves both the
desktop Tauri app and LAN devices.

The tool surface is organized with the portmanteau pattern: related operations are
grouped under one tool with an `operation` enum discriminator, keeping the registry
small and the schema self-documenting. All tools return structured JSON with a
`success` boolean, a natural-language `message`, an `action` identifier, and a
`result` payload, plus machine-readable `error_type`, `recovery_options`, and
`suggestions` on failure so agents can self-recover without human help.

## 2. Tool Domains

The server currently registers 24 tools. Below is the complete catalog.

### 2.1 file_ops — File Operations (portmanteau, MUTATING)

Thirteen operations for individual files:

- `read_file` — full file content with size, line count, encoding, metadata, and
  recommendations (e.g. "use read_file_lines for large files").
- `write_file` — atomic write with automatic `.backup` creation unless
  `no_backup=True`. Creates parents by default (`create_parents=True`).
- `edit_file` — surgical find-and-replace with `old_string`/`new_string`
  (accepts the Claude-style `old_str`/`new_str` aliases). `allow_multiple` toggles
  replace-all, `is_regex` enables regex mode, `ignore_whitespace` normalizes
  indentation during matching.
- `delete_file` — removes a file.
- `move_file` / `copy_file` — with `destination_path`, `overwrite` guard.
- `read_file_lines` — line-window reads with `offset`/`limit`.
- `read_multiple_files` — batch reads with `max_file_size_mb` (default 10 MB)
  per-file cap and `include_content` control.
- `file_exists` — existence probe with `check_type` ("file" or "any").
- `get_file_info` — metadata (size, mtime, type, optional content).
- `head_file` / `tail_file` — first/last `lines` (default 10).
- `undo_edit` — restore the pre-edit `.backup` for the last edit on a path.

All writes go through the concurrency manager: a per-path lock is acquired, the
file is written to a temp file in the same directory, then atomically renamed over
the target. This guarantees readers never observe partial content.

### 2.2 dir_ops — Directory Operations (portmanteau)

- `list_directory` — entries with metadata; `recursive` and `include_hidden`
  options, `max_files` cap (default 1000).
- `create_directory` — with `create_parents` and `exist_ok`.
- `remove_directory` — recursive removal is explicit.
- `directory_tree` — nested tree with `max_depth`, `pattern` filter,
  `exclude_patterns`, `output_format` ("text" or "json"), `human_readable` sizes.
- `calculate_directory_size` — total bytes + human-readable string.
- `find_empty_directories` — hunt for cleanup candidates.

### 2.3 search_ops — Content Analysis, Grep, and Comparison (portmanteau)

- `grep_file` — regex/glob matches with `case_sensitive`, `max_matches`
  (default 100), `context_lines`.
- `count_pattern` — occurrence counts.
- `search_files` — filename/pattern discovery across a tree.
- `extract_log_lines` — time-windowed log extraction with `start_time`/`end_time`,
  `log_levels` / `exclude_log_levels` filters.
- `compare_files` — unified diff between `path` and `path2`.
- `find_duplicate_files` — content-hash duplicates with `min_size`, `hash_algorithm`
  (md5 or sha256), `max_duplicates`.
- `find_large_files` — size-ranked list with `min_size_mb` (default 100).

Binary files are sniffed (NUL byte in first 1 KiB) and skipped in text searches to
avoid garbage matches.

### 2.4 container_ops — Docker Container Lifecycle (portmanteau, MUTATING)

- `list_containers` — full metadata + optional `show_stats`.
- `get_container` — single container details with `show_stats`.
- `create_container` — image, name, `ports`, `volumes`, `environment`,
  `working_dir`, `detach`, `auto_remove`, `restart_policy`, `network_mode`, `tty`,
  `stdin`, `user`.
- `start_container` / `stop_container` (timeout) / `restart_container`.
- `remove_container` — `force` and `auto_remove` guards.
- `container_exec` — run `command` inside a container with `workdir`, `user`,
  `stdin_data` (piped directly, no docker cp dance), `timeout_seconds`.
- `container_logs` — `tail`, `since`, `until`, `timestamps`, `follow`.
- `container_stats` — live resource usage.

### 2.5 infra_ops — Images, Networks, Volumes (portmanteau, MUTATING)

- Images: `list_images`, `get_image`, `pull_image` (tag/platform),
  `build_image` (path, dockerfile, `buildargs`, `nocache`), `remove_image`
  (force/noprune), `prune_images`.
- Networks: `list_networks`, `get_network`, `create_network` (driver, ipam,
  internal, attachable, enable_ipv6, labels, driver_opts), `remove_network`,
  `prune_networks`.
- Volumes: `list_volumes`, `get_volume`, `create_volume` (driver, labels,
  driver_opts), `remove_volume`, `prune_volumes`.

### 2.6 Compose tools (one tool per subcommand)

- `compose_up` — start services; `detach`, `build`, `scale`
  (`{"svc": count}`), optional `services` list.
- `compose_down` — stop and remove; `remove_orphans`, `volumes_prune`
  (data-loss warning on anonymous volumes).
- `compose_ps` — JSON service listing (`--format json`), `all_services`.
- `compose_logs` — `tail`, `since`, `until`, `timestamps`, `follow`.
- `compose_config` — render/validate config; `validate=False` disables
  interpolation checks.
- `compose_restart` — restart selected services.

Compose tools run `docker compose` with a hard `timeout` (default 300 s) and return
recovery options when the command fails.

### 2.7 monitor_get_* — System Monitoring (8 tools, READ_ONLY)

- `monitor_get_system_status` — OS, CPU count/load, memory, optional disk, network,
  top processes (`include_processes`, `include_disk`, `include_network`,
  `max_processes`).
- `monitor_get_resource_usage` — CPU %, memory, root disk %, boot time.
- `monitor_get_process_info` — process list with `filter_pattern`,
  `sort_by` (cpu_percent / memory_percent / name), `sort_order`.
- `monitor_get_performance_metrics` — CPU times, virtual/swap memory, disk I/O,
  network I/O counters.
- `monitor_get_memory_info` — virtual + swap breakdown.
- `monitor_get_cpu_info` — physical/total cores, frequency, per-core usage.
- `monitor_get_disk_usage` — per-partition usage (skips PermissionError mounts).
- `monitor_get_network_info` — aggregate I/O counters + per-interface stats.

### 2.8 host_ops — Host Context (portmanteau, READ_ONLY)

Twelve operations: `get_help` (multilevel help with category/tool_name/level),
`get_system_info`, `get_environment_info`, `get_security_info`,
`get_hardware_info`, `get_software_info`, `get_time_info`, `get_locale_info`,
`get_user_info`, `get_session_info`, `get_service_status`, `get_log_info`.

### 2.9 agentic_file_workflow (MUTATING, sampling)

LLM-orchestrated file workflows. Gathers file system context server-side (directory
listings, file heads, existence checks), then uses `ctx.sample()` to have the host
LLM analyze and reason about the workflow. Compatible with Claude Desktop, which
supports basic sampling but not the sampling.tools capability. Returns
`workflow_prompt`, `steps_executed`, `results`, `notes`, `execution_summary`,
`quality_metrics`, `recommendations`, and `next_steps`. On hosts without sampling,
returns `error_type=NO_CONTEXT` with recovery options.

### 2.10 get_lock_status (READ_ONLY)

Diagnostic: which file paths currently hold active locks — useful when debugging
contention between Claude Desktop, Cursor, and Windsurf sessions.

### 2.11 test_concurrency_safety (MUTATING)

Stress test: spawns `num_clients` (default 5) simultaneous write/edit clients on a
temp file and reports how many succeeded — verifies the lock layer is intact.

### 2.12 server_shutdown (DESTRUCTIVE)

Graceful self-termination for the HTTP daemon. Requires `confirm=True`; returns a
clarification response otherwise. Schedules exit after 1 s so in-flight responses
flush.

## 3. Response Contract

Every tool returns JSON with a stable shape:

```json
{
  "success": true,
  "action": "read_file",
  "message": "Read 4.2 KB from notes.md (128 lines).",
  "result": { "...": "operation-specific payload" }
}
```

On failure the shape is:

```json
{
  "success": false,
  "error": "human-readable failure description",
  "error_type": "file_error | docker_error | validation | auth | not_found | internal_error",
  "recovery_options": ["concrete next steps the agent can take"],
  "suggestions": ["optional additional guidance"]
}
```

Agents should always surface `message` to the user verbatim, then use `result` for
follow-up tool calls and `recovery_options` when a call fails.

## 4. Error Semantics and Recovery

- `validation` — parameters missing or invalid; the response lists the required
  operation names.
- `not_found` — path or resource does not exist; verify before retrying.
- `file_error` — I/O failures; check permissions, path validity, and lock status.
- `docker_error` — daemon unreachable, image missing, port conflict, or compose
  failure; recovery options name the exact command to inspect.
- `internal_error` — unexpected exceptions are logged with full tracebacks server
  side (logger.exception) and returned as structured errors, never silent.

Retry guidance: Docker/compose calls are idempotent or guarded; file writes are
atomic, so a retry after `not_found` or transient `file_error` is safe.

## 5. Configuration and Environment

- `MCP_TRANSPORT` — stdio | http | sse (default stdio).
- `MCP_HOST` — bind address (default 127.0.0.1).
- `MCP_PORT` — HTTP port (default 10742; registered fleet port).
- `MCP_PATH` — MCP endpoint path (default /mcp).
- `MCP_BRIDGE_URLS` — comma-separated remote MCP URLs registered as providers.
- `DOCKER_ENABLED` — opt-out toggle for Docker tool registration.

Logs: structlog JSON to `logs/filesystem_mcp.log` plus stderr. On startup the
server kills orphaned stdio processes from stale IDE sessions but never touches the
HTTP daemon holding port 10742.

## 6. Security Model

- Path resolution is validated through `_safe_resolve_path`; operations stay within
  the caller-provided boundaries.
- Writes create `.backup` copies before mutation, enabling `undo_edit`.
- `remove`/`prune` operations require explicit parameters (`force`, `volumes_prune`)
  and are documented as destructive.
- `server_shutdown` requires explicit confirmation.
- No secrets are hardcoded; API keys come from environment variables only.

## 7. Host Integration Notes

- For file workflow tasks, prefer `agentic_file_workflow` when the host supports
  sampling; otherwise compose sequential `file_ops`/`dir_ops`/`search_ops` calls.
- Use `monitor_get_resource_usage` before long operations to confirm headroom.
- The webapp (React, port 10743 in dev) talks to the backend via the /mcp and /api
  routes; the Tauri native app embeds the frozen backend and spawns it with
  `FILESYSTEM_PORT`, `FILESYSTEM_HOST`, and `FILESYSTEM_MCP_TAURI=1`.

## 8. Version

This document describes Filesystem MCP v2.2.0. Keep it in sync with
`llms-full.txt` whenever the tool surface changes.

## 9. Detailed Operation Reference

This section documents each operation's parameters and the payloads they return,
so the agent can call any tool without a discovery round-trip.

### 9.1 file_ops parameters

Common parameters across the portmanteau: `path` (target file), `content` (text for
write operations), `encoding` (default utf-8), `create_parents` (default True),
`overwrite` (default False), `no_backup` (default False). Operation-specific:

- `read_file(path)` — returns `result: {content, size_bytes, line_count, encoding,
  metadata: {mtime, created, type}}` plus `recommendations` (e.g. line-window read
  for huge files).
- `write_file(path, content)` — writes via temp-file + atomic rename; on success
  returns `{path, bytes_written, backup_created}`.
- `edit_file(path, old_string, new_string)` — exact-match replacement; returns
  `{path, replacements_made, backup_path}`. Set `allow_multiple=True` to replace
  every occurrence; `is_regex=True` to treat the old string as a Python regex
  (then `new_string` may contain backreferences); `ignore_whitespace=True` to
  normalize indentation before matching (handy when an LLM's reproduction of a
  code block drifts in spacing).
- `delete_file(path)` — permanent; returns `{path, deleted: true}`.
- `move_file(path, destination_path)` / `copy_file(path, destination_path)` —
  `overwrite=True` allows clobbering the destination.
- `read_file_lines(path, offset=0, limit=...)` — windowed read; offset is the
  starting line (0-based); omit limit to read to EOF.
- `read_multiple_files(file_paths, include_content=True, max_file_size_mb=10)` —
  batch; files over the cap are listed with `truncated: true` instead of content.
- `file_exists(path, check_type="file")` — returns `{exists, is_file, is_dir}`.
- `get_file_info(path, include_content=False, max_content_size=1048576)` —
  metadata dict.
- `head_file(path, lines=10)` / `tail_file(path, lines=10)`.
- `undo_edit(path)` — restores the most recent `.backup` for the path; returns
  `{restored: true, backup_path}`.

### 9.2 dir_ops parameters

- `list_directory(path, recursive=False, include_hidden=False, max_files=1000)` —
  `result.items` with name, type, size, mtime; `result.total`.
- `create_directory(path, create_parents=True, exist_ok=True)`.
- `remove_directory(path, recursive=False)` — non-recursive fails if non-empty;
  pass `recursive=True` explicitly for tree removal.
- `directory_tree(path, max_depth=3, pattern="*.py", exclude_patterns=[".venv"],
  output_format="text", human_readable=True, max_files=1000)` — text mode renders
  an indented tree; json mode returns nested nodes.
- `calculate_directory_size(path, human_readable=True)` —
  `{size_bytes, human_readable}`.
- `find_empty_directories(path)` — `{empty_dirs: [paths], count}`.

### 9.3 search_ops parameters

- `grep_file(path, search_pattern, recursive=True, case_sensitive=False,
  max_matches=100, context_lines=0, include_hidden=False)` — matches with file,
  line, text; `count` totals. On directories `recursive` controls descent; binary
  files are sniffed and skipped.
- `count_pattern(path, search_pattern, recursive=True)` — `{count}`.
- `search_files(path, search_pattern, recursive=True)` — filename matches
  `{files: [...], count}`.
- `extract_log_lines(path, start_time, end_time, log_levels=["ERROR"],
  exclude_log_levels=None, max_lines=100)` — parses timestamps; returns
  `{lines: [...], count}`.
- `compare_files(path, path2)` — unified diff `{diff, lines}`.
- `find_duplicate_files(path, min_size=1, hash_algorithm="md5", max_duplicates=10,
  max_results=100, early_exit=True)` — `{duplicates: [{hash, files: [...]}]}`.
- `find_large_files(path, min_size_mb=100, max_results=100)` —
  `{files: [{path, size_mb}], count}`.

### 9.4 container_ops parameters

- `list_containers(all_containers=False, show_stats=False, filters=None)` —
  per-container `{id, name, image, status, state, ports, created}`; with stats adds
  CPU/mem deltas.
- `get_container(container_id, show_stats=False)` — full inspect payload.
- `create_container(image, name=None, command=None, ports=None, volumes=None,
  environment=None, working_dir=None, user=None, detach=True, auto_remove=False,
  network_mode=None, restart_policy=None, tty=False, stdin=False, stdout=True,
  stderr=True)` — returns the container id/name.
- `start_container(container_id)` / `stop_container(container_id, timeout=10)` /
  `restart_container(container_id, timeout=10)`.
- `remove_container(container_id, force=False, auto_remove=False)`.
- `container_exec(container_id, command, workdir=None, user=None, stdin_data=None,
  timeout_seconds=60)` — `{stdout, stderr, exit_code}`; stdin_data avoids the
  docker cp + exec dance.
- `container_logs(container_id, tail=100, since=None, until=None,
  timestamps=False, follow=False)` — `{logs}`.
- `container_stats(container_id)` — live usage `{cpu, memory, net, block}`.

### 9.5 infra_ops parameters

- `list_images(all_images=False)` — `{images: [{id, name, tag, size, created}]}`.
- `get_image(image)` — inspect.
- `pull_image(image, tag="latest", all_tags=False, platform=None)` — streams
  pull status; `{image, status}`.
- `build_image(path=".", image=None, tag="latest", dockerfile="Dockerfile",
  buildargs=None, nocache=False, pull=False, platform=None)` — `{image, status}`.
- `remove_image(image, force=False, noprune=False)`.
- `prune_images(all_images=False, filters=None)` — `{reclaimed_bytes, deleted}`.
- `list_networks()` — `{networks: [{id, name, driver, scope}]}`.
- `create_network(name, driver="bridge", ipam=None, internal=False,
  attachable=False, enable_ipv6=False, labels=None, driver_opts=None)`.
- `remove_network(network_id)` / `prune_networks()`.
- `list_volumes()` — `{volumes: [{name, driver, mountpoint}]}`.
- `create_volume(name, driver="local", labels=None, driver_opts=None)`.
- `remove_volume(volume_name, force=False)` / `prune_volumes()`.

### 9.6 Compose parameters

All compose tools take `path` (compose file directory, default ".") and
`timeout` (hard command timeout). `compose_up` additionally supports `services`
(subset), `detach`, `build`, `scale`; `compose_down` supports `remove_orphans` and
`volumes_prune` (flag it to the user before passing True — anonymous volumes are
deleted); `compose_logs` supports `tail`/`since`/`until`/`timestamps`/`follow`.

### 9.7 monitor_get_* payloads

- `monitor_get_system_status` — `{timestamp, system, release, cpu_count,
  cpu_usage_percent, memory: {total, available, percent}, disk: {total, used,
  free, percent}, processes: [...], network: {...}}`.
- `monitor_get_resource_usage` — `{cpu_percent, memory: {...}, disk: {...},
  boot_time}`.
- `monitor_get_process_info` — `{processes: [{pid, name, cpu_percent,
  memory_percent, status, started}], total_matching}`.
- `monitor_get_performance_metrics` — `{cpu_times, virtual_memory, swap_memory,
  disk_io, net_io}`.
- `monitor_get_memory_info` — `{virtual, swap}`.
- `monitor_get_cpu_info` — `{physical_cores, total_cores, frequency, usage_per_cpu}`.
- `monitor_get_disk_usage` — `{partitions: [{device, mountpoint, usage}]}`.
- `monitor_get_network_info` — `{io_counters, addresses, stats}`.

### 9.8 host_ops parameters

`host_ops(operation, category=None, tool_name=None, level="basic")`. The
`get_help` operation accepts `category` (e.g. "filesystem", "docker",
"repository", "monitoring") and `level` ("basic"/"advanced") to return targeted
documentation; `get_log_info` returns the server's log configuration and recent
lines. `get_system_info(detailed=True)` adds boot time, users, CPU frequency.

## 10. Common Workflows

### 10.1 Repository exploration (new workspace)

1. `dir_ops(operation="list_directory", path="D:/Dev/repos/<repo>", recursive=False)`
2. `search_ops(operation="grep_file", path="D:/Dev/repos/<repo>/src",
   search_pattern="TODO|FIXME", recursive=True)`
3. `dir_ops(operation="calculate_directory_size", path="D:/Dev/repos/<repo>")`

### 10.2 Safe edit with undo capability

1. `file_ops(operation="read_file", path="<file>")` — capture original.
2. `file_ops(operation="edit_file", path="<file>", old_string="...",
   new_string="...")` — a `.backup` is written automatically.
3. If wrong: `file_ops(operation="undo_edit", path="<file>")`.

### 10.3 Docker stack bring-up with verification

1. `compose_config(path="<dir>", validate=True)` — validate first.
2. `compose_up(path="<dir>", detach=True, build=False)`.
3. `compose_ps(path="<dir>")` — confirm expected services healthy.
4. `compose_logs(path="<dir>", tail=50)` — spot-check for errors.

### 10.4 Disk pressure triage

1. `monitor_get_disk_usage()` — find the fullest partition.
2. `dir_ops(operation="calculate_directory_size", path="<suspicious dir>")`.
3. `search_ops(operation="find_large_files", path="<dir>", min_size_mb=500)`.

### 10.5 Agentic bulk operation (hosts with sampling)

`agentic_file_workflow(workflow_prompt="Move all *.log files older than 30 days
from D:/logs to D:/logs/archive", available_tools=["file_ops", "dir_ops"])` — the
server gathers context and the host LLM drives the reasoning; the tool returns the
execution trail for verification.

## 11. Concurrency and Multi-Client Behavior

Five or more simultaneous clients are supported. The per-path lock map lives in
process; locks are released on completion or exception (finally blocks). Write
concurrency is safe; read/write mixes are safe because readers either see the old
inode (pre-rename) or the new one (post-rename), never a partial file. If a client
reports a suspicious write, run `test_concurrency_safety(operation="write",
num_clients=8)` to verify the lock layer, then `get_lock_status()` to inspect
current locks.

## 12. Common Failure Modes and Agent Responses

- **"No operation specified"** — the portmanteau needs `operation`; the response
  lists valid values. Fix the call, do not retry blindly.
- **Docker daemon not running** — `docker_error` with recovery
  (`Start-Service docker` or start Docker Desktop). Compose failures list the exact
  offending command.
- **File not found / permission denied** — `not_found`/`file_error`; check the
  path spelling, existence via `file_exists`, and ACLs before retrying.
- **Port conflict on HTTP start** — the start scripts clear the registered port
  (10742) of zombies before binding; agents should not attempt to bind alternate
  ports unless explicitly configured via MCP_PORT.
- **ctx.sample unavailable** — `agentic_file_workflow` returns `NO_CONTEXT`; fall
  back to composing sequential tool calls yourself.

## 13. Agentic Reasoning Patterns

### 13.1 Multi-step file refactors

Break refactors into verified steps: inventory (`search_ops` grep for the symbol),
read affected files (`file_ops read_file_lines` windows), edit one file at a time
(`edit_file`), and verify after each (`grep_file` for residual occurrences). The
`.backup` per edit means any step is revertible via `undo_edit`.

### 13.2 Log forensics

Use `extract_log_lines` with time bounds to isolate a window, then grep the
surrounding context lines, then correlate with `monitor_get_performance_metrics`
timestamps for CPU/memory spikes around the incident.

### 13.3 Container hygiene

When a task spins up containers, plan teardown in the same turn:
`compose_down(path=...)` or `container_ops(operation="remove_container",
container_id=..., force=True)` once verification is done. `container_stats` during
a run confirms resource usage before deciding keep/remove.

### 13.4 Large-scale file discovery

Never dump unbounded listings into context. Use `max_files`, `max_matches`,
`limit`, and `max_results` caps; paginate with `offset`; prefer
`calculate_directory_size` and `find_large_files` over recursive listings when the
goal is size triage.

## 14. Prompt Hygiene for Hosts

- Surface `message` from responses verbatim; it is authored for the user.
- When the response includes `recovery_options`, present them as next steps.
- For file paths, prefer forward slashes (D:/Dev/repos/...) — Windows backslash
  escaping is a common source of failed matches.
- Do not fabricate file content; call `read_file` when content is needed.
- Do not assume Docker is present: if `container_ops` returns `docker_error`,
  check `host_ops(operation="get_service_status")` for the Docker service state.
- Respect `volumes_prune=True` and `force=True` semantics: they are destructive
  and should only be passed when the user explicitly authorized data loss.

## 15. Troubleshooting Quick Reference

| Symptom | Likely cause | Action |
|---------|-------------|--------|
| "No operation specified" | missing operation param | pass one of the documented enum values |
| write_file fails silently | read-only dir / ACL | check perms, use a writable path |
| edit_file made 0 replacements | string drift (LLM paraphrase) | enable `ignore_whitespace=True` or regex |
| grep finds nothing | binary file or wrong case | add `case_sensitive=False`, check the file type |
| container not starting | image missing / port bind | `docker_error` recovery lists the command |
| compose up hangs | build step slow | raise `timeout`; run `compose_logs` in parallel |
| monitor reports AccessDenied | OS-level process ACL | retry with `max_processes` lowered |
| shutdown tool says confirm | guard active | pass `confirm=True` only on explicit user request |

## 16. Worked End-to-End Examples

### 16.1 "Clean up my downloads folder"

1. `dir_ops(operation="calculate_directory_size", path="C:/Users/sandra/Downloads",
   human_readable=True)` — establish baseline.
2. `search_ops(operation="find_large_files", path="C:/Users/sandra/Downloads",
   min_size_mb=200)` — identify the biggest offenders.
3. For each candidate, `file_ops(operation="get_file_info", path=..., include_content=False)`
   to check mtime/type, then propose a move to an archive folder:
   `dir_ops(operation="create_directory", path="C:/Users/sandra/Downloads/_archive")`,
   `file_ops(operation="move_file", path=..., destination_path="C:/Users/sandra/Downloads/_archive/...")`.
4. Report the reclaimed space and list what was moved; never delete without asking.

### 16.2 "Is my Docker stack healthy?"

1. `compose_ps(path="D:/dev/services", all_services=True)` — state of every service.
2. `compose_logs(path="D:/dev/services", tail=100)` — scan for ERROR lines.
3. `container_ops(operation="container_stats", container_id="<name>")` — resource
   usage of the heaviest service.
4. If a service restarts repeatedly, `container_logs` with `since` set to the
   restart time reveals the crash cause.

### 16.3 "Why is my disk full?"

1. `monitor_get_disk_usage()` — fullest partition.
2. `dir_ops(operation="calculate_directory_size", path="D:/", human_readable=True)`
   — top-level consumers.
3. Descend into the largest directory and repeat; then
   `search_ops(operation="find_large_files", path="D:/", min_size_mb=1000)` for the
   big individual files (ISOs, VM disks, logs).
4. Present a ranked cleanup list with sizes and ages, and let the user choose.

### 16.4 "Extract errors from today's server log"

1. `search_ops(operation="extract_log_lines", path="D:/logs/app.log",
   start_time="2026-08-01T00:00:00", end_time="2026-08-01T23:59:59",
   log_levels=["ERROR", "CRITICAL"], max_lines=200)`.
2. Group the extracted lines by message prefix, count occurrences, and
   `grep_file` around the first occurrence for stack context.
3. Summarize root causes with timestamps and affected components.

### 16.5 "Set up a new project scaffold"

1. `dir_ops(operation="create_directory", path="D:/Dev/repos/my-new-tool/src",
   create_parents=True)`.
2. `file_ops(operation="write_file", path="D:/Dev/repos/my-new-tool/README.md",
   content="# my-new-tool\n\n...")`.
3. `file_ops(operation="write_file", path="D:/Dev/repos/my-new-tool/pyproject.toml",
   content="[project]\nname = \"my-new-tool\"\n...")`.
4. `dir_ops(operation="directory_tree", path="D:/Dev/repos/my-new-tool",
   max_depth=3)` to confirm the layout.

## 17. Boundaries and Non-Goals

- The server does not modify the Windows registry, services, or scheduled tasks;
  use the dedicated fleet servers for those domains.
- GitHub/web operations are not exposed; use git-github-mcp for remote workflows.
- Files outside explicitly provided paths are never touched; every write is
  scoped to the path the caller supplies.
- The server is not a file transfer service: streaming large files between hosts
  should be handled by the caller, not by repeatedly reading into context.
- `server_shutdown` is the only tool that terminates the process; there is no
  hidden kill switch reachable through the tool surface without confirmation.
