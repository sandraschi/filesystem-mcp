# Filesystem MCP Troubleshooting Guide

## 🐛 Common Issues and Solutions

### Installation Issues

#### Package Won't Install in Claude Desktop
**Symptoms**: Drag-and-drop fails, package rejected, error messages

**Solutions**:
1. **Verify package integrity**: Ensure `.mcpb` file is not corrupted
2. **Check Claude Desktop version**: Update to latest version
3. **Restart Claude Desktop**: Sometimes resolves installation issues
4. **Check file permissions**: Ensure read access to `.mcpb` file

#### Configuration Prompts Don't Appear
**Symptoms**: Package installs but no setup prompts shown

**Solutions**:
1. **Restart Claude Desktop** after installation
2. **Check Claude Desktop settings**: Look for MCP configuration section
3. **Reinstall package**: Remove and reinstall the MCPB package
4. **Check system permissions**: Ensure Claude Desktop has proper access

### File Operation Issues

#### Permission Denied Errors
**Symptoms**: `PermissionError`, access denied messages

**Common Causes & Solutions**:
```bash
# Check file permissions
ls -la /path/to/file

# Fix permissions (Linux/Mac)
chmod 644 /path/to/file

# Check directory permissions
ls -ld /path/to/directory

# Fix directory permissions
chmod 755 /path/to/directory
```

**Windows Solutions**:
- Right-click file/folder → Properties → Security tab
- Ensure user account has read/write permissions
- Check if file is locked by another process

#### File Not Found Errors
**Symptoms**: `FileNotFoundError`, path doesn't exist

**Debugging Steps**:
1. **Verify path exists**: `ls -la /path/to/file`
2. **Check for typos** in file path
3. **Use absolute paths** instead of relative
4. **Check working directory**: `pwd` or `cd` command
5. **Verify file wasn't moved/deleted**

#### File Too Large Errors
**Symptoms**: Operations fail on large files

**Solutions**:
1. **Increase max file size** in Claude Desktop settings
2. **Split large files** into smaller chunks
3. **Use streaming operations** for very large files
4. **Check available disk space**

### Git Operation Issues

#### Repository Clone Fails
**Symptoms**: Clone operations fail with network/auth errors

**Solutions**:
```bash
# Check network connectivity
ping github.com

# Verify repository URL
curl -I https://github.com/user/repo

# Check authentication (if private repo)
git ls-remote https://github.com/user/repo

# Try with different protocol
git clone git@github.com:user/repo.git  # SSH instead of HTTPS
```

#### Git Authentication Issues
**Symptoms**: Push/pull operations fail with auth errors

**Solutions**:
1. **Configure Git credentials**:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

2. **Set up SSH keys** (recommended for GitHub):
   ```bash
   ssh-keygen -t ed25519 -C "your.email@example.com"
   # Add public key to GitHub account
   ```

3. **Use personal access tokens** for HTTPS:
   - Generate token in GitHub settings
   - Use token as password when prompted

### Docker Operation Issues

#### Docker Connection Failed
**Symptoms**: Container operations fail, daemon not accessible

**Solutions**:
```bash
# Check Docker daemon status
docker ps

# Start Docker service (Linux)
sudo systemctl start docker

# Start Docker Desktop (Mac/Windows)
# Launch Docker Desktop application

# Check Docker socket permissions (Linux)
ls -la /var/run/docker.sock
sudo usermod -aG docker $USER  # Add user to docker group
```

#### Container Not Found
**Symptoms**: Operations fail with "container not found"

**Debugging**:
```bash
# List all containers (including stopped)
docker ps -a

# Check container name/ID
docker inspect container_name

# Verify container is running
docker ps | grep container_name
```

#### Image Pull Fails
**Symptoms**: `pull_image` operations fail with network errors

**Solutions**:
1. **Check internet connectivity**
2. **Verify image name**: `docker search image_name`
3. **Try different registry**: `docker pull registry.hub.docker.com/image:tag`
4. **Check Docker Hub rate limits**

### Performance Issues

#### Operations Taking Too Long
**Symptoms**: Commands timeout or run very slowly

