# Filesystem MCP 2.0.0 Release Notes

## 🚀 Overview

Filesystem MCP 2.0.0 is a major update featuring FastMCP 2.14.1+ compliance and MCPB packaging. This release dramatically expands functionality with 57+ professional tools, advanced file analysis capabilities, and seamless Claude Desktop integration through drag-and-drop MCPB installation.

## ✨ Key Features

### 🗂️ File System Operations (20+ Tools)
- **Basic Operations**: Read, write, copy, move, delete files/directories
- **Advanced Analysis**: Find large files, duplicate detection, directory sizing
- **File Comparison**: Side-by-side diff with unified format output
- **Content Search**: Grep patterns, line-based reading, log extraction
- **Batch Operations**: Process multiple files simultaneously
- **Path Security**: Configurable path validation and access control

### 🐳 Docker Container Management (25+ Tools)
- **Container Lifecycle**: Create, start, stop, restart, remove containers
- **Execution & Monitoring**: Run commands, stream logs, resource statistics
- **Image Management**: List, pull, build, tag, remove images
- **Networking**: Create/manage networks, inspect connectivity
- **Volumes**: Create/manage volumes, bind mounts
- **Docker Compose**: Deploy, scale, monitor multi-container apps

### 🔄 Git Repository Management (5+ Tools)
- **Repository Operations**: Clone, status, commit, branch management
- **Content Access**: Read files, browse repository structure
- **Remote Management**: Handle multiple remotes and branches

### 🤖 Advanced AI Integration
- **MCPB Packaging**: Professional drag-and-drop Claude Desktop installation
- **Extensive Prompts**: Comprehensive AI guidance templates
- **User Configuration**: Interactive setup with working directory, timeouts, etc.
- **Multilevel Help**: Interactive guidance with examples and use cases

### 🚀 Enterprise Features
- **FastMCP 2.14.1+**: Latest framework compliance
- **Security**: Path traversal protection, audit logging, permission validation
- **Performance**: Async operations, resource monitoring, optimized I/O
- **Cross-Platform**: Windows, macOS, Linux support
- **Professional Packaging**: MCPB drag-and-drop installation
- **Extensive Testing**: Unit, integration, and performance tests

## 📦 Installation

### Primary Method: MCPB Package (Recommended)
1. Download `filesystem-mcp.mcpb` from [Releases](https://github.com/sandr/filesystem-mcp/releases)
2. Drag the file into Claude Desktop
3. Configure settings when prompted (working directory, timeouts, etc.)
4. Install dependencies separately:
   ```bash
   pip install fastmcp>=2.14.1 pydantic>=2.5.0 docker>=6.0.0 gitpython>=3.1.0
   ```

### Alternative Methods
```bash
# Manual installation (for other MCP clients)
pip install git+https://github.com/sandr/filesystem-mcp.git

# Docker container (advanced users)
docker run -it --rm filesystem-mcp
```

## 📚 Documentation

For detailed documentation, please refer to the [README.md](README.md) file.

## 🔗 Links

- **GitHub Repository**: https://github.com/sandraschi/filesystem-mcp
- **Issue Tracker**: https://github.com/sandraschi/filesystem-mcp/issues
- **Documentation**: https://github.com/sandraschi/filesystem-mcp#readme

## 🙏 Acknowledgments

- The FastMCP team for the excellent framework
- The Anthropic MCPB team for professional packaging tools
- The Docker community for their amazing container technology
- The mcp-filesystem project for providing excellent tool implementations
- All contributors who helped make this release possible

## ⚖️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
