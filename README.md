# Filesystem MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.14.1+-purple.svg)](https://github.com/modelcontextprotocol/python-sdk)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI/CD](https://github.com/sandr/filesystem-mcp/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/sandr/filesystem-mcp/actions/workflows/ci-cd.yml)
[![Coverage](https://codecov.io/gh/sandr/filesystem-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/sandr/filesystem-mcp)
[![PyPI](https://img.shields.io/pypi/v/filesystem-mcp)](https://pypi.org/project/filesystem-mcp/)

A **FastMCP 2.14.1+ compliant** MCP server using **portmanteau pattern** for comprehensive file system operations, Git repository management, and Docker container management. Built with modern Python patterns, enterprise-grade security, and extensive testing for professional deployment.

## ✨ Features

### 🗂️ File System Operations (20+ Tools)
- **Basic Operations**: Read, write, list, copy, move, and delete files/directories
- **Advanced Analysis**: Find large files, duplicate detection, directory size calculation
- **File Comparison**: Side-by-side diff comparison with unified format
- **Content Search**: Grep pattern matching, line-based reading, log extraction
- **Batch Operations**: Process multiple files simultaneously
- **Path Management**: Secure path validation with configurable restrictions
- **Metadata Analysis**: Comprehensive file information with type detection

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
- **Multilevel Help System**: Hierarchical documentation with portmanteau tool examples and use cases
- **System Status Tool**: Comprehensive system monitoring with resource usage metrics
- **Interactive Guidance**: Context-aware help with parameter validation and suggestions

### 🚀 Advanced Features
- **FastMCP 2.14.1+ Compliance**: Modern tool registration with `@app.tool()` decorators
- **Portmanteau Pattern**: Consolidated tool interfaces reducing complexity while maintaining full functionality
- **Enterprise Security**: Path traversal protection, permission validation, audit trails
- **Extensive Testing**: Unit, integration, and performance tests with 80%+ coverage
- **MCPB Packaging**: Professional drag-and-drop installation for Claude Desktop
- **Structured Logging**: Comprehensive logging with file output and monitoring
- **Async Operations**: Full async/await support for optimal concurrency
- **Pydantic V2**: Modern data validation with `field_validator` and `ConfigDict`
- **Multilevel Help System**: Interactive guidance with portmanteau tool examples and use cases
- **System Monitoring**: Resource usage tracking and performance metrics
- **Cross-Platform**: Windows, macOS, and Linux support

## 🚀 Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

### 📦 Quick Start
Run immediately via `uvx`:
```bash
uvx filesystem-mcp
```

### 🎯 Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "filesystem-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/filesystem-mcp", "run", "filesystem-mcp"]
  }
}
```
### Prerequisites
- **Python 3.9+** (FastMCP 2.14.3+ requirement)
- **Docker Engine** (for container operations)
- **Git** (for repository operations)

### 📦 PyPI Package Install (RECOMMENDED)

**Fastest Installation - Production Ready:**

```bash
pip install filesystem-mcp
```

**Claude Desktop Integration:**
- Open Claude Desktop
- Settings → MCP Servers
- Add new MCP server:
  ```json
  {
    "mcpServers": {
      "filesystem-mcp": {
        "command": "filesystem-mcp"
      }
    }
  }
  ```

### 🎯 Claude Desktop MCPB Package

1.  **Download** the `filesystem-mcp.mcpb` package from [Releases](https://github.com/sandr/filesystem-mcp/releases)
2.  **Drag & Drop** the file to Claude Desktop
3.  **Configure** settings when prompted (working directory, timeouts, etc.)
4.  **Install dependencies** separately (see below)
5.  **Start using** 57+ professional tools immediately

## 🚀 Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

### 📦 Quick Start
Run immediately via `uvx`:
```bash
uvx filesystem-mcp
```

### 🎯 Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "filesystem-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/filesystem-mcp", "run", "filesystem-mcp"]
  }
}
```
## 🚀 Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

### 📦 Quick Start
Run immediately via `uvx`:
```bash
uvx filesystem-mcp
```

### 🎯 Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "filesystem-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/filesystem-mcp", "run", "filesystem-mcp"]
  }
}
```
### HTTP/HTTPS Mode (For Web Apps)

For web applications or custom MCP clients, run the server in HTTP mode:

```bash
# Set environment variables
export MCP_TRANSPORT=http
export MCP_HOST=127.0.0.1  # or 0.0.0.0 for all interfaces
export MCP_PORT=8000

# Run the server
python -m filesystem_mcp
```

Or use uvicorn directly with the ASGI app:

```python
from filesystem_mcp import http_app
import uvicorn

# Get ASGI app
asgi_app = http_app()