**Solutions**:
1. **Increase timeout settings** in Claude Desktop configuration
2. **Check system resources**: CPU, memory, disk I/O
3. **Reduce operation scope**: Smaller directories, fewer files
4. **Use more specific search patterns**

#### High Memory Usage
**Symptoms**: Operations consume excessive memory

**Solutions**:
1. **Process files in chunks** for large operations
2. **Use streaming operations** instead of loading entire files
3. **Monitor system resources** during operations
4. **Close file handles** properly after operations

### Network and Connectivity Issues

#### Connection Timeouts
**Symptoms**: Network operations fail with timeout errors

**Solutions**:
1. **Check network connectivity**: `ping google.com`
2. **Increase timeout settings** in configuration
3. **Verify firewall settings** aren't blocking connections
4. **Check proxy settings** if applicable

#### SSL/TLS Certificate Issues
**Symptoms**: HTTPS operations fail with certificate errors

**Solutions**:
1. **Update system certificates**: `sudo apt update && sudo apt install ca-certificates`
2. **Disable SSL verification** (not recommended for production)
3. **Check system time**: Incorrect time can cause certificate validation failures

### System-Specific Issues

#### Windows Path Issues
**Symptoms**: Path-related errors on Windows

**Solutions**:
- Use forward slashes: `/path/to/file` instead of `\path\to\file`
- Use raw strings for paths: `r"C:\path\to\file"`
- Avoid spaces in paths or use quotes
- Check Windows file permissions

#### macOS Permission Issues
**Symptoms**: Operations fail with permission errors on macOS

**Solutions**:
```bash
# Check System Integrity Protection
csrutil status

# Grant full disk access to terminal/Python
# System Settings → Privacy & Security → Full Disk Access

# Check file permissions
ls -la /path/to/file
```

#### Linux File System Issues
**Symptoms**: File operations fail on Linux systems

**Solutions**:
```bash
# Check disk space
df -h

# Check file system type
df -T /path/to/file

# Check mount options
mount | grep /path/to/mount

# Fix permissions
chmod 644 /path/to/file
chown user:group /path/to/file
```

### Debugging Tools

#### Enable Debug Logging
```bash
# Set environment variables
export FILESYSTEM_MCP_LOG_LEVEL="DEBUG"
export FILESYSTEM_MCP_LOG_FILE="/tmp/filesystem-mcp-debug.log"

# Restart Claude Desktop to apply changes
```

#### Check System Information
Use the built-in system info tool:
```bash
get_system_info
```

#### Test Basic Functionality
```bash
# Test file operations
write_file test.txt "Hello World"
read_file test.txt

# Test directory operations
list_directory .

# Test Docker (if available)
list_containers
```

### Getting Help

#### Community Support
- Check GitHub issues for similar problems
- Search existing documentation
- Create detailed bug reports with:
  - Error messages
  - System information
  - Steps to reproduce
  - Expected vs actual behavior

#### Professional Support
For enterprise deployments:
- Contact support with detailed logs
- Provide system diagnostics
- Include configuration details
- Specify Claude Desktop version

### Emergency Recovery

#### Reset Configuration
1. **Uninstall MCPB package** from Claude Desktop
2. **Clear Claude Desktop cache**
3. **Restart Claude Desktop**
4. **Reinstall package** with fresh configuration

#### Data Recovery
- **Check backup locations** for important files
- **Use Git recovery** for repository issues
- **Restore from snapshots** if available

#### System Cleanup
```bash
# Clean Docker resources
docker system prune -a

# Clean temporary files
rm -rf /tmp/filesystem-mcp*

# Reset Git repositories if needed
cd /path/to/repo && git reset --hard HEAD
```

### Prevention Best Practices

1. **Regular Backups**: Always backup important data before operations
2. **Test Operations**: Test with small datasets first
3. **Monitor Resources**: Watch system resources during operations
4. **Use Appropriate Timeouts**: Set reasonable timeout values
5. **Keep Software Updated**: Update Claude Desktop, Docker, and system software
6. **Check Permissions**: Verify access permissions before operations

---

**Need more help?** Check the system information tool and include details when reporting issues.
