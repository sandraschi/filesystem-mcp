# Three Filesystem MCP Servers Comparison

## Overview

| Server | Framework | Focus | Total Tools | Platform |
|--------|-----------|-------|-------------|----------|
| **filesystem-mcp** | FastMCP 2.12 | Comprehensive (Files, Docker, Git, Dev Tools) | ~50+ tools | Cross-platform |
| **mcp-filesystem** | MCP SDK (typer) | Advanced file operations | 23 tools | Cross-platform |
| **windows-operations-mcp** | FastMCP 2.12.3 | Windows system operations | ~50+ tools | **Windows only** |

---

## Detailed Tool Comparison

### File Operations

| Tool | filesystem-mcp | mcp-filesystem | windows-operations-mcp |
|------|----------------|----------------|------------------------|
| `read_file` | ✅ | ✅ | ✅ |
| `write_file` | ✅ | ✅ | ✅ |
| `list_directory` | ✅ | ✅ | ✅ `list_directory_contents` |
| `create_directory` | ✅ | ✅ | ✅ `create_directory_safe` |
| `delete_file` | ❌ | ❌ | ✅ |
| `move_file` | ❌ | ✅ | ✅ |
| `copy_file` | ❌ | ❌ | ✅ |
| `delete_directory` | ✅ | ❌ | ✅ `delete_directory_safe` |
| `move_directory` | ❌ | ❌ | ✅ `move_directory_safe` |
| `copy_directory` | ❌ | ❌ | ✅ `copy_directory_safe` |
| `get_file_info` | ✅ | ✅ | ✅ |
| `head_file` | ✅ | ✅ | ❌ |
| `tail_file` | ✅ | ✅ | ❌ |
| `grep_file` | ✅ | ✅ `grep_files` | ❌ |
| `edit_file` | ✅ | ✅ | ✅ |
| `file_exists` | ✅ | ❌ | ❌ |
| `read_multiple_files` | ❌ | ✅ | ❌ |
| `search_files` | ❌ | ✅ | ❌ |
| `directory_tree` | ❌ | ✅ | ❌ |
| `calculate_directory_size` | ❌ | ✅ | ❌ |
| `find_duplicate_files` | ❌ | ✅ | ❌ |
| `compare_files` | ❌ | ✅ | ❌ |
| `find_large_files` | ❌ | ✅ | ❌ |
| `find_empty_directories` | ❌ | ✅ | ❌ |
| `read_file_lines` | ❌ | ✅ | ❌ |
| `edit_file_at_line` | ❌ | ✅ | ❌ |
| `count_pattern` | ✅ | ❌ | ❌ |
| `extract_log_lines` | ✅ | ❌ | ❌ |
| `remove_directory` | ✅ | ❌ | ❌ |

**File Operations Winner:**
- **Most comprehensive**: `mcp-filesystem` (23 file tools)
- **Best for basic ops**: `filesystem-mcp` (13 tools)
- **Best for Windows**: `windows-operations-mcp` (10 tools with Windows-specific features)

---

### Docker Operations

| Tool | filesystem-mcp | mcp-filesystem | windows-operations-mcp |
|------|----------------|----------------|------------------------|
| **Container Management** | ✅ 10 tools | ❌ | ❌ |
| **Image Management** | ✅ 6 tools | ❌ | ❌ |
| **Network & Volumes** | ✅ 6 tools | ❌ | ❌ |
| **Docker Compose** | ✅ 6 tools | ❌ | ❌ |

**Docker Winner:** `filesystem-mcp` (28 Docker tools) - **Only one with Docker support**

---

### Git Operations

| Tool | filesystem-mcp | mcp-filesystem | windows-operations-mcp |
|------|----------------|----------------|------------------------|
| `clone_repo` | ✅ | ❌ | ❌ |
| `get_repo_status` | ✅ | ❌ | ✅ `git_status` |
| `commit_changes` | ✅ | ❌ | ✅ `git_commit` |
| `list_branches` | ✅ | ❌ | ❌ |
| `read_repo` | ✅ | ❌ | ❌ |
| `git_add` | ❌ | ❌ | ✅ |
| `git_push` | ❌ | ❌ | ✅ |

**Git Winner:** `filesystem-mcp` (5 tools) vs `windows-operations-mcp` (4 tools)

---

### Developer Tools

| Tool | filesystem-mcp | mcp-filesystem | windows-operations-mcp |
|------|----------------|----------------|------------------------|
| **Unified Developer Tool** | ✅ 10 commands | ❌ | ❌ |
| - `analyze_dependencies` | ✅ | ❌ | ❌ |
| - `analyze_imports` | ✅ | ❌ | ❌ |
| - `analyze_project` | ✅ | ❌ | ❌ |
| - `check_file_sizes` | ✅ | ❌ | ❌ |
| - `detect_duplicates` | ✅ | ❌ | ❌ |
| - `find_symbols` | ✅ | ❌ | ❌ |
| - `find_todos` | ✅ | ❌ | ❌ |
| - `run_linter` | ✅ | ❌ | ❌ |
| - `validate_config` | ✅ | ❌ | ❌ |
| - `validate_json` | ✅ | ❌ | ❌ |

