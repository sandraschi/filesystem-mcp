# Filesystem MCP Configuration Guide

## 📋 Configuration Overview

The Filesystem MCP supports flexible configuration through Claude Desktop settings and environment variables. All settings are optional with sensible defaults.

## ⚙️ Claude Desktop Configuration

### User Configuration Panel

When you install the MCPB package, Claude Desktop will prompt you to configure:

#### Working Directory
- **Type**: File path selector
- **Default**: Current directory (.)
- **Description**: Default directory for file operations
- **Example**: `/home/user/projects`

#### Max File Size (MB)
- **Type**: Number input
- **Default**: 100
- **Description**: Maximum file size for read/write operations in megabytes
- **Example**: 500

#### Operation Timeout (seconds)
- **Type**: Number input
- **Default**: 30
- **Description**: Timeout for long-running operations
- **Example**: 60

## 🌍 Environment Variables

### Python Environment
```bash
# Required for Python execution
export PYTHONPATH="${PWD}"
export PYTHONUNBUFFERED="1"
```

### Custom Working Directory
```bash
# Override default working directory
export FILESYSTEM_MCP_WORKING_DIR="/home/user/workspace"
```

### Operation Limits
```bash
# File size limits
export FILESYSTEM_MCP_MAX_FILE_SIZE_MB="200"

# Operation timeouts
export FILESYSTEM_MCP_TIMEOUT_SECONDS="45"

# Directory scan limits
export FILESYSTEM_MCP_MAX_FILES="10000"
```

### Docker Configuration
```bash
# Docker socket path (if non-standard)
export DOCKER_HOST="unix:///var/run/docker.sock"

# Docker API version
export DOCKER_API_VERSION="1.43"
```

### Git Configuration
```bash
# Default Git user settings
export GIT_AUTHOR_NAME="Your Name"
export GIT_AUTHOR_EMAIL="your.email@example.com"

# Git clone timeout
export GIT_CLONE_TIMEOUT="300"
```

## 🔧 Advanced Configuration

### Path Validation
The MCP includes comprehensive path validation:

- **Allowed paths**: All user-accessible directories
- **Security**: Prevents directory traversal attacks
- **Permissions**: Validates file access permissions
- **Symlinks**: Follows symbolic links safely

### Performance Tuning
```bash
# File reading chunk size
export FILESYSTEM_MCP_CHUNK_SIZE="8192"

# Concurrent operations limit
export FILESYSTEM_MCP_MAX_CONCURRENT="10"

# Memory limits for large files
export FILESYSTEM_MCP_MEMORY_LIMIT_MB="512"
```

### Logging Configuration
```bash
# Log level (DEBUG, INFO, WARNING, ERROR)
export FILESYSTEM_MCP_LOG_LEVEL="INFO"

# Log file path
export FILESYSTEM_MCP_LOG_FILE="/tmp/filesystem-mcp.log"

# Enable structured logging
export FILESYSTEM_MCP_STRUCTURED_LOGS="true"
```

## 🐳 Docker Integration

### Container Configuration
```bash
# Default container settings
export DOCKER_DEFAULT_TIMEOUT="30"
export DOCKER_DEFAULT_MEMORY="512m"
export DOCKER_DEFAULT_CPU="1.0"
```

### Network Configuration
```bash
# Docker network settings
export DOCKER_NETWORK_MODE="bridge"
export DOCKER_NETWORK_NAME="filesystem-mcp-net"
```

## 🔒 Security Settings

### File Operation Security
```bash
# Enable file permission checks
export FILESYSTEM_MCP_CHECK_PERMISSIONS="true"

# Block dangerous operations
export FILESYSTEM_MCP_BLOCK_DANGEROUS_OPS="true"

# Audit logging
export FILESYSTEM_MCP_ENABLE_AUDIT="true"
```

### Network Security
```bash
# Restrict external connections
export FILESYSTEM_MCP_ALLOW_EXTERNAL="false"

# Certificate validation
export FILESYSTEM_MCP_VERIFY_SSL="true"
```

## 📊 Monitoring Configuration

### System Monitoring
```bash
# Enable system resource monitoring
export FILESYSTEM_MCP_MONITOR_SYSTEM="true"

# Resource check interval
export FILESYSTEM_MCP_MONITOR_INTERVAL="60"

# Alert thresholds
export FILESYSTEM_MCP_CPU_THRESHOLD="80"
export FILESYSTEM_MCP_MEMORY_THRESHOLD="85"
```

### Performance Monitoring
```bash
# Operation timing
export FILESYSTEM_MCP_TRACK_PERFORMANCE="true"

# Slow operation threshold
export FILESYSTEM_MCP_SLOW_OP_THRESHOLD="10"

# Performance log file
export FILESYSTEM_MCP_PERF_LOG="/tmp/filesystem-mcp-perf.log"
```

## 🔄 Configuration Validation

### Test Configuration
```bash
# Validate current configuration
python -c "import os; print('Configuration valid')"

# Test file operations
python -c "from pathlib import Path; print('File access OK')"

# Test Docker connectivity
docker ps > /dev/null && echo "Docker OK" || echo "Docker failed"
```

### Configuration File
You can create a `.env` file for persistent configuration:

```bash
# .env file
FILESYSTEM_MCP_WORKING_DIR=/home/user/projects
FILESYSTEM_MCP_MAX_FILE_SIZE_MB=200
FILESYSTEM_MCP_TIMEOUT_SECONDS=60
DOCKER_HOST=unix:///var/run/docker.sock
```

## 🆘 Troubleshooting Configuration

### Common Issues

**Configuration not applied**
- Restart Claude Desktop after configuration changes
- Check environment variable syntax
- Verify file permissions

**Docker connection failed**
- Ensure Docker daemon is running: `docker ps`
- Check DOCKER_HOST environment variable
- Verify user permissions for Docker socket

**File access denied**
- Check file permissions: `ls -la file.txt`
- Verify working directory exists
- Check path validation rules

**Performance issues**
- Reduce MAX_FILE_SIZE_MB
- Increase timeout values
- Check system resources

### Debug Configuration
```bash
# Enable debug logging
export FILESYSTEM_MCP_LOG_LEVEL="DEBUG"

# Check current configuration
env | grep FILESYSTEM_MCP

# Test basic functionality
python -c "import sys; print(f'Python: {sys.version}')"




