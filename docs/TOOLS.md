# Tools

Filesystem MCP registers **24 MCP tools** (FastMCP 3.4+). The full catalog with
parameters is maintained in:

- [FILESYSTEM_MCP_TOOLS_LIST.md](../FILESYSTEM_MCP_TOOLS_LIST.md) — detailed per-tool reference
- `GET /api/capabilities` (HTTP) — live tool list
- `assets/prompts/system.md` — authoritative prompt contract (sections 2, 9)

## Catalog Summary

| Tool | Domain | Operations / Notes |
|------|--------|--------------------|
| `file_ops` | Files | read_file, write_file, edit_file, delete_file, move_file, copy_file, read_file_lines, read_multiple_files, file_exists, get_file_info, head_file, tail_file, undo_edit |
| `dir_ops` | Directories | list_directory, create_directory, remove_directory, directory_tree, calculate_directory_size, find_empty_directories |
| `search_ops` | Search | grep_file, count_pattern, search_files, extract_log_lines, compare_files, find_duplicate_files, find_large_files |
| `container_ops` | Docker | list/get/create/start/stop/restart/remove container, container_exec, container_logs, container_stats |
| `infra_ops` | Docker | images, networks, volumes CRUD + prune |
| `compose_up/down/ps/logs/config/restart` | Docker Compose | one tool per subcommand |
| `monitor_get_system_status` | Monitoring | full snapshot |
| `monitor_get_resource_usage` | Monitoring | CPU/mem/disk quick probe |
| `monitor_get_process_info` | Monitoring | process list |
| `monitor_get_performance_metrics` | Monitoring | counters |
| `monitor_get_memory_info` | Monitoring | virtual + swap |
| `monitor_get_cpu_info` | Monitoring | cores + per-core usage |
| `monitor_get_disk_usage` | Monitoring | per-partition |
| `monitor_get_network_info` | Monitoring | interfaces + I/O |
| `host_ops` | Host | get_help, get_system_info, get_environment_info, get_security_info, get_hardware_info, get_software_info, get_time_info, get_locale_info, get_user_info, get_session_info, get_service_status, get_log_info |
| `agentic_file_workflow` | Agentic | LLM-sampling file workflows (ctx.sample) |
| `get_lock_status` | Concurrency | active per-path locks |
| `test_concurrency_safety` | Concurrency | concurrent-write stress test |
| `server_shutdown` | Lifecycle | graceful shutdown (confirm=True) |

## Response Contract

Every tool returns:

```json
{"success": true, "action": "<operation>", "message": "natural-language summary", "result": {...}}
```

Failures: `{"success": false, "error": str, "error_type": str, "recovery_options": [...], "suggestions": [...]}`.

## Tool Annotations

All tools carry FastMCP annotations: `READ_ONLY` (queries, monitoring),
`MUTATING` (writes, docker lifecycle), `DESTRUCTIVE` (server_shutdown).