# Run with uvicorn
uvicorn.run(asgi_app, host="127.0.0.1", port=8000)
```

Or via command line:
```bash
uvicorn filesystem_mcp:http_app --host 127.0.0.1 --port 8000
```

The MCP endpoint will be available at: `http://127.0.0.1:8000/mcp/`

**Quick test:**
```bash
curl http://127.0.0.1:8000/mcp/
```

### Manual Claude Desktop Configuration

For manual installation or other MCP clients, add to your Claude Desktop configuration file (`claude_desktop_config.json`):

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
  - `MCP_TRANSPORT`: Set to `"http"` for HTTP mode, `"stdio"` for stdio mode (default: `"stdio"`)
  - `MCP_HOST`: Host address for HTTP mode (default: `"127.0.0.1"`)
  - `MCP_PORT`: Port number for HTTP mode (default: `8000`)
  - `FASTMCP_LOG_LEVEL`: Set to `DEBUG`, `INFO`, `WARNING`, or `ERROR`
  - `GIT_USERNAME`: Default Git username for commits
  - `GIT_EMAIL`: Default Git email for commits

## 🚀 Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

### 📦 Quick Start
Run immediately via `uvx`:
```bash
uvx filesystem-mcp
```

### 🎯 Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "filesystem-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/filesystem-mcp", "run", "filesystem-mcp"]
  }
}
```
## 🤖 Help System & Status Tools

### System Operations (portmanteau)

**Unified system tool** with 20+ operations:
- **Help**: `get_help` - Multilevel help system with tool documentation
- **Status**: `get_system_status` - Comprehensive system monitoring
- **Resources**: `get_resource_usage`, `get_cpu_info`, `get_memory_info`, `get_disk_usage`
- **Processes**: `get_process_info` - Process monitoring and management
- **Network**: `get_network_info` - Network interface information
- **System Info**: `get_system_info`, `get_hardware_info`, `get_software_info`
- **Environment**: `get_environment_info`, `get_locale_info`, `get_time_info`
- **Security**: `get_security_info` - Basic security information
- **Performance**: `get_performance_metrics` - System performance monitoring

```python
# Get comprehensive help
result = system_operations("get_help", category="filesystem")

# Monitor system status
result = system_operations("get_system_status", include_processes=True, include_disk=True)

# Get resource usage
result = system_operations("get_resource_usage")
```

### Multilevel Help System
Get comprehensive guidance for all portmanteau tools:

```python
# Overview of all categories and tools
system_operations("get_help")

# Detailed help for filesystem operations
system_operations("get_help", category="filesystem")

# Specific tool documentation with examples
system_operations("get_help", category="filesystem", tool_name="filesystem_operations")
```

**Help Categories:**
- `filesystem` - File reading, writing, directory management, search, analysis
- `docker` - Container, image, network, and volume management
- `repository` - Git repository operations (clone, commit, branch, merge, etc.)
- `system` - System monitoring, status, and help functionality

### System Status Monitoring
Monitor system resources and server health:

```python
# Comprehensive system status
system_operations("get_system_status")

# Resource monitoring only
system_operations("get_system_status", include_processes=True, include_disk=True)

# Network and system info
system_operations("get_system_status", include_network=True)
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

### Available Portmanteau Tools

#### 📂 Filesystem Operations (portmanteau)

**Unified filesystem tool** with 20+ operations:
- **file_ops**: Comprehensive file management (`read_file`, `write_file`, `edit_file`, `move_file`, `undo_edit`).
    - **Honed Editing**: Support for Regex, Multi-occurrence, Indentation Normalization, and Atomic Batch Edits.
    - **Reversion**: Rapid undo capability via `.bak` file restoration.
- `calculate_directory_size`, `find_duplicate_files`, `find_large_files`
- `find_empty_directories`, `compare_files`, `read_multiple_files`
- `move_file`, `read_file_lines`, `search_files`

#### `edit_file`
Precise text replacement with context validation and advanced matching.

**Parameters**:
- `path` (str): Target file path.
- `old_string` (str): Text to find.
- `new_string` (str): Replacement text.
- `allow_multiple` (bool): If true, replaces all occurrences. Default: `false`.
- `is_regex` (bool): If true, treats `old_string` as a regex pattern. Default: `false`.
- `ignore_whitespace` (bool): If true, matches regardless of indentation. Default: `false`.
- `replacements` (list): Batch mode! List of `{old_string, new_string}` for atomic multi-chunk edits.

#### `undo_edit`
Reverts the most recent edit to a file by restoring its `.bak` backup.

**Parameters**:
- `path` (str): Target file path.

```python
# Read a file
result = filesystem_operations("read_file", path="README.md")

# List directory contents
result = filesystem_operations("list_directory", path=".", recursive=True)

# Search for files
result = filesystem_operations("search_files", directory_path=".", pattern="*.py")
```

