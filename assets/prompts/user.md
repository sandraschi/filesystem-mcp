# Filesystem MCP User Guide

## Overview
The Filesystem MCP provides comprehensive file system operations, Git repository management, and Docker container orchestration with enterprise-grade security and Austrian precision.

## Quick Start

### Basic File Operations
```bash
# Read a file
read_file path/to/file.txt

# Write to a file
write_file path/to/file.txt "Hello, World!"

# List directory contents
list_directory /home/user/documents

# Check if file exists
file_exists path/to/file.txt
```

### Git Operations
```bash
# Clone a repository
clone_repo https://github.com/user/repo.git /local/path

# Check repository status
get_repo_status /path/to/repo

# Commit changes
commit_changes /path/to/repo "Added new feature"

# List branches
list_branches /path/to/repo
```

### Docker Operations
```bash
# List containers
list_containers

# Start a container
start_container my-container

# Execute command in container
container_exec my-container "ls -la"

# View container logs
container_logs my-container
```

## Advanced Usage

### File Analysis
```bash
# Find large files
find_large_files /home/user 50

# Find duplicate files
find_duplicate_files /home/user/documents

# Calculate directory size
calculate_directory_size /home/user/projects

# Compare two files
compare_files file1.txt file2.txt
```

### Batch Operations
```bash
# Read multiple files
read_multiple_files ["file1.txt", "file2.txt", "file3.txt"]

# Search for files by pattern
search_files /home/user "*.py"

# Extract log lines
extract_log_lines /var/log/app.log "ERROR" 100
```

## Configuration

### Environment Variables
- `PYTHONPATH`: Python module search path
- `PYTHONUNBUFFERED`: Disable output buffering

### User Configuration
Configure via Claude Desktop settings:
- Working Directory: Default directory for operations
- Max File Size: Maximum file size for operations (MB)
- Timeout: Operation timeout in seconds

## Security Features

- Path traversal protection
- Permission validation
- Secure file operations
- Audit logging
- Input sanitization

## Best Practices

1. **Use absolute paths** when possible for clarity
2. **Check file existence** before operations
3. **Use appropriate timeouts** for long operations
4. **Validate inputs** before batch operations
5. **Monitor resource usage** for large directories

## Troubleshooting

### Common Issues

**Permission Denied**
- Check file permissions
- Ensure proper user access
- Verify path validity

**File Not Found**
- Verify file path exists
- Check for typos in path
- Use absolute paths

**Operation Timeout**
- Increase timeout settings
- Check system resources
- Break large operations into smaller chunks

**Docker Connection Failed**
- Verify Docker daemon is running
- Check Docker socket permissions
- Ensure proper Docker configuration

## Examples

### Complete Workflow: Project Setup
```bash
# 1. Clone repository
clone_repo https://github.com/user/project.git ./project

# 2. Check repository status
get_repo_status ./project

# 3. List project files
list_directory ./project

# 4. Read main configuration
read_file ./project/config.json

# 5. Build Docker containers
compose_up ./project

# 6. Check container status
list_containers
```

### File Management Workflow
```bash
# 1. Find large files to clean up
find_large_files /home/user 100

# 2. Find and remove empty directories
find_empty_directories /home/user/temp

# 3. Search for specific file types
search_files /home/user/documents "*.pdf"

# 4. Backup important files
read_multiple_files ["/home/user/docs/important.txt", "/home/user/docs/notes.md"]
```




