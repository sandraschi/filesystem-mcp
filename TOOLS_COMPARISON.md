# Tools Comparison: filesystem-mcp vs mcp-filesystem

## ✅ **UPDATE: Successful Tool Porting** (2025-12-25)

**filesystem-mcp** has successfully ported **8 high-value tools** from mcp-filesystem:
- ✅ `directory_tree` - Visual directory tree representation
- ✅ `calculate_directory_size` - Directory size calculation with statistics
- ✅ `find_duplicate_files` - Duplicate file detection using hashing
- ✅ `find_large_files` - Large file detection for disk management
- ✅ `find_empty_directories` - Empty directory cleanup
- ✅ `compare_files` - File comparison with diff output
- ✅ `read_multiple_files` - Batch file reading
- ✅ `move_file` - File/directory moving and renaming
- ✅ `read_file_lines` - Precise line-based file reading
- ✅ `search_files` - Advanced recursive file search with patterns

**Total tools increased**: ~50 → **~57+ tools**

These tools enhance filesystem-mcp's advanced file operations capabilities while maintaining FastMCP 2.12+ compliance.

---

## Overview

| Feature | filesystem-mcp | mcp-filesystem |
|---------|----------------|----------------|
| **Framework** | FastMCP 2.12 | MCP SDK (typer-based) |
| **Total Tools** | ~50+ tools | ~23 tools |
| **Focus** | Comprehensive (Files, Docker, Git, Dev Tools) | File operations focused |
| **Architecture** | Modular (separate tool modules) | Single server file |

---

## File Operations Comparison

### ✅ Common Tools (Both Have)

| Tool | filesystem-mcp | mcp-filesystem | Notes |
|------|----------------|----------------|-------|
| `read_file` | ✅ | ✅ | Both read complete file contents |
| `write_file` | ✅ | ✅ | Both write file contents |
| `list_directory` | ✅ | ✅ | Both list directory contents |
| `get_file_info` | ✅ | ✅ | Both get file metadata |
| `head_file` | ✅ | ✅ | Both read first N lines |
| `tail_file` | ✅ | ✅ | Both read last N lines |
| `create_directory` | ✅ | ✅ | Both create directories |
| `edit_file` | ✅ | ✅ | Both edit files (different approaches) |

### 🔍 Advanced File Operations

| Tool | filesystem-mcp | mcp-filesystem | Description |
|------|----------------|----------------|-------------|
| `grep_file` | ✅ | ✅ `grep_files` | Search patterns in files |
| `count_pattern` | ✅ | ❌ | Count pattern occurrences |
| `extract_log_lines` | ✅ | ❌ | Extract log lines with filtering |
| `read_multiple_files` | ✅ **NEW** | ✅ | Read multiple files at once |
| `move_file` | ✅ **NEW** | ✅ | Move/rename files |
| `search_files` | ✅ **NEW** | ✅ | Recursive file search with patterns |
| `directory_tree` | ✅ **NEW** | ✅ | Recursive tree view |
| `calculate_directory_size` | ✅ **NEW** | ✅ | Calculate directory size |
| `find_duplicate_files` | ✅ **NEW** | ✅ | Find duplicate files by hash |
| `compare_files` | ✅ **NEW** | ✅ | Compare two files (diff) |
| `find_large_files` | ✅ **NEW** | ✅ | Find files larger than size |
| `find_empty_directories` | ✅ **NEW** | ✅ | Find empty directories |
| `read_file_lines` | ✅ **NEW** | ✅ | Read specific line ranges |
| `edit_file_at_line` | ❌ | ✅ | Line-based editing with verification |
| `remove_directory` | ✅ | ❌ | Remove directories |
| `file_exists` | ✅ | ❌ | Check file existence |

---

## Unique Features

### filesystem-mcp Only

#### 🐳 Docker Operations (20+ tools)
- **Container Management**: `list_containers`, `get_container`, `create_container`, `start_container`, `stop_container`, `restart_container`, `remove_container`, `container_exec`, `container_logs`, `container_stats`
- **Image Management**: `list_images`, `get_image`, `pull_image`, `build_image`, `remove_image`, `prune_images`
- **Network & Volumes**: `list_networks`, `get_network`, `create_network`, `remove_network`, `prune_networks`, `list_volumes`, `get_volume`, `create_volume`, `remove_volume`, `prune_volumes`
- **Docker Compose**: `compose_up`, `compose_down`, `compose_ps`, `compose_logs`, `compose_config`, `compose_restart`

#### 🔄 Git Operations (4 tools)
- `clone_repo` - Clone repositories
- `get_repo_status` - Get repository status
- `commit_changes` - Commit changes
- `read_repo` - Read repository structure
- `list_branches` - List Git branches