#### 🐳 Docker Operations (portmanteau)

**Unified Docker tool** with 25+ operations:
- **Container**: `list_containers`, `get_container`, `create_container`, `start_container`, `stop_container`, `restart_container`, `remove_container`, `container_exec`, `container_logs`, `container_stats`
- **Images**: `list_images`, `get_image`, `pull_image`, `build_image`, `remove_image`, `prune_images`
- **Networks**: `list_networks`, `get_network`, `create_network`, `remove_network`, `prune_networks`
- **Volumes**: `list_volumes`, `get_volume`, `create_volume`, `remove_volume`, `prune_volumes`
- **Compose**: `compose_up`, `compose_down`, `compose_ps`, `compose_logs`, `compose_config`, `compose_restart`

```python
# List running containers
result = docker_operations("list_containers")

# Create and start a container
result = docker_operations("create_container", image="nginx:latest", name="web", ports={"80/tcp": 8080})
result = docker_operations("start_container", container_id="web")

# Get container logs
result = docker_operations("container_logs", container_id="web", tail=100)
```

#### 🔄 Repository Operations (portmanteau)

**Unified Git tool** with 30+ operations:
- **Basic**: `clone_repo`, `get_repo_status`, `commit_changes`, `read_repo`
- **Branching**: `create_branch`, `switch_branch`, `merge_branch`, `delete_branch`, `list_branches`
- **Remotes**: `push_changes`, `pull_changes`, `fetch_updates`, `list_remotes`, `add_remote`, `remove_remote`
- **History**: `get_commit_history`, `show_commit`, `diff_changes`, `blame_file`, `get_file_history`
- **Advanced**: `stash_changes`, `apply_stash`, `list_stashes`, `create_tag`, `list_tags`, `delete_tag`
- **Operations**: `revert_commit`, `reset_to_commit`, `cherry_pick`, `rebase_branch`, `resolve_conflicts`

```python
# Clone a repository
result = repository_operations("clone_repo", repo_url="https://github.com/user/repo.git", target_dir="./project")

# Get repository status
result = repository_operations("get_repo_status", repo_path="./project")

# Commit changes
result = repository_operations("commit_changes", repo_path="./project", message="Add new feature", add_all=True)
```

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

# Get a list of available portmanteau tools
tools = app.list_tools()
print(f"Available portmanteau tools: {', '.join(tools.keys())}")

# Example: Filesystem operations
try:
    # Read a file
    result = tools["filesystem_operations"]("read_file", path="README.md")
    print(f"File content: {result['content'][:200]}...")

    # List directory contents
    result = tools["filesystem_operations"]("list_directory", path=".", recursive=False)
    print(f"Directory contents: {len(result['files'])} items")

    # Search for Python files
    result = tools["filesystem_operations"]("search_files", directory_path=".", pattern="*.py")
    print(f"Found {result['total_matches']} Python files")

except Exception as e:
    print(f"Filesystem error: {e}")

# Example: Docker operations
try:
    # List running containers
    result = tools["docker_operations"]("list_containers")
    print(f"Running containers: {len(result['containers'])}")

    # Get container details
    if result['containers']:
        container_id = result['containers'][0]['id']
        details = tools["docker_operations"]("get_container", container_id=container_id)
        print(f"Container {container_id}: {details['container']['status']}")

except Exception as e:
    print(f"Docker error: {e}")

# Example: Repository operations
try:
    # Get repository status
    result = tools["repository_operations"]("get_repo_status", repo_path=".")
    print(f"Repository status: {result['is_dirty']} (ahead: {result['ahead']}, behind: {result['behind']})")

    # List branches
    result = tools["repository_operations"]("list_branches", repo_path=".")
    print(f"Branches: {result['local_branches']}")

except Exception as e:
    print(f"Repository error: {e}")

# Example: System operations
try:
    # Get system status
    result = tools["system_operations"]("get_system_status", include_processes=True)
    print(f"CPU usage: {result['cpu']['usage_percent']}%")
    print(f"Memory usage: {result['memory']['percent']}%")

    # Get help information
    result = tools["system_operations"]("get_help", category="filesystem")
    print(f"Available filesystem operations: {len(result.get('tools', {}))}")

except Exception as e:
    print(f"System error: {e}")
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


## 🌐 Webapp Dashboard

This MCP server includes a free, premium web interface for monitoring and control.
By default, the web dashboard runs on port **10742**.
*(Assigned ports: **10742** (Backend (was 13000)), **10743** (Frontend (was 13001)))*

To start the webapp:
1. Navigate to the `webapp` (or `web`, `frontend`) directory.
2. Run `start.bat` (Windows) or `./start.ps1` (PowerShell).
3. Open `http://localhost:10742` in your browser.
