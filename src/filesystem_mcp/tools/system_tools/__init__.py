"""
System tools for the Filesystem MCP - FastMCP 2.12 compliant.

This module provides multilevel help system and comprehensive status reporting
for the filesystem-mcp server. All tools follow FastMCP 2.12 standards with
proper multiline decorators and extensive error handling.
"""

import logging
import sys
import platform
import psutil
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Configure structured logging for this module
logger = logging.getLogger(__name__)

# Import app locally in functions to avoid circular imports
def _get_app():
    """Get the app instance locally to avoid circular imports."""
    import sys
    import os
    # Add src to path if not already there
    src_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    import filesystem_mcp
    return filesystem_mcp.app

class HelpSystem:
    """Multilevel help system for filesystem-mcp tools."""

    def __init__(self):
        """Initialize the help system with tool documentation."""
        self.categories = {
            "file_operations": {
                "name": "File Operations",
                "description": "Core file system operations with security and performance",
                "tools": {
                    "read_file": {
                        "description": "Read file contents with encoding detection and metadata",
                        "parameters": ["file_path", "encoding"],
                        "examples": [
                            "Read a Python file: read_file('/path/to/file.py')",
                            "Read with specific encoding: read_file('/path/to/file.txt', 'utf-16')"
                        ],
                        "use_cases": ["Configuration analysis", "Code review", "Content extraction"]
                    },
                    "write_file": {
                        "description": "Write content to files with atomic operations and validation",
                        "parameters": ["path", "content", "encoding", "create_parents"],
                        "examples": [
                            "Write configuration: write_file('config.json', '{\"key\": \"value\"}')",
                            "Create parent directories: write_file('nested/file.txt', 'content', create_parents=True)"
                        ],
                    "use_cases": ["Configuration generation", "Log writing", "Template creation"]
                },
                "edit_file": {
                    "description": "Edit files by replacing text content with atomic operations and backup",
                    "parameters": ["file_path", "old_string", "new_string"],
                    "examples": [
                        "Replace text in config: edit_file('config.json', '\"debug\": true', '\"debug\": false')",
                        "Remove empty lines: edit_file('file.txt', '\\n\\n', '\\n')"
                    ],
                    "use_cases": ["Configuration updates", "Code refactoring", "Text processing"]
                },
                    "list_directory": {
                        "description": "List directory contents with filtering and metadata",
                        "parameters": ["directory_path", "recursive", "include_hidden", "max_depth"],
                        "examples": [
                            "List current directory: list_directory('.')",
                            "Recursive listing: list_directory('/path', recursive=True, max_depth=3)"
                        ],
                        "use_cases": ["Project exploration", "File organization", "Security auditing"]
                    },
                    "file_exists": {
                        "description": "Check file/directory existence with detailed status",
                        "parameters": ["path", "check_type", "follow_symlinks"],
                        "examples": [
                            "Check file exists: file_exists('config.json', 'file')",
                            "Check directory: file_exists('/path', 'directory')"
                        ],
                        "use_cases": ["Path validation", "Resource checking", "Conditional operations"]
                    },
                    "get_file_info": {
                        "description": "Get comprehensive file/directory information and metadata",
                        "parameters": ["path", "follow_symlinks", "include_content", "max_content_size"],
                        "examples": [
                            "Get file metadata: get_file_info('important.txt')",
                            "Include content: get_file_info('config.json', include_content=True)"
                        ],
                        "use_cases": ["File analysis", "Metadata extraction", "Content inspection"]
                    }
                }
            },
            "git_operations": {
                "name": "Git Repository Management",
                "description": "Professional Git repository operations with advanced features",
                "tools": {
                    "clone_repo": {
                        "description": "Clone Git repositories with branch selection and optimization",
                        "parameters": ["repo_url", "target_dir", "branch", "depth", "single_branch"],
                        "examples": [
                            "Clone repository: clone_repo('https://github.com/user/repo.git')",
                            "Shallow clone: clone_repo('https://github.com/user/repo.git', depth=1)"
                        ],
                        "use_cases": ["Repository setup", "Dependency management", "Code review"]
                    },
                    "get_repo_status": {
                        "description": "Comprehensive repository status with staged/unstaged changes",
                        "parameters": ["repo_path", "include_staged", "include_unstaged", "include_untracked"],
                        "examples": [
                            "Check status: get_repo_status('.')",
                            "Include remote info: get_repo_status('.', include_remote=True)"
                        ],
                        "use_cases": ["Change tracking", "Commit preparation", "Repository monitoring"]
                    },
                    "list_branches": {
                        "description": "List branches with tracking status and ahead/behind information",
                        "parameters": ["repo_path"],
                        "examples": ["List all branches: list_branches('.')"],
                        "use_cases": ["Branch management", "Workflow tracking", "Collaboration"]
                    },
                    "commit_changes": {
                        "description": "Commit changes with validation and detailed commit information",
                        "parameters": ["repo_path", "message", "add_all"],
                        "examples": [
                            "Commit all changes: commit_changes('.', 'Update documentation', add_all=True)"
                        ],
                        "use_cases": ["Version control", "Change tracking", "Collaboration"]
                    },
                    "read_repo": {
                        "description": "Explore repository contents with file analysis and structure mapping",
                        "parameters": ["repo_path", "path", "include_content", "recursive"],
                        "examples": [
                            "Read repository root: read_repo('.')",
                            "Explore subdirectory: read_repo('.', 'src')"
                        ],
                        "use_cases": ["Code exploration", "Repository analysis", "Content discovery"]
                    }
                }
            },
            "docker_operations": {
                "name": "Docker Container Management",
                "description": "Container operations with resource analysis and security validation",
                "tools": {
                    "list_containers": {
                        "description": "List Docker containers with comprehensive resource and status information",
                        "parameters": ["all_containers", "filters"],
                        "examples": [
                            "List running containers: list_containers()",
                            "List all containers: list_containers(all_containers=True)"
                        ],
                        "use_cases": ["Container monitoring", "Resource management", "Deployment verification"]
                    }
                }
            },
            "system_tools": {
                "name": "System Tools",
                "description": "System status, help, and diagnostic tools",
                "tools": {
                    "get_system_status": {
                        "description": "Comprehensive system status with resource usage and health metrics",
                        "parameters": ["include_processes", "include_disk"],
                        "examples": [
                            "Full system status: get_system_status()",
                            "Resource only: get_system_status(include_processes=False, include_disk=False)"
                        ],
                        "use_cases": ["System monitoring", "Performance analysis", "Health checking"]
                    },
                    "get_help": {
                        "description": "Multilevel help system with tool documentation and examples",
                        "parameters": ["category", "tool_name", "level"],
                        "examples": [
                            "General help: get_help()",
                            "Category help: get_help('file_operations')",
                            "Tool help: get_help('file_operations', 'read_file')"
                        ],
                        "use_cases": ["Tool discovery", "Usage guidance", "Troubleshooting"]
                    }
                }
            },
            "developer_tools": {
                "name": "Developer Toolkit",
                "description": "Unified developer utilities with multiple specialized commands",
                "tools": {
                    "developer_tool": {
                        "description": "Comprehensive developer toolkit with 10 specialized commands",
                        "parameters": ["command", "path", "pattern", "recursive", "max_results", "fix", "encoding"],
                        "commands": {
                            "analyze_dependencies": "Analyze project dependencies from package managers",
                            "analyze_imports": "Analyze Python import statements and dependencies",
                            "analyze_project": "Detect project type, frameworks, and structure",
                            "check_file_sizes": "Analyze file sizes and identify large files",
                            "detect_duplicates": "Find duplicate files by content hash",
                            "find_symbols": "Search for function/class definitions and usages",
                            "find_todos": "Find TODO/FIXME comments in codebase",
                            "run_linter": "Execute code linting (ruff, flake8, eslint)",
                            "validate_config": "Validate configuration files (JSON/YAML/TOML/INI)",
                            "validate_json": "Parse and validate JSON files with structure analysis"
                        },
                        "examples": [
                            "Analyze project: developer_tool('analyze_project', path='.')",
                            "Find symbols: developer_tool('find_symbols', pattern='auth', recursive=True)",
                            "Run linter: developer_tool('run_linter', path='src/', fix=True)",
                            "Find TODOs: developer_tool('find_todos', path='src', recursive=True)",
                            "Validate JSON: developer_tool('validate_json', path='config.json')",
                            "Check file sizes: developer_tool('check_file_sizes', path='.', recursive=True)"
                        ],
                        "use_cases": ["Code analysis", "Project management", "Quality assurance", "Debugging", "Dependency management"]
                    }
                }
            }
        }

    def get_overview(self) -> Dict[str, Any]:
        """Get overview of all available tools and categories."""
        return {
            "categories": list(self.categories.keys()),
            "total_tools": sum(len(cat["tools"]) for cat in self.categories.values()),
            "version": "2.0.0",
            "fastmcp_version": "2.12.0+",
            "description": "Professional filesystem, Git, and Docker management server"
        }

    def get_category_help(self, category: str) -> Dict[str, Any]:
        """Get detailed help for a specific category."""
        if category not in self.categories:
            return {"error": f"Category '{category}' not found. Available categories: {list(self.categories.keys())}"}

        cat_info = self.categories[category]
        return {
            "name": cat_info["name"],
            "description": cat_info["description"],
            "tools": list(cat_info["tools"].keys()),
            "tool_count": len(cat_info["tools"])
        }

    def get_tool_help(self, category: str, tool_name: str) -> Dict[str, Any]:
        """Get detailed help for a specific tool."""
        if category not in self.categories:
            return {"error": f"Category '{category}' not found"}

        cat_info = self.categories[category]
        if tool_name not in cat_info["tools"]:
            return {"error": f"Tool '{tool_name}' not found in category '{category}'"}

        tool_info = cat_info["tools"][tool_name]
        result = {
            "name": tool_name,
            "category": category,
            "description": tool_info["description"],
            "parameters": tool_info["parameters"],
            "examples": tool_info["examples"],
            "use_cases": tool_info["use_cases"]
        }

        # Add commands info for developer_tool
        if tool_name == "developer_tool" and "commands" in tool_info:
            result["commands"] = tool_info["commands"]
            result["command_count"] = len(tool_info["commands"])

        return result

