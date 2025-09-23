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
        return {
            "name": tool_name,
            "category": category,
            "description": tool_info["description"],
            "parameters": tool_info["parameters"],
            "examples": tool_info["examples"],
            "use_cases": tool_info["use_cases"]
        }

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