**Developer Tools Winner:** `filesystem-mcp` (10 developer tools) - **Only one with developer tools**

---

### Windows-Specific Operations

| Tool | filesystem-mcp | mcp-filesystem | windows-operations-mcp |
|------|----------------|----------------|------------------------|
| **Windows Services** | ❌ | ❌ | ✅ 4 tools |
| - `list_windows_services` | ❌ | ❌ | ✅ |
| - `start_windows_service` | ❌ | ❌ | ✅ |
| - `stop_windows_service` | ❌ | ❌ | ✅ |
| - `restart_windows_service` | ❌ | ❌ | ✅ |
| **Windows Event Logs** | ❌ | ❌ | ✅ 4 tools |
| - `query_windows_event_log` | ❌ | ❌ | ✅ |
| - `export_windows_event_log` | ❌ | ❌ | ✅ |
| - `clear_windows_event_log` | ❌ | ❌ | ✅ |
| - `monitor_windows_event_log` | ❌ | ❌ | ✅ |
| **Windows Performance** | ❌ | ❌ | ✅ 3 tools |
| - `get_windows_performance_counters` | ❌ | ❌ | ✅ |
| - `monitor_windows_performance` | ❌ | ❌ | ✅ |
| - `get_windows_system_performance` | ❌ | ❌ | ✅ |
| **Windows Permissions** | ❌ | ❌ | ✅ 4 tools |
| - `get_file_permissions` | ❌ | ❌ | ✅ |
| - `set_file_permissions` | ❌ | ❌ | ✅ |
| - `analyze_directory_permissions` | ❌ | ❌ | ✅ |
| - `fix_file_permissions` | ❌ | ❌ | ✅ |
| **PowerShell/CMD** | ❌ | ❌ | ✅ 2 tools |
| - `run_powershell_tool` | ❌ | ❌ | ✅ |
| - `run_cmd_tool` | ❌ | ❌ | ✅ |

**Windows Operations Winner:** `windows-operations-mcp` (17 Windows-specific tools) - **Only one with Windows system operations**

---

### Archive Operations

| Tool | filesystem-mcp | mcp-filesystem | windows-operations-mcp |
|------|----------------|----------------|------------------------|
| `create_archive` | ❌ | ❌ | ✅ |
| `extract_archive` | ❌ | ❌ | ✅ |
| `list_archive` | ❌ | ❌ | ✅ |

**Archive Winner:** `windows-operations-mcp` (3 tools) - **Only one with archive support**

---

### JSON Operations

| Tool | filesystem-mcp | mcp-filesystem | windows-operations-mcp |
|------|----------------|----------------|------------------------|
| `read_json_file` | ❌ | ❌ | ✅ |
| `write_json_file` | ❌ | ❌ | ✅ |
| `validate_json` | ✅ (via dev tool) | ❌ | ✅ |
| `format_json` | ❌ | ❌ | ✅ |
| `to_json` | ❌ | ❌ | ✅ |
| `extract_json_from_text` | ❌ | ❌ | ✅ |

**JSON Winner:** `windows-operations-mcp` (6 tools) - **Most comprehensive JSON support**

---

### Media Metadata

| Tool | filesystem-mcp | mcp-filesystem | windows-operations-mcp |
|------|----------------|----------------|------------------------|
| `get_media_metadata` | ❌ | ❌ | ✅ |
| `update_media_metadata` | ❌ | ❌ | ✅ |
| `get_image_metadata` | ❌ | ❌ | ✅ |
| `update_image_metadata` | ❌ | ❌ | ✅ |
| `get_mp3_metadata` | ❌ | ❌ | ✅ |
| `update_mp3_metadata` | ❌ | ❌ | ✅ |

**Media Winner:** `windows-operations-mcp` (6 tools) - **Only one with media metadata**

---

### System & Network Operations

| Tool | filesystem-mcp | mcp-filesystem | windows-operations-mcp |
|------|----------------|----------------|------------------------|
| `get_system_info` | ✅ (via system_tools) | ❌ | ✅ |
| `get_system_status` | ✅ | ❌ | ❌ |
| `health_check` | ❌ | ❌ | ✅ |
| `test_port` | ❌ | ❌ | ✅ |
| `get_process_list` | ❌ | ❌ | ✅ |
| `get_process_info` | ❌ | ❌ | ✅ |
| `get_system_resources` | ❌ | ❌ | ✅ |
| `get_help` | ✅ | ❌ | ✅ |

**System Operations Winner:** `windows-operations-mcp` (7 tools) - **Most comprehensive system tools**

