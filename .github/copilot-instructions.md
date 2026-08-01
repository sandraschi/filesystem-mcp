# Session Context (Filesystem MCP)

You have access to Filesystem MCP: 24 tools for file operations, Docker containers,
and system monitoring.

**Before starting work:**
1. Check system status: `monitor_get_system_status(include_processes=False)`
2. Explore relevant directories: `dir_ops(operation="list_directory", path="D:/Dev/repos")`

**At end of work, clean up:**
- Close long-running containers you started, verify locks with `get_lock_status()`
- Prefer atomic writes through `file_ops(operation="write_file")` over raw file APIs
