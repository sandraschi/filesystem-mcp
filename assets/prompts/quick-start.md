# Filesystem MCP Quick Start

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.9+
- Required dependencies (install separately):
  ```bash
  pip install fastmcp>=2.14.1 pydantic>=2.5.0 docker>=6.0.0 gitpython>=3.1.0
  ```

### Installation
1. Download the `.mcpb` package
2. Drag it into Claude Desktop
3. Configure your settings when prompted
4. Start using the tools!

## 🔥 Most Useful Tools

### File Operations
```bash
# Read any file
read_file path/to/file.txt

# Write to files
write_file notes.txt "My important notes"

# Find what you need
list_directory /home/user
search_files . "*.py"
```

### Git Management
```bash
# Clone repositories
clone_repo https://github.com/user/repo.git ./local

# Check status
get_repo_status ./project

# Commit changes
commit_changes ./project "Added feature"
```

### Docker Operations
```bash
# Manage containers
list_containers
start_container my-app
container_logs my-app
```

### File Analysis
```bash
# Find storage hogs
find_large_files /home/user 100

# Clean up duplicates
find_duplicate_files /home/user/documents

# See directory sizes
calculate_directory_size /home/user/projects
```

## 🎯 Common Workflows

### Project Setup
1. Clone repository: `clone_repo <url> ./project`
2. Check status: `get_repo_status ./project`
3. Start services: `compose_up ./project`

### File Management
1. Find large files: `find_large_files . 50`
2. Find duplicates: `find_duplicate_files ./docs`
3. Compare files: `compare_files file1.txt file2.txt`

### Log Analysis
1. Search logs: `grep_file app.log "ERROR"`
2. Extract entries: `extract_log_lines app.log ["ERROR", "WARN"]`

## ⚙️ Configuration

### Claude Desktop Settings
- **Working Directory**: Default path for operations
- **Max File Size**: Limit for file operations (MB)
- **Timeout**: Seconds for long operations

### Environment Setup
```bash
# Set working directory
export FILESYSTEM_MCP_WORKING_DIR="/home/user"

# Configure timeouts
export FILESYSTEM_MCP_TIMEOUT="60"
```

## 🆘 Need Help?

- Check tool documentation: `get_system_info`
- View available tools: Claude Desktop will show all tools
- Common issues: See troubleshooting guide

## 📚 Next Steps

- Explore advanced Docker operations
- Set up automated workflows
- Configure custom scripts
- Integrate with your development process

**Happy coding! 🎉**