---

## Feature Matrix Summary

| Feature Category | filesystem-mcp | mcp-filesystem | windows-operations-mcp |
|------------------|----------------|----------------|------------------------|
| **Basic File Ops** | ✅ Good | ✅ Excellent | ✅ Good |
| **Advanced File Ops** | ⚠️ Limited | ✅ Excellent | ⚠️ Limited |
| **Docker Support** | ✅ Full | ❌ None | ❌ None |
| **Git Support** | ✅ Full | ❌ None | ⚠️ Basic |
| **Developer Tools** | ✅ Extensive | ❌ None | ❌ None |
| **Windows System Ops** | ❌ None | ❌ None | ✅ Full |
| **Archive Operations** | ❌ None | ❌ None | ✅ Yes |
| **JSON Operations** | ⚠️ Basic | ❌ None | ✅ Full |
| **Media Metadata** | ❌ None | ❌ None | ✅ Full |
| **PowerShell/CMD** | ❌ None | ❌ None | ✅ Yes |
| **Network Tools** | ❌ None | ❌ None | ✅ Yes |
| **Process Management** | ❌ None | ❌ None | ✅ Yes |
| **Cross-platform** | ✅ Yes | ✅ Yes | ❌ Windows only |

---

## Use Case Recommendations

### Choose **filesystem-mcp** if you need:
- ✅ Docker container/image management
- ✅ Comprehensive Git operations
- ✅ Developer workflow tools (linting, dependency analysis)
- ✅ Cross-platform compatibility
- ✅ System monitoring
- ✅ Comprehensive toolset in one server

### Choose **mcp-filesystem** if you need:
- ✅ Advanced file search and analysis
- ✅ Line-based file editing with verification
- ✅ File comparison and diff operations
- ✅ Directory size calculations
- ✅ Duplicate file detection
- ✅ Cross-platform compatibility
- ✅ Security-focused path restrictions

### Choose **windows-operations-mcp** if you need:
- ✅ Windows Services management
- ✅ Windows Event Log operations
- ✅ Windows Performance monitoring
- ✅ Windows Permissions management
- ✅ PowerShell/CMD command execution
- ✅ Archive operations (ZIP)
- ✅ JSON file operations
- ✅ Media metadata extraction
- ✅ Process management
- ✅ Network testing
- ✅ Windows-specific system operations

### Use All Three if:
- You want the best of all worlds
- You need Docker/Git tools AND advanced file operations AND Windows system ops
- Different use cases require different toolsets
- You want to compare implementations

---

## Tool Count Summary

| Category | filesystem-mcp | mcp-filesystem | windows-operations-mcp |
|----------|----------------|----------------|------------------------|
| File Operations | 13 tools | 23 tools | 10 tools |
| Docker Operations | 28 tools | 0 tools | 0 tools |
| Git Operations | 5 tools | 0 tools | 4 tools |
| Developer Tools | 10 commands | 0 tools | 0 tools |
| System Tools | 2 tools | 0 tools | 7 tools |
| Windows Operations | 0 tools | 0 tools | 17 tools |
| Archive Operations | 0 tools | 0 tools | 3 tools |
| JSON Operations | 1 tool | 0 tools | 6 tools |
| Media Metadata | 0 tools | 0 tools | 6 tools |
| **TOTAL** | **~59 tools** | **23 tools** | **~57 tools** |

---

## Architecture Comparison

### filesystem-mcp
- **Framework**: FastMCP 2.12
- **Architecture**: Modular (separate modules for each category)
- **Platform**: Cross-platform
- **Dependencies**: docker, gitpython, psutil
- **Entry Point**: `python -m filesystem_mcp`

### mcp-filesystem
- **Framework**: MCP SDK with typer CLI
- **Architecture**: Single server file with component system
- **Platform**: Cross-platform
- **Dependencies**: Minimal (fastmcp, typer)
- **Entry Point**: `uv run python -m mcp_filesystem [dirs]`

### windows-operations-mcp
- **Framework**: FastMCP 2.12.3
- **Architecture**: Modular with explicit registration functions
- **Platform**: **Windows only** (requires pywin32)
- **Dependencies**: pywin32, psutil, structlog
- **Entry Point**: `python -m windows_operations_mcp`
- **Packaging**: MCPB (MCP Bundle) format

---

## Conclusion

**filesystem-mcp** is best for:
- Development workflows with Docker and Git
- Cross-platform file operations
- Developer productivity tools

**mcp-filesystem** is best for:
- Advanced file operations and analysis
- Precise file editing
- Cross-platform file management

**windows-operations-mcp** is best for:
- Windows system administration
- Windows Services and Event Logs
- PowerShell automation
- Windows-specific operations

All three servers complement each other well and can be used simultaneously for different purposes. The choice depends on your specific needs and platform requirements.

