# Filesystem MCP User Guide

## Available Tools

### File Operations
- **read_file**: Read file contents with metadata
- **write_file**: Write content to files with validation
- **list_directory**: List directory contents with filtering
- **file_exists**: Check file/directory existence with details
- **get_file_info**: Get comprehensive file information

### Git Operations
- **clone_repo**: Clone Git repositories with options
- **get_repo_status**: Get repository status and changes
- **list_branches**: List branches with tracking information
- **commit_changes**: Commit changes with custom messages
- **read_repository**: Read repository structure and contents

### Docker Operations
- **list_containers**: List Docker containers with details

## Usage Examples

### File Operations
```
I need to read the contents of config.txt and analyze its settings.

I want to create a new directory structure for my project with proper permissions.

Please check if the file exists and get its metadata before processing.
```

### Git Operations
```
I need to clone this repository and check its current status.

Please list all branches and show me which one I'm currently on.

I want to commit my changes with a descriptive message.
```

### Docker Operations
```
Show me all running containers and their resource usage.

I need to inspect a specific container's configuration.
```

## Configuration

### Working Directory
Set your preferred working directory for file operations. This directory will be used as the default location for file operations and Git repositories.

### Git Settings
- Username: Your Git username for commits
- Email: Your Git email for commits
- These can be set globally or per-repository

### Docker Settings
- Enable Docker tools if you have Docker installed
- Docker daemon must be running for container operations

## Best Practices

1. **Start Simple**: Begin with basic file operations before complex Git workflows
2. **Check Paths**: Always verify file paths exist before operations
3. **Use Filters**: Use directory listing filters to find specific files
4. **Review Changes**: Check Git status before committing
5. **Backup Important Files**: Consider backing up files before bulk operations

## Error Handling

The system provides detailed error messages for:
- File not found errors
- Permission denied issues
- Invalid path formats
- Git repository problems
- Docker daemon connectivity issues

## Getting Help

For assistance with specific operations:
- Describe what you're trying to accomplish
- Provide the file paths or repository URLs
- Specify any error messages you've encountered
- Mention your operating system and environment

The Filesystem MCP server is designed to be safe, reliable, and user-friendly while providing comprehensive file system and development workflow capabilities.