# Global help system instance
help_system = HelpSystem()

@_get_app().tool()
async def get_help(
    category: Optional[str] = None,
    tool_name: Optional[str] = None,
    level: str = "overview"
) -> dict:
    """Multilevel help system for filesystem-mcp tools with comprehensive documentation.

    This tool provides hierarchical help information about all available tools,
    their parameters, examples, and use cases. It supports different levels of
    detail from high-level overview to specific tool documentation.

    Args:
        category: Tool category ('file_operations', 'git_operations', 'docker_operations', 'system_tools')
        tool_name: Specific tool name within the category
        level: Detail level ('overview', 'category', 'tool')

    Returns:
        Dictionary containing help information at the requested level

    Examples:
        get_help() - Overview of all categories and tools
        get_help('file_operations') - All file operation tools
        get_help('file_operations', 'read_file') - Detailed help for read_file tool

    Error Handling:
        Returns error information for invalid categories or tool names
    """
    try:
        logger.info(f"Providing help: category={category}, tool={tool_name}, level={level}")

        if not category and not tool_name:
            # Overview level
            result = help_system.get_overview()
            logger.info(f"Provided overview help with {result['total_tools']} tools")
            return result

        elif category and not tool_name:
            # Category level
            result = help_system.get_category_help(category)
            if "error" in result:
                logger.warning(f"Help request failed: {result['error']}")
                return {"success": False, "error": result["error"]}
            else:
                logger.info(f"Provided category help for '{category}' with {result['tool_count']} tools")
                return {"success": True, "data": result}

        elif category and tool_name:
            # Tool level
            result = help_system.get_tool_help(category, tool_name)
            if "error" in result:
                logger.warning(f"Help request failed: {result['error']}")
                return {"success": False, "error": result["error"]}
            else:
                logger.info(f"Provided detailed help for '{category}.{tool_name}'")
                return {"success": True, "data": result}

        else:
            error_msg = "Invalid help request combination. Use category only or category + tool_name"
            logger.warning(error_msg)
            return {"success": False, "error": error_msg}

    except Exception as e:
        logger.error(f"Unexpected error in help system: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Help system error: {str(e)}",
            "suggestion": "Try get_help() for overview or get_help('category_name') for category help"
        }

