# Filesystem MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A FastMCP 2.10 compliant MCP server for file system, Docker, and Git operations, designed to enable agentic AI programming capabilities with comprehensive container management.

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

### 🚀 Advanced Features
- Secure path handling and validation
- Comprehensive error handling and logging
- FastMCP 2.10 compliant API
- Asynchronous operations for improved performance
- Detailed documentation and type hints

## 🚀 Installation

### Prerequisites
- Python 3.8+
- Docker Engine (for container operations)
- Git (for repository operations)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/sandraschi/filesystem-mcp.git
cd filesystem-mcp

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

### Docker Installation

If you want to run the MCP server in a container:

```bash
# Build the Docker image
docker build -t filesystem-mcp .

# Run the container
docker run -d -p 8000:8000 --name filesystem-mcp filesystem-mcp
```

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
