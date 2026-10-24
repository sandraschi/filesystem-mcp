# Filesystem MCP Tools List

**Date:** 2026-10-24
**Status:** Actual tools available in this repo (portmanteau pattern: one tool,
many operations via the `operation` enum)

Canonical references: `docs/TOOLS.md`, `assets/prompts/system.md` (§2),
live `GET /api/capabilities`.

## file_ops (files, MUTATING)

read_file, write_file, edit_file, delete_file, move_file, copy_file,
read_file_lines, read_multiple_files, file_exists, get_file_info, head_file,
tail_file, undo_edit, get_file_hash, append_file, touch_file, compress, decompress

## dir_ops (directories, MUTATING)

list_directory, create_directory, remove_directory, directory_tree,
calculate_directory_size, find_empty_directories, copy_tree, move_directory

## search_ops (search + code intel, READ_ONLY)

grep_file, count_pattern, search_files, extract_log_lines, compare_files,
find_duplicate_files, find_large_files, find_todos, find_symbols,
validate_json, analyze_project, run_linter (ruff-only), validate_config

## Docker (deprecated — docker-mcp owns this surface)

container_ops, infra_ops, compose_up, compose_down, compose_ps,
compose_logs, compose_config, compose_restart

## Monitoring + host (READ_ONLY)

monitor_get_system_status, monitor_get_resource_usage, monitor_get_process_info,
monitor_get_performance_metrics, monitor_get_memory_info, monitor_get_cpu_info,
monitor_get_disk_usage, monitor_get_network_info, host_ops (incl. get_help),
agentic_file_workflow, get_lock_status, test_concurrency_safety, server_shutdown

## Not in this repo

- **Git** (`clone_repo`, `repo_ops`, `git_*`) — moved to `git-github-mcp`
  (`gitops:git_core` / `github_ops`). `get_help` for `repo_ops` / `git_*` /
  `category='repository'` returns a `moved` error with the redirect.
- `edit_file_at_line` — not from this repo (Cursor built-in or another server);
  use `edit_file` string replacement instead.