@_get_app().tool()
async def get_system_status(
    include_processes: bool = True,
    include_disk: bool = True,
    include_network: bool = False
) -> dict:
    """Get comprehensive system status with resource usage and health metrics.

    This tool provides detailed information about the system's current state,
    including CPU, memory, disk usage, and process information. It includes
    structured logging and comprehensive error handling for reliable monitoring.

    Args:
        include_processes: Include top process information (default: True)
        include_disk: Include disk usage information (default: True)
        include_network: Include network interface information (default: False)

    Returns:
        Dictionary containing comprehensive system status information

    Error Handling:
        Returns error information if system information cannot be retrieved
    """
    try:
        logger.info("Retrieving comprehensive system status")

        # Basic system information
        system_info = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "architecture": platform.architecture(),
            "python_version": sys.version,
            "python_executable": sys.executable,
            "working_directory": str(Path.cwd()),
            "uptime": time.time() - psutil.boot_time()
        }

        # CPU information
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "cpu_percent": psutil.cpu_percent(interval=1, percpu=True),
            "cpu_frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }

        # Memory information
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free
        }

        # Disk information
        disk_info = {}
        if include_disk:
            try:
                disk_usage = psutil.disk_usage('/')
                disk_info = {
                    "total": disk_usage.total,
                    "used": disk_usage.used,
                    "free": disk_usage.free,
                    "percent": disk_usage.percent
                }
            except Exception as e:
                logger.warning(f"Could not get disk information: {e}")
                disk_info = {"error": str(e)}

        # Process information
        process_info = []
        if include_processes:
            try:
                # Get top 10 processes by CPU usage
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                    try:
                        proc_info = proc.info
                        processes.append({
                            "pid": proc_info['pid'],
                            "name": proc_info['name'],
                            "cpu_percent": proc_info['cpu_percent'],
                            "memory_percent": proc_info['memory_percent'],
                            "status": proc_info['status']
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                # Sort by CPU usage and take top 10
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
                process_info = processes[:10]

            except Exception as e:
                logger.warning(f"Could not get process information: {e}")
                process_info = {"error": str(e)}

        # Network information
        network_info = {}
        if include_network:
            try:
                network_interfaces = psutil.net_if_addrs()
                network_stats = psutil.net_if_stats()

                for interface, addrs in network_interfaces.items():
                    if interface in network_stats:
                        network_info[interface] = {
                            "addresses": [
                                {
                                    "family": str(addr.family),
                                    "address": addr.address,
                                    "netmask": addr.netmask,
                                    "broadcast": addr.broadcast
                                } for addr in addrs
                            ],
                            "stats": network_stats[interface]._asdict()
                        }
            except Exception as e:
                logger.warning(f"Could not get network information: {e}")
                network_info = {"error": str(e)}

        # FastMCP server status
        server_status = {
            "fastmcp_version": "2.12.3",
            "server_version": "2.0.0",
            "tool_count": 15,
            "status": "operational"
        }

        result = {
            "success": True,
            "system": system_info,
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info if include_disk else None,
            "processes": process_info if include_processes else None,
            "network": network_info if include_network else None,
            "server": server_status
        }

        logger.info("Successfully retrieved comprehensive system status")
        return result

    except Exception as e:
        logger.error(f"Unexpected error getting system status: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to get system status: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@_get_app().tool()
async def developer_tool(
    command: str,
    path: str = ".",
    pattern: Optional[str] = None,
    recursive: bool = True,
    include_hidden: bool = False,
    max_results: int = 100,
    output_format: str = "summary",
    fix: Optional[bool] = None,
    encoding: str = "utf-8"
) -> dict:
    """Unified developer toolkit with multiple specialized commands.

    This tool provides a comprehensive set of developer utilities through a single
    interface. Select functionality using the 'command' parameter, then provide
    command-specific parameters as needed.

    Args:
        command: The developer command to execute. See supported commands below.
        path: Target path for operations (default: current directory)
        pattern: Pattern for search/filter operations
        recursive: Whether to search recursively (default: True)
        include_hidden: Include hidden files/directories (default: False)
        max_results: Maximum results to return (default: 100)
        output_format: Output format ('summary', 'detailed', 'json')
        fix: Auto-fix issues when available (for linting)
        encoding: Text encoding to use (default: utf-8)

    Available Commands (alphabetically sorted):
        analyze_dependencies - Analyze project dependencies from package managers
        analyze_imports - Analyze Python import statements and dependencies
        analyze_project - Detect project type, frameworks, and structure
        check_file_sizes - Analyze file sizes and identify large files
        detect_duplicates - Find duplicate files by content hash
        find_symbols - Search for function/class definitions and usages
        find_todos - Find TODO/FIXME comments in codebase
        run_linter - Execute code linting (ruff, flake8, eslint)
        validate_config - Validate configuration files (JSON/YAML/TOML/INI)
        validate_json - Parse and validate JSON files with structure analysis

    Returns:
        Dictionary containing command results and metadata

    Examples:
        Analyze project: developer_tool('analyze_project', path='.')
        Find symbols: developer_tool('find_symbols', pattern='auth', recursive=True)
        Run linter: developer_tool('run_linter', path='src/', fix=True)
        Find TODOs: developer_tool('find_todos', path='src', recursive=True)
        Validate JSON: developer_tool('validate_json', path='config.json')
        Check file sizes: developer_tool('check_file_sizes', path='.', recursive=True)
    """
    try:
        logger.info(f"Running developer command: {command} on path: {path}")

        # Route to appropriate command handler
        if command == "analyze_project":
            return await _analyze_project(path, output_format)
        elif command == "find_symbols":
            return await _find_symbols(path, pattern, recursive, include_hidden, max_results)
        elif command == "run_linter":
            return await _run_linter(path, fix, encoding)
        elif command == "validate_json":
            return await _validate_json(path)
        elif command == "analyze_imports":
            return await _analyze_imports(path, recursive, include_hidden, max_results)
        elif command == "find_todos":
            return await _find_todos(path, recursive, include_hidden, max_results)
        elif command == "check_file_sizes":
            return await _check_file_sizes(path, recursive, include_hidden, max_results)
        elif command == "validate_config":
            return await _validate_config(path)
        elif command == "detect_duplicates":
            return await _detect_duplicates(path, recursive, include_hidden, max_results)
        elif command == "analyze_dependencies":
            return await _analyze_dependencies(path)
        else:
            return {
                "success": False,
                "error": f"Unknown command: {command}",
                "available_commands": [
                    "analyze_project", "find_symbols", "run_linter", "validate_json",
                    "analyze_imports", "find_todos", "check_file_sizes", "validate_config",
                    "detect_duplicates", "analyze_dependencies"
                ],
                "command": command
            }

    except Exception as e:
        logger.error(f"Unexpected error in developer_tool command '{command}': {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to execute command '{command}': {str(e)}",
            "command": command,
            "path": path
        }


async def _analyze_project(path: str, output_format: str, **kwargs) -> dict:
    """Analyze project structure and detect frameworks/tools."""
    try:
        from pathlib import Path
        project_path = Path(path).resolve()

        if not project_path.exists():
            return {"success": False, "error": f"Path not found: {path}"}

        # Detect project type and frameworks
        indicators = {
            "python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile", "__init__.py"],
            "javascript": ["package.json", "node_modules/", "webpack.config.js", "babel.config.js"],
            "typescript": ["tsconfig.json", "package.json"],
            "react": ["package.json", "src/components/", "public/index.html"],
            "vue": ["package.json", "src/main.js", "vue.config.js"],
            "angular": ["angular.json", "package.json"],
            "django": ["manage.py", "settings.py", "urls.py"],
            "flask": ["app.py", "run.py", "requirements.txt"],
            "fastapi": ["main.py", "requirements.txt", "pyproject.toml"],
            "docker": ["Dockerfile", "docker-compose.yml", ".dockerignore"],
            "git": [".git/"],
            "rust": ["Cargo.toml", "src/main.rs"],
            "go": ["go.mod", "main.go"],
            "java": ["pom.xml", "build.gradle", "src/main/java/"],
            "csharp": ["*.csproj", "Program.cs"]
        }

        detected_types = []
        config_files = []
        build_tools = []

        for file_type, files in indicators.items():
            found_files = []
            for indicator in files:
                if indicator.endswith("/"):
                    # Directory check
                    if (project_path / indicator.rstrip("/")).is_dir():
                        found_files.append(indicator)
                else:
                    # File check
                    if (project_path / indicator).exists():
                        found_files.append(indicator)

            if found_files:
                detected_types.append({
                    "type": file_type,
                    "confidence": len(found_files) / len(files),
                    "indicators": found_files
                })

        # Sort by confidence
        detected_types.sort(key=lambda x: x["confidence"], reverse=True)

        # Additional analysis
        file_count = sum(1 for _ in project_path.rglob("*") if _.is_file()) if project_path.is_dir() else 0
        dir_count = sum(1 for _ in project_path.rglob("*") if _.is_dir()) if project_path.is_dir() else 0

        result = {
            "success": True,
            "project_path": str(project_path),
            "project_types": detected_types,
            "file_count": file_count,
            "directory_count": dir_count,
            "primary_type": detected_types[0]["type"] if detected_types else "unknown",
            "confidence": detected_types[0]["confidence"] if detected_types else 0
        }

        return result

    except Exception as e:
        return {"success": False, "error": f"Project analysis failed: {str(e)}"}


async def _find_symbols(path: str, pattern: str, recursive: bool, include_hidden: bool, max_results: int, **kwargs) -> dict:
    """Find function/class definitions and symbol usages."""
    try:
        from pathlib import Path
        import re
        search_path = Path(path).resolve()

        if not search_path.exists():
            return {"success": False, "error": f"Path not found: {path}"}

        if not pattern:
            return {"success": False, "error": "Pattern required for symbol search"}

        # Common symbol patterns for different languages
        symbol_patterns = {
            "python": {
                "function": rf"def\s+{re.escape(pattern)}\s*\(",
                "class": rf"class\s+{re.escape(pattern)}\s*[:\(]",
                "variable": rf"{re.escape(pattern)}\s*=",
                "import": rf"import.*{re.escape(pattern)}|from.*{re.escape(pattern)}"
            },
            "javascript": {
                "function": rf"function\s+{re.escape(pattern)}\s*\(|const\s+{re.escape(pattern)}\s*=\s*\(",
                "class": rf"class\s+{re.escape(pattern)}\s*",
                "variable": rf"(const|let|var)\s+{re.escape(pattern)}\s*="
            }
        }

        results = []
        files_searched = 0

        # Get files to search
        if search_path.is_file():
            files_to_search = [search_path]
        else:
            pattern_obj = re.compile(r'.*\.(py|js|ts|java|cpp|c\+\+|c|cs)$', re.IGNORECASE)
            files_to_search = []
            for file_path in (search_path.rglob("*") if recursive else search_path.glob("*")):
                if file_path.is_file() and pattern_obj.match(file_path.name):
                    if not include_hidden and file_path.name.startswith('.'):
                        continue
                    files_to_search.append(file_path)

        # Search each file
        for file_path in files_to_search[:50]:  # Limit files to prevent timeout
            try:
                files_searched += 1
                content = file_path.read_text(encoding='utf-8', errors='replace')

                # Detect language
                if file_path.suffix.lower() in ['.py']:
                    lang = "python"
                elif file_path.suffix.lower() in ['.js', '.ts']:
                    lang = "javascript"
                else:
                    continue

                lines = content.splitlines()
                file_results = []

                for line_num, line in enumerate(lines, 1):
                    if len(results) >= max_results:
                        break

                    for symbol_type, regex_pattern in symbol_patterns.get(lang, {}).items():
                        if re.search(regex_pattern, line):
                            file_results.append({
                                "line_number": line_num,
                                "line_content": line.strip(),
                                "symbol_type": symbol_type,
                                "language": lang
                            })

                if file_results:
                    results.extend(file_results)

                if len(results) >= max_results:
                    break

            except Exception as e:
                logger.warning(f"Error searching {file_path}: {e}")
                continue

        return {
            "success": True,
            "pattern": pattern,
            "results": results[:max_results],
            "total_results": len(results),
            "files_searched": files_searched,
            "truncated": len(results) > max_results
        }

    except Exception as e:
        return {"success": False, "error": f"Symbol search failed: {str(e)}"}


async def _run_linter(path: str, fix: Optional[bool], encoding: str) -> dict:
    """Run code linting on the specified path."""
    try:
        from pathlib import Path
        import subprocess
        import os

        target_path = Path(path).resolve()
        if not target_path.exists():
            return {"success": False, "error": f"Path not found: {path}"}

        # Detect project type and run appropriate linter
        linters = {}

        if (target_path / "pyproject.toml").exists() or (target_path / "setup.py").exists():
            # Python project - try ruff first, then flake8
            try:
                result = subprocess.run(["ruff", "check", str(target_path), "--output-format=json"],
                                      capture_output=True, text=True, timeout=30)
                linters["python_ruff"] = {
                    "command": "ruff check",
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "issues": len(result.stdout.splitlines()) if result.stdout else 0
                }
            except (subprocess.TimeoutExpired, FileNotFoundError):
                try:
                    result = subprocess.run(["flake8", str(target_path)],
                                          capture_output=True, text=True, timeout=30)
                    linters["python_flake8"] = {
                        "command": "flake8",
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "issues": len(result.stdout.splitlines()) if result.stdout else 0
                    }
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass

        elif (target_path / "package.json").exists():
            # JavaScript/TypeScript project - try eslint
            try:
                result = subprocess.run(["npx", "eslint", str(target_path), "--format=json"],
                                      capture_output=True, text=True, timeout=30, cwd=str(target_path))
                linters["javascript_eslint"] = {
                    "command": "eslint",
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "issues": len(result.stdout.splitlines()) if result.stdout else 0
                }
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        if not linters:
            return {
                "success": True,
                "message": "No supported linters found for this project type",
                "supported_linters": ["ruff", "flake8", "eslint"],
                "path": str(target_path)
            }

        return {
            "success": True,
            "linters": linters,
            "path": str(target_path),
            "total_issues": sum(linter.get("issues", 0) for linter in linters.values())
        }

    except Exception as e:
        return {"success": False, "error": f"Linting failed: {str(e)}"}


async def _validate_json(path: str, **kwargs) -> dict:
    """Validate JSON files and provide structure analysis."""
    try:
        from pathlib import Path
        import json

        file_path = Path(path).resolve()

        if not file_path.exists():
            return {"success": False, "error": f"File not found: {path}"}

        if not file_path.is_file():
            return {"success": False, "error": f"Path is not a file: {path}"}

        try:
            content = file_path.read_text(encoding='utf-8')
            data = json.loads(content)

            # Analyze structure
            def analyze_structure(obj, path=""):
                if isinstance(obj, dict):
                    return {
                        "type": "object",
                        "keys": len(obj),
                        "properties": {k: analyze_structure(v, f"{path}.{k}" if path else k) for k, v in list(obj.items())[:10]}  # Limit depth
                    }
                elif isinstance(obj, list):
                    return {
                        "type": "array",
                        "length": len(obj),
                        "item_types": list(set(type(item).__name__ for item in obj[:10])) if obj else []
                    }
                else:
                    return {"type": type(obj).__name__}

            structure = analyze_structure(data)

            return {
                "success": True,
                "file_path": str(file_path),
                "valid": True,
                "structure": structure,
                "file_size": file_path.stat().st_size,
                "encoding": "utf-8"
            }

        except json.JSONDecodeError as e:
            return {
                "success": True,
                "file_path": str(file_path),
                "valid": False,
                "error": f"JSON parsing error: {str(e)}",
                "line": getattr(e, 'lineno', None),
                "column": getattr(e, 'colno', None)
            }
        except UnicodeDecodeError as e:
            return {
                "success": False,
                "error": f"Encoding error: {str(e)}",
                "file_path": str(file_path)
            }

    except Exception as e:
        return {"success": False, "error": f"JSON validation failed: {str(e)}"}


async def _analyze_imports(path: str, recursive: bool, include_hidden: bool, max_results: int, **kwargs) -> dict:
    """Analyze import statements in code files."""
    try:
        from pathlib import Path
        import re

        search_path = Path(path).resolve()

        if not search_path.exists():
            return {"success": False, "error": f"Path not found: {path}"}

        imports = {}
        files_analyzed = 0

        # Get Python files
        if search_path.is_file():
            files_to_analyze = [search_path] if search_path.suffix == '.py' else []
        else:
            files_to_analyze = []
            for file_path in (search_path.rglob("*.py") if recursive else search_path.glob("*.py")):
                if not include_hidden and file_path.name.startswith('.'):
                    continue
                files_to_analyze.append(file_path)

        for file_path in files_to_analyze[:20]:  # Limit files
            try:
                files_analyzed += 1
                content = file_path.read_text(encoding='utf-8', errors='replace')

                # Find import statements
                import_pattern = r'^(?:from\s+([^\s]+)\s+import|import\s+([^\s]+))'
                for match in re.finditer(import_pattern, content, re.MULTILINE):
                    module = match.group(1) or match.group(2)
                    if module:
                        module = module.split('.')[0]  # Get base module
                        if module not in imports:
                            imports[module] = []
                        imports[module].append({
                            "file": str(file_path.relative_to(search_path)),
                            "line": content[:match.start()].count('\n') + 1
                        })

            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")
                continue

        # Sort by usage frequency
        sorted_imports = sorted(imports.items(), key=lambda x: len(x[1]), reverse=True)

        return {
            "success": True,
            "files_analyzed": files_analyzed,
            "total_imports": sum(len(files) for files in imports.values()),
            "unique_modules": len(imports),
            "imports": {module: files[:max_results//len(imports) or 1] for module, files in sorted_imports[:max_results//10 or 10]},
            "truncated": len(sorted_imports) > max_results//10
        }

    except Exception as e:
        return {"success": False, "error": f"Import analysis failed: {str(e)}"}


async def _find_todos(path: str, recursive: bool, include_hidden: bool, max_results: int, **kwargs) -> dict:
    """Find TODO, FIXME, and similar comments in code."""
    try:
        from pathlib import Path
        import re

        search_path = Path(path).resolve()

        if not search_path.exists():
            return {"success": False, "error": f"Path not found: {path}"}

        todos = []
        files_searched = 0

        # Get code files
        if search_path.is_file():
            files_to_search = [search_path]
        else:
            code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs']
            files_to_search = []
            for file_path in (search_path.rglob("*") if recursive else search_path.glob("*")):
                if file_path.is_file() and file_path.suffix.lower() in code_extensions:
                    if not include_hidden and file_path.name.startswith('.'):
                        continue
                    files_to_search.append(file_path)

        # Patterns for different comment styles
        patterns = [
            (r'#\s*(TODO|FIXME|XXX|HACK|NOTE)\s*:\s*(.+)', 'python'),
            (r'//\s*(TODO|FIXME|XXX|HACK|NOTE)\s*:\s*(.+)', 'javascript'),
            (r'/\*\s*(TODO|FIXME|XXX|HACK|NOTE)\s*:\s*(.+?)\s*\*/', 'javascript'),
            (r'<!--\s*(TODO|FIXME|XXX|HACK|NOTE)\s*:\s*(.+?)\s*-->', 'html'),
        ]

        for file_path in files_to_search[:50]:  # Limit files
            try:
                files_searched += 1
                content = file_path.read_text(encoding='utf-8', errors='replace')
                lines = content.splitlines()

                for line_num, line in enumerate(lines, 1):
                    if len(todos) >= max_results:
                        break

                    for pattern, lang in patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            todos.append({
                                "file": str(file_path.relative_to(search_path)),
                                "line_number": line_num,
                                "type": match.group(1).upper(),
                                "content": match.group(2).strip(),
                                "language": lang,
                                "full_line": line.strip()
                            })

            except Exception as e:
                logger.warning(f"Error searching {file_path}: {e}")
                continue

        return {
            "success": True,
            "todos": todos,
            "total_found": len(todos),
            "files_searched": files_searched,
            "truncated": len(todos) > max_results,
            "summary": {
                "TODO": len([t for t in todos if t["type"] == "TODO"]),
                "FIXME": len([t for t in todos if t["type"] == "FIXME"]),
                "XXX": len([t for t in todos if t["type"] == "XXX"]),
                "HACK": len([t for t in todos if t["type"] == "HACK"]),
                "NOTE": len([t for t in todos if t["type"] == "NOTE"])
            }
        }

    except Exception as e:
        return {"success": False, "error": f"TODO search failed: {str(e)}"}


async def _check_file_sizes(path: str, recursive: bool, include_hidden: bool, max_results: int, **kwargs) -> dict:
    """Analyze file sizes and identify large files."""
    try:
        from pathlib import Path

        search_path = Path(path).resolve()

        if not search_path.exists():
            return {"success": False, "error": f"Path not found: {path}"}

        files_info = []

        # Get all files
        if search_path.is_file():
            files_to_check = [search_path]
        else:
            files_to_check = []
            for file_path in (search_path.rglob("*") if recursive else search_path.glob("*")):
                if file_path.is_file():
                    if not include_hidden and file_path.name.startswith('.'):
                        continue
                    files_to_check.append(file_path)

        total_size = 0
        for file_path in files_to_check:
            try:
                stat = file_path.stat()
                size = stat.st_size
                total_size += size

                files_info.append({
                    "path": str(file_path.relative_to(search_path)) if search_path.is_dir() else str(file_path),
                    "size_bytes": size,
                    "size_mb": round(size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "extension": file_path.suffix.lower()
                })

            except Exception as e:
                logger.warning(f"Error checking {file_path}: {e}")
                continue

        # Sort by size (largest first)
        files_info.sort(key=lambda x: x["size_bytes"], reverse=True)

        # Group by extension
        extension_stats = {}
        for file_info in files_info:
            ext = file_info["extension"] or "no_extension"
            if ext not in extension_stats:
                extension_stats[ext] = {"count": 0, "total_size": 0, "avg_size": 0}
            extension_stats[ext]["count"] += 1
            extension_stats[ext]["total_size"] += file_info["size_bytes"]

        for ext, stats in extension_stats.items():
            stats["avg_size"] = round(stats["total_size"] / stats["count"], 2)

        return {
            "success": True,
            "path": str(search_path),
            "total_files": len(files_info),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "largest_files": files_info[:max_results],
            "extension_stats": extension_stats,
            "truncated": len(files_info) > max_results
        }

    except Exception as e:
        return {"success": False, "error": f"File size analysis failed: {str(e)}"}


async def _validate_config(path: str, **kwargs) -> dict:
    """Validate configuration files (JSON, YAML, TOML, INI)."""
    try:
        from pathlib import Path

        file_path = Path(path).resolve()

        if not file_path.exists():
            return {"success": False, "error": f"File not found: {path}"}

        if not file_path.is_file():
            return {"success": False, "error": f"Path is not a file: {path}"}

        suffix = file_path.suffix.lower()
        result = {
            "success": True,
            "file_path": str(file_path),
            "file_type": suffix,
            "valid": False,
            "errors": []
        }

        try:
            if suffix in ['.json']:
                import json
                content = file_path.read_text(encoding='utf-8')
                data = json.loads(content)
                result["valid"] = True
                result["parsed_data"] = data

            elif suffix in ['.yaml', '.yml']:
                try:
                    import yaml
                    content = file_path.read_text(encoding='utf-8')
                    data = yaml.safe_load(content)
                    result["valid"] = True
                    result["parsed_data"] = data
                except ImportError:
                    result["errors"].append("PyYAML not available")

            elif suffix in ['.toml']:
                try:
                    import tomllib
                    content = file_path.read_bytes()
                    data = tomllib.loads(content.decode('utf-8'))
                    result["valid"] = True
                    result["parsed_data"] = data
                except ImportError:
                    result["errors"].append("tomllib not available (Python 3.11+)")

            elif suffix in ['.ini', '.cfg']:
                import configparser
                config = configparser.ConfigParser()
                config.read(file_path, encoding='utf-8')
                result["valid"] = True
                result["sections"] = list(config.sections())

            else:
                result["errors"].append(f"Unsupported config format: {suffix}")

        except Exception as e:
            result["errors"].append(f"Parsing error: {str(e)}")

        return result

    except Exception as e:
        return {"success": False, "error": f"Config validation failed: {str(e)}"}


async def _detect_duplicates(path: str, recursive: bool, include_hidden: bool, max_results: int, **kwargs) -> dict:
    """Find duplicate files based on content hash."""
    try:
        from pathlib import Path
        import hashlib

        search_path = Path(path).resolve()

        if not search_path.exists():
            return {"success": False, "error": f"Path not found: {path}"}

        # Calculate hashes for all files
        file_hashes = {}
        files_processed = 0

        if search_path.is_file():
            files_to_check = [search_path]
        else:
            files_to_check = []
            for file_path in (search_path.rglob("*") if recursive else search_path.glob("*")):
                if file_path.is_file():
                    if not include_hidden and file_path.name.startswith('.'):
                        continue
                    files_to_check.append(file_path)

        for file_path in files_to_check[:1000]:  # Limit files
            try:
                files_processed += 1
                if file_path.stat().st_size > 10 * 1024 * 1024:  # Skip files > 10MB
                    continue

                content = file_path.read_bytes()
                file_hash = hashlib.md5(content).hexdigest()

                if file_hash not in file_hashes:
                    file_hashes[file_hash] = []
                file_hashes[file_hash].append(str(file_path.relative_to(search_path)))

            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")
                continue

        # Find duplicates
        duplicates = []
        for file_hash, files in file_hashes.items():
            if len(files) > 1:
                duplicates.append({
                    "hash": file_hash,
                    "files": files,
                    "count": len(files),
                    "total_size": sum((search_path / f).stat().st_size for f in files)
                })

        # Sort by number of duplicates
        duplicates.sort(key=lambda x: x["count"], reverse=True)

        return {
            "success": True,
            "path": str(search_path),
            "files_processed": files_processed,
            "duplicate_groups": duplicates[:max_results],
            "total_duplicate_groups": len(duplicates),
            "total_duplicated_files": sum(d["count"] for d in duplicates),
            "total_wasted_space": sum(d["total_size"] * (d["count"] - 1) for d in duplicates),
            "truncated": len(duplicates) > max_results
        }

    except Exception as e:
        return {"success": False, "error": f"Duplicate detection failed: {str(e)}"}


async def _analyze_dependencies(path: str, **kwargs) -> dict:
    """Analyze project dependencies from various package managers."""
    try:
        from pathlib import Path
        import json

        project_path = Path(path).resolve()

        if not project_path.exists():
            return {"success": False, "error": f"Path not found: {path}"}

        dependencies = {}

        # Python dependencies
        if (project_path / "requirements.txt").exists():
            try:
                content = (project_path / "requirements.txt").read_text()
                deps = []
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract package name (before ==, >=, etc.)
                        package = line.split()[0].split('>=')[0].split('==')[0].split('<')[0].split('>')[0]
                        deps.append(package)
                dependencies["python_requirements"] = deps
            except Exception as e:
                dependencies["python_requirements_error"] = str(e)

        if (project_path / "pyproject.toml").exists():
            try:
                import tomllib
                content = (project_path / "pyproject.toml").read_bytes()
                data = tomllib.loads(content.decode('utf-8'))

                poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
                if poetry_deps:
                    dependencies["python_poetry"] = list(poetry_deps.keys())

                pep621_deps = data.get("project", {}).get("dependencies", [])
                if pep621_deps:
                    dependencies["python_pep621"] = pep621_deps

            except Exception as e:
                dependencies["python_pyproject_error"] = str(e)

        # JavaScript/Node.js dependencies
        if (project_path / "package.json").exists():
            try:
                content = (project_path / "package.json").read_text()
                data = json.loads(content)

                if "dependencies" in data:
                    dependencies["javascript_dependencies"] = list(data["dependencies"].keys())
                if "devDependencies" in data:
                    dependencies["javascript_devDependencies"] = list(data["devDependencies"].keys())

            except Exception as e:
                dependencies["javascript_error"] = str(e)

        # Rust dependencies
        if (project_path / "Cargo.toml").exists():
            try:
                import tomllib
                content = (project_path / "Cargo.toml").read_bytes()
                data = tomllib.loads(content.decode('utf-8'))

                deps = data.get("dependencies", {})
                if deps:
                    dependencies["rust_dependencies"] = list(deps.keys())

            except Exception as e:
                dependencies["rust_error"] = str(e)

        # Go dependencies
        if (project_path / "go.mod").exists():
            try:
                content = (project_path / "go.mod").read_text()
                deps = []
                for line in content.splitlines():
                    if line.startswith("require "):
                        # Parse require block
                        continue
                    elif line.strip().startswith("github.com/") or line.strip().startswith("golang.org/"):
                        deps.append(line.strip().split()[0])
                dependencies["go_dependencies"] = deps
            except Exception as e:
                dependencies["go_error"] = str(e)

        return {
            "success": True,
            "project_path": str(project_path),
            "dependencies": dependencies,
            "total_dependencies": sum(len(deps) for deps in dependencies.values() if isinstance(deps, list)),
            "package_managers": list(dependencies.keys())
        }

    except Exception as e:
        return {"success": False, "error": f"Dependency analysis failed: {str(e)}"}