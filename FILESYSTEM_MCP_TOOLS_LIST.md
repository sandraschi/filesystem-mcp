# Filesystem MCP Tools List

**Date:** 2025-10-30  
**Status:** Actual tools available in this repo

## Available Tools

Based on code analysis of `src/filesystem_mcp/tools/file_operations/__init__.py`:

### File Operations

1. `read_file` - Read complete file contents
2. `write_file` - Write file contents
3. `list_directory` - List directory contents
4. `file_exists` - Check if file exists
5. `get_file_info` - Get detailed file metadata
6. `head_file` - Read first N lines of file
7. `tail_file` - Read last N lines of file
8. `grep_file` - Search for patterns in files
9. `count_pattern` - Count pattern occurrences in files
10. `extract_log_lines` - Extract log lines matching criteria
11. `edit_file` - Edit file by replacing old_string with new_string
12. `create_directory` - Create directories
13. `remove_directory` - Remove directories

## Missing Tools (Not in this repo)

- `edit_file_at_line` - **NOT IMPLEMENTED** in this repo
- This appears to be from a different MCP server or built-in Cursor tool

## Note

The `edit_file_at_line` tool you're trying to use is **NOT** from this filesystem-mcp repository. It must be provided by:
- Cursor's built-in MCP tools
- A different MCP server configuration
- The MCP protocol definition

If you need line-based editing, use the existing `edit_file` tool which performs string replacement operations.
