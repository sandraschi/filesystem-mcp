# Filesystem MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.12.0+-purple.svg)](https://github.com/modelcontextprotocol/python-sdk)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI/CD](https://github.com/sandr/filesystem-mcp/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/sandr/filesystem-mcp/actions/workflows/ci-cd.yml)
[![Coverage](https://codecov.io/gh/sandr/filesystem-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/sandr/filesystem-mcp)
[![PyPI](https://img.shields.io/pypi/v/filesystem-mcp)](https://pypi.org/project/filesystem-mcp/)

A **FastMCP 2.12.0+ compliant** MCP server for comprehensive file system operations, Git repository management, and Docker container management. Built with modern Python patterns, enterprise-grade security, and extensive testing for professional deployment.

## ✨ Features

### 🗂️ File System Operations
- Read, write, and manage files and directories
- List directory contents with detailed file metadata
- Check file existence and get file information
- Recursive directory scanning with configurable depth
- File content analysis and manipulation

### 🐳 Docker Container Management
- **Container Operations**
  - List, create, start, stop, and remove containers
  - Execute commands inside running containers
  - Stream container logs with filtering options
  - Monitor container resource usage and statistics
  - Inspect container details and configuration

- **Image Management**
  - List available Docker images
  - Pull, build, and remove images
  - Inspect image details and history

- **Network & Volume Management**
  - Create and manage Docker networks
  - Manage Docker volumes and bind mounts
  - Configure container networking

- **Docker Compose Support**
  - Deploy and manage multi-container applications
  - Scale services up and down
  - View service logs and status

### 🔄 Git Repository Management
- Clone repositories with branch and depth control
- Get repository status (staged, unstaged, untracked changes)
- Commit changes with custom messages
- Read repository structure and file contents
- Manage branches and remotes

### 🤖 System Tools & Help
- **Multilevel Help System**: Hierarchical documentation with tool examples and use cases
- **System Status Tool**: Comprehensive system monitoring with resource usage metrics
- **Interactive Guidance**: Context-aware help with parameter validation and suggestions

### 🚀 Advanced Features
- **FastMCP 2.12.0+ Compliance**: Modern tool registration with `@app.tool()` decorators
- **Enterprise Security**: Path traversal protection, permission validation, audit trails
- **Extensive Testing**: Unit, integration, and performance tests with 80%+ coverage
- **DXT Packaging**: Professional deployment with all dependencies included
- **Structured Logging**: Comprehensive logging with file output and monitoring
- **Async Operations**: Full async/await support for optimal concurrency
- **Pydantic V2**: Modern data validation with `field_validator` and `ConfigDict`
- FastMCP 2.10 compliant API
- Asynchronous operations for improved performance
- Detailed documentation and type hints

## 🚀 Installation

### Prerequisites
- **Python 3.9+** (FastMCP 2.12.0+ requirement)
- **Docker Engine** (for container operations)
- **Git** (for repository operations)
- **Node.js 20+** (for DXT packaging)

### Quick Start with DXT (Recommended)

1. **Download** the `filesystem-mcp.dxt` package from [Releases](https://github.com/sandr/filesystem-mcp/releases)
2. **Drag & Drop** the file to Claude Desktop
3. **Configure** working directory when prompted
4. **Start using** professional tools immediately

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/sandr/filesystem-mcp.git
cd filesystem-mcp

# Create and activate a virtual environment (recommended)
python -m venv venv
# On Windows: .\venv\Scripts\Activate.ps1
# On Unix/Mac: source venv/bin/activate

# Install with all dependencies
pip install -e .[dev,test]

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### Claude Desktop Configuration

After installation, configure Claude Desktop to use the filesystem MCP server by adding the following to your Claude Desktop configuration file (`claude_desktop_config.json`):

**Windows:**
```json
{
  "mcpServers": {
    "filesystem-mcp": {
      "command": "python",
      "args": ["-m", "filesystem_mcp"],
      "env": {
        "PYTHONPATH": "D:\\path\\to\\filesystem-mcp\\src",
        "PYTHONUNBUFFERED": "1",
        "FASTMCP_LOG_LEVEL": "INFO"
      },
      "cwd": "D:\\path\\to\\your\\working\\directory"
    }
  }
}
```

**macOS/Linux:**
```json
{
  "mcpServers": {
    "filesystem-mcp": {
      "command": "python",
      "args": ["-m", "filesystem_mcp"],
      "env": {
        "PYTHONPATH": "/path/to/filesystem-mcp/src",
        "PYTHONUNBUFFERED": "1",
        "FASTMCP_LOG_LEVEL": "INFO"
      },
      "cwd": "/path/to/your/working/directory"
    }
  }
}
```

**Configuration Notes:**
- Replace `D:\\path\\to\\filesystem-mcp\\src` with the actual path to your cloned repository's `src` directory
- Set `cwd` to your preferred working directory for file operations
- The server supports the following optional environment variables:
  - `FASTMCP_LOG_LEVEL`: Set to `DEBUG`, `INFO`, `WARNING`, or `ERROR`
  - `GIT_USERNAME`: Default Git username for commits
  - `GIT_EMAIL`: Default Git email for commits

### Docker Installation

Run the MCP server in a container with all dependencies:

```bash
# Build the multi-platform Docker image
docker buildx build -t filesystem-mcp \
  --platform linux/amd64,linux/arm64 .

# Run the container
docker run -d --name filesystem-mcp \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/workspace \
  filesystem-mcp
```

## 🤖 Help System & Status Tools

### Multilevel Help System
Get comprehensive guidance for all tools:

```python
# Overview of all categories and tools
get_help()

# Detailed help for file operations
get_help('file_operations')

# Specific tool documentation with examples
get_help('file_operations', 'read_file')
```

**Help Categories:**
- `file_operations` - File reading, writing, directory management
- `git_operations` - Repository cloning, status, commits, branches
- `docker_operations` - Container listing, resource monitoring
- `system_tools` - Help and status functionality

### System Status Monitoring
Monitor system resources and server health:

```python
# Comprehensive system status
get_system_status()

# Resource monitoring only
get_system_status(include_processes=True, include_disk=True)

# Network and system info
get_system_status(include_network=True)
```

**Status Metrics:**
- CPU usage (physical/logical cores, frequency, load)
- Memory statistics (total, available, usage percentage)
- Disk usage (total, used, free space)
- Process information (top CPU consumers)
- Network interfaces (IP addresses, status)
- Server health (FastMCP version, tool count, status)

## 🛠️ Usage

### Starting the Server

```bash
# Start the MCP server (default: http://0.0.0.0:8000)
python -m filesystem_mcp

# With custom host and port
python -m filesystem_mcp --host 127.0.0.1 --port 8080

# With debug mode enabled
python -m filesystem_mcp --debug
```

### Available Tools

#### 📂 File Operations

| Tool | Description | Parameters |
|------|-------------|------------|
| `read_file` | Read file contents | `file_path`, `encoding` |
| `write_file` | Write to a file | `file_path`, `content`, `encoding` |
| `list_directory` | List directory contents | `directory_path`, `recursive` |
| `file_exists` | Check if file/directory exists | `file_path` |
| `get_file_info` | Get file/directory metadata | `file_path` |

#### 🐳 Docker Operations

**Container Management**
- `list_containers`: List all containers with filtering options
- `get_container`: Get detailed container information
- `create_container`: Create a new container with custom configuration
- `start_container`: Start a stopped container
- `stop_container`: Stop a running container
- `restart_container`: Restart a container
- `remove_container`: Remove a container
- `container_exec`: Execute commands in a container
- `container_logs`: Stream container logs
- `container_stats`: Get container resource usage statistics

**Image Management**
- `list_images`: List available Docker images
- `pull_image`: Pull an image from a registry
- `build_image`: Build an image from a Dockerfile
- `remove_image`: Remove an image

**Network & Volume Management**
- `list_networks`: List Docker networks
- `create_network`: Create a new network
- `remove_network`: Remove a network
- `list_volumes`: List Docker volumes
- `create_volume`: Create a new volume
- `remove_volume`: Remove a volume

**Docker Compose**
- `compose_up`: Start services defined in docker-compose.yml
- `compose_down`: Stop and remove containers, networks, etc.
- `compose_ps`: List containers for services
- `compose_logs`: View output from containers

#### 🔄 Repository Operations

| Tool | Description | Parameters |
|------|-------------|------------|
| `clone_repo` | Clone a Git repository | `repo_url`, `target_dir`, `branch`, `depth` |
| `get_repo_status` | Get repository status | `repo_path` |
| `commit_changes` | Commit changes to repository | `repo_path`, `message`, `add_all`, `paths` |
| `read_repo` | Read repository structure | `repo_path`, `max_depth`, `include_files`, `include_dirs` |

#### 🛠️ Developer Tools

**Unified Developer Toolkit** - One tool with 10 specialized commands:

| Command | Description | Key Parameters |
|---------|-------------|----------------|
| `analyze_dependencies` | Analyze project dependencies from package managers | `path` |
| `analyze_imports` | Analyze Python import statements and dependencies | `path`, `recursive`, `max_results` |
| `analyze_project` | Detect project type, frameworks, and structure | `path`, `output_format` |
| `check_file_sizes` | Analyze file sizes and identify large files | `path`, `recursive`, `max_results` |
| `detect_duplicates` | Find duplicate files by content hash | `path`, `recursive`, `max_results` |
| `find_symbols` | Search for function/class definitions and usages | `path`, `pattern`, `recursive` |
| `find_todos` | Find TODO/FIXME comments in codebase | `path`, `recursive`, `max_results` |
| `run_linter` | Execute code linting (ruff, flake8, eslint) | `path`, `fix`, `encoding` |
| `validate_config` | Validate configuration files (JSON/YAML/TOML/INI) | `path` |
| `validate_json` | Parse and validate JSON files with structure analysis | `path` |

**Usage:**
```python
# Analyze project structure
result = developer_tool('analyze_project', path='.')

# Find all TODO comments
todos = developer_tool('find_todos', path='src', recursive=True)

# Run linting with auto-fix
lint_result = developer_tool('run_linter', path='src/', fix=True)

# Find function definitions
symbols = developer_tool('find_symbols', pattern='auth', recursive=True)
```

### Example Usage

```python
from filesystem_mcp import app

# Get a list of available tools
tools = app.list_tools()
print(f"Available tools: {', '.join(tools.keys())}")

# Example: List running containers
try:
    containers = tools["list_containers"]()
    print(f"Running containers: {containers}")
except Exception as e:
    print(f"Error: {e}")

# Example: Create a new container
container_config = {
    "image": "nginx:latest",
    "name": "my-nginx",
    "ports": {"80/tcp": 8080},
    "detach": True
}
container = tools["create_container"](**container_config)
print(f"Created container: {container}")
```

### Example Usage

```python
from filesystem_mcp import app

# Get a list of available tools
tools = app.list_tools()
print(f"Available tools: {', '.join(tools.keys())}")

# Use a tool
try:
    result = tools["read_file"]("README.md")
    print(f"File content: {result[:200]}...")
except Exception as e:
    print(f"Error: {e}")
```

## 🏗️ Development

### Project Structure

```text
filesystem-mcp/
├── .github/                # GitHub workflows and templates
├── docs/                   # Documentation files
├── filesystem_mcp/         # Main package
│   ├── __init__.py         # Package initialization
│   ├── app.py              # FastAPI application setup
│   ├── config.py           # Configuration management
│   ├── models/             # Pydantic models
│   ├── tools/              # Tool implementations
│   │   ├── __init__.py     # Tool registration
│   │   ├── file_operations/  # File system tools
│   │   ├── docker_operations/ # Docker management tools
│   │   └── repo_operations/  # Git repository tools
│   └── utils/              # Utility functions
├── tests/                  # Test suite
├── .gitignore             # Git ignore rules
├── LICENSE                # MIT License
├── pyproject.toml         # Project configuration and dependencies
├── README.md              # This file
└── requirements-dev.txt    # Development dependencies
```

### 🧪 Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run tests with coverage report
pytest --cov=filesystem_mcp --cov-report=term-missing

# Run specific test file
pytest tests/test_docker_operations.py -v
```

### 🎨 Code Style & Quality

This project enforces code quality using:

- **Black** - Code formatting
- **isort** - Import sorting
- **mypy** - Static type checking
- **pylint** - Code quality analysis

```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Type checking with mypy
mypy .

# Lint with pylint
pylint filesystem_mcp/
```

### 📦 Building and Releasing

1. Update the version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit changes with a message like "Bump version to x.y.z"
4. Create a git tag: `git tag vx.y.z`
5. Push the tag: `git push origin vx.y.z`
6. GitHub Actions will automatically build and publish the package to PyPI

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, or suggest new features.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a history of changes to this project.