#### 🛠️ Developer Tools (1 unified tool with 10 commands)
- `developer_tool` with commands:
  - `analyze_dependencies` - Analyze project dependencies
  - `analyze_imports` - Analyze Python imports
  - `analyze_project` - Detect project type/frameworks
  - `check_file_sizes` - Find large files
  - `detect_duplicates` - Find duplicate files
  - `find_symbols` - Search for functions/classes
  - `find_todos` - Find TODO/FIXME comments
  - `run_linter` - Run code linting (ruff, flake8, eslint)
  - `validate_config` - Validate config files
  - `validate_json` - Parse and validate JSON

#### 📊 System Tools (2 tools)
- `get_help` - Multilevel help system
- `get_system_status` - System monitoring

### mcp-filesystem Only

#### 🔒 Security Features
- `list_allowed_directories` - List directories server can access
- Path validation and restrictions built-in
- Directory-based access control

#### 📝 Advanced Editing
- `edit_file_at_line` - Line-based editing with:
  - Line number-based edits
  - Verification (expected_content)
  - Multiple edit actions (replace, insert_before, insert_after, delete)
  - Dry-run mode
  - Offset/limit support

#### 🔍 Advanced Search
- `grep_files` - More advanced grep with:
  - Regex support
  - Context lines (before/after)
  - Pagination (offset/limit)
  - File size limits
  - Count-only mode
  - Multiple include/exclude patterns

---

## Feature Comparison Matrix

| Feature Category | filesystem-mcp | mcp-filesystem |
|------------------|----------------|----------------|
| **Basic File Ops** | ✅ Complete | ✅ Complete |
| **Advanced File Ops** | ✅ **Comprehensive** | ✅ Extensive |
| **Docker Support** | ✅ Full | ❌ None |
| **Git Support** | ✅ Full | ❌ None |
| **Developer Tools** | ✅ Extensive | ❌ None |
| **System Monitoring** | ✅ Yes | ❌ None |
| **Security/Validation** | ⚠️ Basic | ✅ Advanced |
| **Line-based Editing** | ✅ **Partial** | ✅ Yes |
| **File Comparison** | ✅ **Yes** | ✅ Yes |
| **Duplicate Detection** | ✅ **Native** | ✅ Native |
| **Directory Analysis** | ✅ **Full** | ✅ Yes (size, empty dirs) |

---

## Use Case Recommendations

### Choose **filesystem-mcp** if you need:
- ✅ Docker container/image management
- ✅ Git repository operations
- ✅ Developer workflow tools (linting, dependency analysis)
- ✅ System monitoring
- ✅ Comprehensive toolset in one server
- ✅ FastMCP 2.12 compliance

### Choose **mcp-filesystem** if you need:
- ✅ Advanced file search and analysis
- ✅ Line-based file editing with verification
- ✅ File comparison and diff operations
- ✅ Directory size calculations
- ✅ Duplicate file detection
- ✅ Security-focused path restrictions
- ✅ More granular file operation control

### Use Both if:
- You want the best of both worlds
- You need Docker/Git tools AND advanced file operations
- You want to compare implementations
- Different use cases require different toolsets

---

## Tool Count Summary

| Category | filesystem-mcp | mcp-filesystem |
|----------|----------------|----------------|
| File Operations | 20 tools | 23 tools |
| Docker Operations | 20+ tools | 0 tools |
| Git Operations | 5 tools | 0 tools |
| Developer Tools | 10 commands (1 tool) | 0 tools |
| System Tools | 2 tools | 0 tools |
| **TOTAL** | **~57+ tools** | **23 tools** |

---

## Implementation Differences

### filesystem-mcp
- **Architecture**: Modular (separate modules for each category)
- **Framework**: FastMCP 2.12 with `@app.tool()` decorators
- **Error Handling**: Structured with Pydantic models
- **Logging**: Comprehensive structured logging
- **Dependencies**: More dependencies (docker, gitpython, etc.)

### mcp-filesystem
- **Architecture**: Single server file with component system
- **Framework**: MCP SDK with typer CLI
- **Error Handling**: String-based error messages
- **Logging**: Basic logging
- **Dependencies**: Minimal dependencies
- **Security**: Built-in path validation and restrictions

---

## Conclusion

**filesystem-mcp** is better for:
- Comprehensive development workflows
- Docker and Git integration
- Developer productivity tools

**mcp-filesystem** is better for:
- Advanced file operations
- Precise file editing
- File analysis and comparison
- Security-focused operations

Both servers complement each other well and can be used simultaneously for different purposes.

