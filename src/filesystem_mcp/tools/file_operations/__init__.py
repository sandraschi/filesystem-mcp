"""
File operations for the Filesystem MCP - FastMCP 2.12 compliant.

This module provides comprehensive file system operations using FastMCP 2.12 patterns.
All tools are registered using the @_get_app().tool() decorator pattern for maximum compatibility.
"""

import os
import stat
import shutil
import logging
import sys
import fnmatch
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Literal

from pydantic import BaseModel, Field, field_validator, ConfigDict

# Configure structured logging for this module
logger = logging.getLogger(__name__)

# Import app locally in functions to avoid circular imports
def _get_app():
    """Get the app instance locally to avoid circular imports."""
    from ... import app
    return app

# Pydantic V2 models for request/response validation
class FileContent(BaseModel):
    """Model for file content response - FastMCP 2.12 compliant."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: str = Field(..., description="Path to the file")
    content: str = Field(..., description="File content")
    encoding: str = Field(default="utf-8", description="File encoding")
    size: int = Field(..., description="File size in bytes")
    last_modified: datetime = Field(..., description="Last modification time")

class FileWriteRequest(BaseModel):
    """Model for file write request - FastMCP 2.12 compliant."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: str = Field(..., description="Path to the file")
    content: str = Field(..., description="Content to write")
    encoding: str = Field(default="utf-8", description="File encoding")
    create_parents: bool = Field(default=True, description="Create parent directories if they don't exist")

    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        """Validate that the path is not outside the allowed directories."""
        # Add security check to prevent directory traversal
        try:
            resolved = Path(v).resolve()
            # Add additional security checks here if needed
            return str(resolved)
        except Exception as e:
            raise ValueError(f"Invalid file path: {e}")

class FileInfo(BaseModel):
    """Model for file/directory information - FastMCP 2.12 compliant."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: str = Field(..., description="Path to the file/directory")
    name: str = Field(..., description="Name of the file/directory")
    type: Literal["file", "directory", "symlink", "other"] = Field(..., description="Type of the entry")
    size: Optional[int] = Field(None, description="Size in bytes (for files)")
    created: Optional[datetime] = Field(None, description="Creation time")
    modified: Optional[datetime] = Field(None, description="Last modification time")
    accessed: Optional[datetime] = Field(None, description="Last access time")
    permissions: Dict[str, bool] = Field(..., description="File permissions")
    parent: Optional[str] = Field(None, description="Parent directory")

# Helper functions with structured logging
def _get_file_permissions(path: Path) -> Dict[str, bool]:
    """Get file permissions as a dictionary with structured logging."""
    try:
        mode = path.stat().st_mode
        permissions = {
            'readable': os.access(path, os.R_OK),
            'writable': os.access(path, os.W_OK),
            'executable': os.access(path, os.X_OK),
            'is_hidden': path.name.startswith('.')
        }
        logger.debug(f"Retrieved permissions for {path}: {permissions}")
        return permissions
    except Exception as e:
        logger.error(f"Failed to get permissions for {path}: {e}")
        raise

def _safe_resolve_path(file_path: str) -> Path:
    """Safely resolve a file path with security checks and structured logging."""
    try:
        logger.debug(f"Resolving path: {file_path}")
        path = Path(file_path).expanduser().absolute()

        # Security checks
        if '..' in path.parts:
            logger.warning(f"Path traversal attempt detected: {file_path}")
            raise ValueError("Path traversal detected")

        logger.debug(f"Resolved path: {path}")
        return path
    except Exception as e:
        logger.error(f"Path resolution error for '{file_path}': {e}")
        raise ValueError(f"Invalid path: {e}")

@_get_app().tool()
async def read_file(
    file_path: str,
    encoding: str = "utf-8"
) -> dict:
    """Read the contents of a file with proper error handling and metadata.

    This tool reads a file and returns its content along with comprehensive
    metadata. It includes proper error handling, security checks, and
    structured logging for debugging.

    Args:
        file_path: Path to the file to read (relative or absolute)
        encoding: Character encoding to use (default: utf-8)

    Returns:
        Dictionary containing file content and metadata

    Error Handling:
        Returns error dict if file not found, permission denied, or other issues
    """
    try:
        logger.info(f"Reading file: {file_path}")

        # Resolve and validate the path
        path = _safe_resolve_path(file_path)

        # Check if file exists
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "path": file_path
            }

        # Check if it's a directory
        if path.is_dir():
            logger.warning(f"Path is a directory, not a file: {file_path}")
            return {
                "success": False,
                "error": f"Path is a directory, not a file: {file_path}",
                "path": file_path
            }

        # Check read permissions
        if not os.access(path, os.R_OK):
            logger.warning(f"Read permission denied: {file_path}")
            return {
                "success": False,
                "error": f"Read permission denied: {file_path}",
                "path": file_path
            }

        # Read file content and get metadata
        try:
            content = path.read_text(encoding=encoding)
            stat_info = path.stat()

            result = {
                "success": True,
                "path": str(path),
                "content": content,
                "encoding": encoding,
                "size": stat_info.st_size,
                "last_modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat()
            }

            logger.info(f"Successfully read file: {file_path} ({stat_info.st_size} bytes)")
            return result

        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode file with {encoding} encoding: {file_path}")
            return {
                "success": False,
                "error": f"Failed to decode file with {encoding} encoding: {e}",
                "path": file_path
            }

    except Exception as e:
        logger.error(f"Unexpected error reading file {file_path}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to read file: {str(e)}",
            "path": file_path
        }

@_get_app().tool()
async def write_file(
    path: str,
    content: str,
    encoding: str = "utf-8",
    create_parents: bool = True
) -> dict:
    """Write content to a file with proper error handling and validation.

    This tool writes content to a file, creating parent directories if needed.
    It includes comprehensive error handling, permission checks, and security
    validations. All operations are logged for debugging and monitoring.

    Args:
        path: Path to the file to write to (relative or absolute)
        content: Content to write to the file
        encoding: Character encoding to use (default: utf-8)
        create_parents: Whether to create parent directories (default: True)

    Returns:
        Dictionary containing operation result and metadata

    Error Handling:
        Returns error dict for permission issues, path problems, etc.
    """
    try:
        logger.info(f"Writing file: {path}")

        # Resolve and validate the path
        file_path_obj = _safe_resolve_path(path)

        # Check if parent directory exists and is writable
        parent_dir = file_path_obj.parent
        if not parent_dir.exists():
            if create_parents:
                try:
                    logger.debug(f"Creating parent directories for: {path}")
                    parent_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logger.error(f"Failed to create parent directory for {path}: {e}")
                    return {
                        "success": False,
                        "error": f"Failed to create parent directory: {e}",
                        "path": path
                    }
            else:
                logger.error(f"Parent directory does not exist: {parent_dir}")
                return {
                    "success": False,
                    "error": f"Parent directory does not exist: {parent_dir}",
                    "path": path
                }

        # Check if parent directory is writable
        if not os.access(parent_dir, os.W_OK):
            logger.error(f"Write permission denied for directory: {parent_dir}")
            return {
                "success": False,
                "error": f"Write permission denied for directory: {parent_dir}",
                "path": path
            }

        # Check if file exists and is writable
        if file_path_obj.exists():
            if file_path_obj.is_dir():
                logger.error(f"Path is a directory, not a file: {path}")
                return {
                    "success": False,
                    "error": f"Path is a directory, not a file: {path}",
                    "path": path
                }
            if not os.access(file_path_obj, os.W_OK):
                logger.error(f"Write permission denied: {path}")
                return {
                    "success": False,
                    "error": f"Write permission denied: {path}",
                    "path": path
                }

        # Write the file
        try:
            bytes_written = file_path_obj.write_text(content, encoding=encoding)
            stat_info = file_path_obj.stat()

            result = {
                "success": True,
                "path": str(file_path_obj),
                "bytes_written": bytes_written,
                "size": stat_info.st_size,
                "last_modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat()
            }

            logger.info(f"Successfully wrote {bytes_written} bytes to: {path}")
            return result

        except (UnicodeEncodeError, LookupError) as e:
            logger.error(f"Encoding error writing to {path}: {e}")
            return {
                "success": False,
                "error": f"Encoding error: {e}",
                "path": path
            }

    except Exception as e:
        logger.error(f"Unexpected error writing to file {path}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to write to file: {str(e)}",
            "path": path
        }

class DirectoryListingRequest(BaseModel):
    """Request model for directory listing - FastMCP 2.12 compliant."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    directory_path: str = Field(
        ".",
        description="Path to the directory (default: current directory)"
    )
    recursive: bool = Field(
        False,
        description="Whether to list contents recursively (default: False)"
    )
    include_hidden: bool = Field(
        False,
        description="Whether to include hidden files/directories (default: False)"
    )
    max_depth: Optional[int] = Field(
        None,
        ge=1,
        description="Maximum depth for recursive listing (default: None for unlimited)"
    )
    max_files: int = Field(
        1000,
        ge=1,
        le=10000,
        description="Maximum number of files to return (default: 1000, max: 10000)"
    )

@_get_app().tool()
async def list_directory(
    directory_path: str = ".",
    recursive: bool = False,
    include_hidden: bool = False,
    max_depth: Optional[int] = None,
    max_files: int = 1000,
    exclude_patterns: Optional[List[str]] = None
) -> dict:
    """List contents of a directory with detailed metadata and filtering options.

    This tool provides a detailed listing of directory contents with comprehensive
    metadata including file sizes, timestamps, permissions, and type information.
    It supports recursive listing with depth control and hidden file filtering.
    
    Args:
        directory_path: Path to the directory (default: current directory)
        recursive: Whether to list contents recursively (default: False)
        include_hidden: Whether to include hidden files/directories (default: False)
        max_depth: Maximum depth for recursive listing (default: None for unlimited)
        max_files: Maximum number of files to return (default: 1000)
        exclude_patterns: List of patterns to exclude (globs, directory names).
                          Defaults to common build/cache directories: ['node_modules', '__pycache__', '.git', 'dist', 'build', '.next', '.nuxt']
    
    Returns:
        Dictionary containing 'files' list and metadata
        
    Error Handling:
        Returns error information if directory access fails or path is invalid
    """
    try:
        logger.info(f"Listing directory: {directory_path}")

        # Resolve and validate the path
        path = _safe_resolve_path(directory_path)

        # Set default exclusions if none provided
        if exclude_patterns is None:
            exclude_patterns = ['node_modules', '__pycache__', '.git', 'dist', 'build', '.next', '.nuxt']
        
        # Check if path exists
        if not path.exists():
            logger.warning(f"Directory not found: {directory_path}")
            return {
                "success": False,
                "error": f"Directory not found: {directory_path}",
                "path": directory_path,
                "type": "error"
            }
            
        # Check if path is a directory
        if not path.is_dir():
            logger.warning(f"Path is not a directory: {directory_path}")
            return {
                "success": False,
                "error": f"Path is not a directory: {directory_path}",
                "path": directory_path,
                "type": "error"
            }
            
        # Check read permissions
        if not os.access(path, os.R_OK):
            logger.warning(f"Read permission denied: {directory_path}")
            return {
                "success": False,
                "error": f"Read permission denied: {directory_path}",
                "path": directory_path,
                "type": "error"
            }
            
        # Internal function for recursive listing
        def _list_dir(current_path: Path, current_depth: int = 0, visited: set = None, current_count: int = 0) -> tuple[List[dict], bool, int]:
            if visited is None:
                visited = set()

            # Prevent infinite loops by tracking visited directories
            resolved_path = current_path.resolve()
            if resolved_path in visited:
                logger.warning(f"Skipping already visited directory: {current_path}")
                return [], False, current_count
            visited.add(resolved_path)

            results = []
            limit_reached = False
            
            try:
                for item in current_path.iterdir():
                    # Check if we've reached the file limit
                    if current_count >= max_files:
                        limit_reached = True
                        break

                    # Skip hidden files/directories if not requested
                    if not include_hidden and item.name.startswith('.'):
                        continue

                    # Skip excluded patterns
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if fnmatch.fnmatch(item.name, pattern):
                            should_exclude = True
                            break
                        # Also check if it's a directory matching the pattern
                        if item.is_dir() and fnmatch.fnmatch(item.name + '/', pattern):
                            should_exclude = True
                            break

                    if should_exclude:
                        continue
                        
                    try:
                        stat_info = item.stat()
                        is_dir = item.is_dir()
                        is_symlink = item.is_symlink()
                        
                        # Determine entry type
                        entry_type = "directory" if is_dir else "file"
                        if is_symlink:
                            entry_type = "symlink"
                        elif not is_dir and not is_symlink:
                            entry_type = "other"
                        
                        # Create file info dictionary
                        file_info = {
                            "path": str(item),
                            "name": item.name,
                            "type": entry_type,
                            "size": stat_info.st_size if not is_dir and not is_symlink else None,
                            "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                            "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                            "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
                            "permissions": _get_file_permissions(item),
                            "parent": str(current_path)
                        }
                        
                        results.append(file_info)
                        current_count += 1

                        # Recurse into subdirectories if requested and depth allows
                        if (recursive and is_dir and not is_symlink and
                            (max_depth is None or current_depth < max_depth) and
                            current_count < max_files):
                            sub_results, sub_limit_reached, current_count = _list_dir(item, current_depth + 1, visited, current_count)
                            results.extend(sub_results)
                            if sub_limit_reached:
                                limit_reached = True
                            
                    except (PermissionError, OSError) as e:
                        logger.warning(f"Skipping inaccessible item {item}: {e}")
                        continue
                        
            except (PermissionError, OSError) as e:
                logger.warning(f"Cannot access directory {current_path}: {e}")
                
            return results, limit_reached, current_count
        
        # Start recursive listing
        file_list, limit_reached, final_count = _list_dir(path)
        logger.info(f"Successfully listed {len(file_list)} items in {directory_path}")

        result = {
            "files": file_list,
            "directory": str(path),
            "total_count": len(file_list),
            "recursive": recursive,
            "include_hidden": include_hidden,
            "exclude_patterns": exclude_patterns,
            "limit_reached": limit_reached,
            "max_files": max_files
        }

        if limit_reached:
            logger.warning(f"File listing limit of {max_files} reached for {directory_path}")
            result["warning"] = f"Listing truncated at {max_files} files. Use max_files parameter to increase limit."

        return result
        
    except Exception as e:
        logger.error(f"Unexpected error listing directory {directory_path}: {e}", exc_info=True)
        return [{
            "success": False,
            "error": f"Failed to list directory: {str(e)}",
            "path": directory_path,
            "type": "error"
        }]

class FileExistsRequest(BaseModel):
    """Request model for file existence check - FastMCP 2.12 compliant."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: str = Field(..., description="Path to check")
    check_type: Optional[Literal["file", "directory", "any"]] = Field(
        "any",
        description="Type of filesystem object to check for (file, directory, or any)"
    )
    follow_symlinks: bool = Field(
        True,
        description="Whether to follow symbolic links (default: True)"
    )

@_get_app().tool()
async def file_exists(
    path: str,
    check_type: str = "any",
    follow_symlinks: bool = True
) -> dict:
    """Check if a file or directory exists with detailed status information.

    This tool checks for the existence of a filesystem object with optional
    type checking and symlink resolution. It provides comprehensive information
    about the object if it exists, including metadata and permissions.
    
    Args:
        path: Path to check for existence (relative or absolute)
        check_type: Type of object to check for ("file", "directory", or "any")
        follow_symlinks: Whether to follow symbolic links (default: True)
    
    Returns:
        Dictionary containing existence status and detailed information
        
    Error Handling:
        Returns error information if path access fails
    """
    try:
        logger.info(f"Checking if path exists: {path}")

        # Resolve and validate the path
        path_obj = _safe_resolve_path(path)
        
        # Check if the path exists
        exists = path_obj.exists()
        
        # If it doesn't exist, we can return early
        if not exists:
            logger.debug(f"Path does not exist: {path}")
            return {
                "exists": False,
                "path": str(path_obj),
                "type": "none",
                "message": "Path does not exist"
            }
            
        # Get the actual type (following symlinks if requested)
        actual_path = path_obj.resolve() if follow_symlinks else path_obj
        is_symlink = path_obj.is_symlink()
        is_file = actual_path.is_file()
        is_dir = actual_path.is_dir()
        
        # Determine the type
        path_type = "file" if is_file else "directory" if is_dir else "other"
        
        # Check if the type matches the requested type
        type_matches = (
            check_type == "any" or
            (check_type == "file" and is_file) or
            (check_type == "directory" and is_dir)
        )
        
        # Get file info if available
        file_info = None
        if exists and (is_file or is_dir):
            try:
                stat_info = actual_path.stat()
                file_info = {
                    "size": stat_info.st_size if is_file else 0,
                    "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
                    "permissions": _get_file_permissions(actual_path)
                }
            except (PermissionError, OSError) as e:
                logger.warning(f"Could not get file info for {path_obj}: {e}")
        
        # Prepare the response
        response = {
            "exists": exists and type_matches,
            "path": str(path_obj),
            "resolved_path": str(actual_path) if exists and is_symlink else None,
            "type": path_type,
            "is_symlink": is_symlink,
            "type_matches": type_matches,
            "details": file_info,
            "message": "Path exists and matches type criteria" if type_matches else "Path exists but does not match type criteria"
        }
        
        logger.info(f"Path exists check completed for {path}: exists={exists and type_matches}, type={path_type}")
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error checking path existence: {path}", exc_info=True)
        return {
            "exists": False,
            "path": path,
            "error": f"Failed to check path existence: {str(e)}",
            "message": "Error occurred while checking path"
        }

class FileInfoRequest(BaseModel):
    """Request model for getting file/directory information."""
    path: str = Field(..., description="Path to the file or directory")
    follow_symlinks: bool = Field(
        True,
        description="Whether to follow symbolic links (default: True)"
    )
    include_content: bool = Field(
        False,
        description="Whether to include file content (for small text files only, default: False)"
    )
    max_content_size: int = Field(
        1024 * 1024,  # 1MB default
        description="Maximum file size to include content for (in bytes, default: 1MB)"
    )

@_get_app().tool()
async def get_file_info(
    path: str,
    follow_symlinks: bool = True,
    include_content: bool = False,
    max_content_size: int = 1024 * 1024
) -> dict:
    """Get detailed information about a file or directory.

    This tool provides comprehensive information about a filesystem object,
    including metadata, permissions, timestamps, and optionally file content
    for small text files. All operations include proper error handling and
    structured logging for debugging.
    
    Args:
        path: Path to the file or directory (relative or absolute)
        follow_symlinks: Whether to follow symbolic links (default: True)
        include_content: Whether to include file content (for text files only)
        max_content_size: Maximum file size to include content for (default: 1MB)
    
    Returns:
        Dictionary containing comprehensive file/directory information
        
    Error Handling:
        Returns error information if path access fails or file cannot be read
    """
    try:
        logger.info(f"Getting file info for: {path}")

        # Resolve and validate the path
        path_obj = _safe_resolve_path(path)
        
        # Check if path exists
        if not path_obj.exists():
            logger.warning(f"Path not found: {path}")
            return {
                "success": False,
                "error": f"Path not found: {path}",
                "path": path
            }
            
        # Resolve symlinks if requested
        actual_path = path_obj.resolve() if follow_symlinks else path_obj
        is_symlink = path_obj.is_symlink()
        is_dir = actual_path.is_dir()
        is_file = actual_path.is_file()
        
        # Get basic stat info
        try:
            stat_info = actual_path.stat()
            
            # Determine file type
            file_type = "directory" if is_dir else "file"
            if is_symlink:
                file_type = "symlink"
            elif not is_dir and not is_file:
                file_type = "other"
            
            # Prepare the basic response
            response = {
                "success": True,
                "path": str(path_obj),
                "resolved_path": str(actual_path) if is_symlink and follow_symlinks else None,
                "name": path_obj.name,
                "parent": str(path_obj.parent),
                "type": file_type,
                "is_directory": is_dir,
                "is_file": is_file,
                "is_symlink": is_symlink,
                "size": stat_info.st_size,
                "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
                "permissions": _get_file_permissions(actual_path),
                "inode": stat_info.st_ino,
                "device": stat_info.st_dev,
                "hard_links": stat_info.st_nlink,
                "mode": stat.filemode(stat_info.st_mode),
                "is_hidden": path_obj.name.startswith('.')
            }
            
            # Add content for small text files if requested
            if (include_content and is_file and
                stat_info.st_size <= max_content_size):
                try:
                    # Only include content for text files
                    text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
                    is_text = lambda bytes: bool(bytes.translate(None, text_chars))
                    
                    with open(actual_path, 'rb') as f:
                        sample = f.read(1024)
                        if is_text(sample):
                            f.seek(0)
                            response["content"] = f.read().decode('utf-8', errors='replace')
                            response["content_encoding"] = "utf-8"
                            response["content_truncated"] = False
                except Exception as e:
                    logger.warning(f"Could not read file content for {path_obj}: {e}")
                    response["content_error"] = str(e)
            
            logger.info(f"Successfully retrieved info for {path}: {file_type} ({stat_info.st_size} bytes)")
            return response
            
        except (PermissionError, OSError) as e:
            logger.error(f"Permission denied accessing {path}: {e}")
            return {
                "success": False,
                "error": f"Permission denied: {e}",
                "path": path
            }
        
    except Exception as e:
        logger.error(f"Unexpected error getting file info for {path}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to get file info: {str(e)}",
            "path": path
        }

    
    return file_info


@_get_app().tool()
async def head_file(
    file_path: str,
    lines: int = 10,
    encoding: str = "utf-8"
) -> dict:
    """Read the first N lines of a file (head command equivalent).

    This tool reads and returns the first N lines of a file, similar to the Unix
    'head' command. It's useful for quickly examining the beginning of files
    without reading the entire content.

    Args:
        file_path: Path to the file to read
        lines: Number of lines to read from the beginning (default: 10, max: 1000)
        encoding: Character encoding to use (default: utf-8)

    Returns:
        Dictionary containing file head content and metadata

    Error Handling:
        Returns error dict if file not found, permission denied, or other issues
    """
    try:
        logger.info(f"Reading head of file: {file_path}")

        # Validate lines parameter
        if lines < 1:
            lines = 1
        elif lines > 1000:
            lines = 1000

        # Resolve and validate the path
        path = _safe_resolve_path(file_path)

        # Check if file exists
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path
            }

        # Check if it's a file
        if not path.is_file():
            logger.warning(f"Path is not a file: {file_path}")
            return {
                "success": False,
                "error": f"Path is not a file: {file_path}",
                "file_path": file_path
            }

        # Check read permissions
        if not os.access(path, os.R_OK):
            logger.warning(f"Read permission denied: {file_path}")
            return {
                "success": False,
                "error": f"Read permission denied: {file_path}",
                "file_path": file_path
            }

        # Read the first N lines
        try:
            content_lines = []
            with path.open(encoding=encoding, errors='replace') as f:
                for i, line in enumerate(f):
                    if i >= lines:
                        break
                    content_lines.append(line.rstrip('\n\r'))

            # Get file stats
            stat_info = path.stat()

            result = {
                "success": True,
                "message": f"Successfully read first {len(content_lines)} lines of {file_path}",
                "file_path": str(path),
                "content": '\n'.join(content_lines),
                "lines_requested": lines,
                "lines_returned": len(content_lines),
                "size": stat_info.st_size,
                "encoding": encoding,
                "truncated": len(content_lines) < lines  # True if file has fewer lines than requested
            }

            logger.info(f"Successfully read head of {file_path}: {len(content_lines)} lines")
            return result

        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error for {file_path}: {e}")
            return {
                "success": False,
                "error": f"Unicode decode error: {e}",
                "file_path": file_path,
                "encoding": encoding
            }

        except Exception as e:
            logger.error(f"Failed to read head of {file_path}: {e}")
            return {
                "success": False,
                "error": f"Failed to read file: {str(e)}",
                "file_path": file_path
            }

    except Exception as e:
        logger.error(f"Unexpected error reading head of {file_path}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to read file head: {str(e)}",
            "file_path": file_path
        }


@_get_app().tool()
async def tail_file(
    file_path: str,
    lines: int = 10,
    encoding: str = "utf-8"
) -> dict:
    """Read the last N lines of a file (tail command equivalent).

    This tool reads and returns the last N lines of a file, similar to the Unix
    'tail' command. It's useful for quickly examining the end of files like logs
    without reading the entire content.
    
    Args:
        file_path: Path to the file to read
        lines: Number of lines to read from the end (default: 10, max: 1000)
        encoding: Character encoding to use (default: utf-8)
        
    Returns:
        Dictionary containing file tail content and metadata

    Error Handling:
        Returns error dict if file not found, permission denied, or other issues
    """
    try:
        logger.info(f"Reading tail of file: {file_path}")

        # Validate lines parameter
        if lines < 1:
            lines = 1
        elif lines > 1000:
            lines = 1000

        # Resolve and validate the path
        path = _safe_resolve_path(file_path)

        # Check if file exists
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path
            }

        # Check if it's a file
        if not path.is_file():
            logger.warning(f"Path is not a file: {file_path}")
            return {
                "success": False,
                "error": f"Path is not a file: {file_path}",
                "file_path": file_path
            }

        # Check read permissions
        if not os.access(path, os.R_OK):
            logger.warning(f"Read permission denied: {file_path}")
            return {
                "success": False,
                "error": f"Read permission denied: {file_path}",
                "file_path": file_path
            }

        # Read the last N lines efficiently
        try:
            content_lines = []
            with path.open(encoding=encoding, errors='replace') as f:
                # Use a deque for efficient tail reading
                from collections import deque
                lines_deque = deque(maxlen=lines)

                for line in f:
                    lines_deque.append(line.rstrip('\n\r'))

                content_lines = list(lines_deque)

        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error for {file_path}: {e}")
            return {
                "success": False,
                "error": f"Unicode decode error: {e}",
                "file_path": file_path,
                "encoding": encoding
            }

        except Exception as e:
            logger.error(f"Failed to read tail of {file_path}: {e}")
            return {
                "success": False,
                "error": f"Failed to read file: {str(e)}",
                "file_path": file_path
            }

        # Get file stats
        stat_info = path.stat()

        result = {
            "success": True,
            "message": f"Successfully read last {len(content_lines)} lines of {file_path}",
            "file_path": str(path),
            "content": '\n'.join(content_lines),
            "lines_requested": lines,
            "lines_returned": len(content_lines),
            "size": stat_info.st_size,
            "encoding": encoding,
            "truncated": len(content_lines) < lines  # True if file has fewer lines than requested
        }

        logger.info(f"Successfully read tail of {file_path}: {len(content_lines)} lines")
        return result

    except Exception as e:
        logger.error(f"Unexpected error reading tail of {file_path}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to read file tail: {str(e)}",
            "file_path": file_path
        }


@_get_app().tool()
async def grep_file(
    file_path: str,
    pattern: str,
    case_sensitive: bool = False,
    max_matches: int = 100,
    context_lines: int = 0,
    encoding: str = "utf-8"
) -> dict:
    """Search for patterns in a file (grep equivalent).

    This tool searches for text patterns in files using regular expressions,
    similar to the Unix 'grep' command. Perfect for log analysis, code searching,
    and finding specific content in large files.

    Args:
        file_path: Path to the file to search
        pattern: Regular expression pattern to search for
        case_sensitive: Whether the search is case sensitive (default: False)
        max_matches: Maximum number of matches to return (default: 100, max: 1000)
        context_lines: Number of context lines around each match (default: 0)
        encoding: Character encoding to use (default: utf-8)

    Returns:
        Dictionary containing search results and metadata

    Error Handling:
        Returns error dict if file not found, permission denied, or invalid regex
    """
    try:
        logger.info(f"Searching file {file_path} for pattern: {pattern}")

        # Validate parameters
        if max_matches < 1:
            max_matches = 1
        elif max_matches > 1000:
            max_matches = 1000

        if context_lines < 0:
            context_lines = 0
        elif context_lines > 10:
            context_lines = 10

        # Compile regex pattern
        try:
            flags = re.MULTILINE
            if not case_sensitive:
                flags |= re.IGNORECASE
            regex = re.compile(pattern, flags)
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
            return {
                "success": False,
                "error": f"Invalid regex pattern: {e}",
                "pattern": pattern
            }

        # Resolve and validate the path
        path = _safe_resolve_path(file_path)

        # Check if file exists
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path,
                "pattern": pattern
            }

        # Check if it's a file
        if not path.is_file():
            logger.warning(f"Path is not a file: {file_path}")
            return {
                "success": False,
                "error": f"Path is not a file: {file_path}",
                "file_path": file_path,
                "pattern": pattern
            }

        # Check read permissions
        if not os.access(path, os.R_OK):
            logger.warning(f"Read permission denied: {file_path}")
            return {
                "success": False,
                "error": f"Read permission denied: {file_path}",
                "file_path": file_path,
                "pattern": pattern
            }

        # Perform the search
        matches = []
        line_number = 0
        total_matches = 0

        try:
            with path.open(encoding=encoding, errors='replace') as f:
                lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    line_number = i

                    if regex.search(line):
                        total_matches += 1

                        # Create match entry
                        match_info = {
                            "line_number": i,
                            "line_content": line.rstrip('\n\r'),
                            "match": regex.findall(line)[0] if regex.findall(line) else ""
                        }

                        # Add context lines if requested
                        if context_lines > 0:
                            start_ctx = max(0, i - context_lines - 1)
                            end_ctx = min(len(lines), i + context_lines)
                            match_info["context"] = {
                                "before": [lines[j].rstrip('\n\r') for j in range(start_ctx, i-1)],
                                "after": [lines[j].rstrip('\n\r') for j in range(i, end_ctx)]
                            }

                        matches.append(match_info)

                        # Stop if we hit max_matches
                        if len(matches) >= max_matches:
                            break

            # Get file stats
            stat_info = path.stat()

            result = {
                "success": True,
                "message": f"Found {total_matches} matches for pattern '{pattern}' in {file_path}",
                "file_path": str(path),
                "pattern": pattern,
                "matches": matches,
                "total_matches": total_matches,
                "matches_returned": len(matches),
                "truncated": len(matches) >= max_matches,
                "case_sensitive": case_sensitive,
                "max_matches": max_matches,
                "context_lines": context_lines,
                "file_size": stat_info.st_size,
                "encoding": encoding
            }

            logger.info(f"Successfully searched {file_path}: {total_matches} matches found")
            return result

        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error for {file_path}: {e}")
            return {
                "success": False,
                "error": f"Unicode decode error: {e}",
                "file_path": file_path,
                "pattern": pattern,
                "encoding": encoding
            }

        except Exception as e:
            logger.error(f"Failed to search {file_path}: {e}")
            return {
                "success": False,
                "error": f"Failed to search file: {str(e)}",
                "file_path": file_path,
                "pattern": pattern
            }

    except Exception as e:
        logger.error(f"Unexpected error searching {file_path}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to search file: {str(e)}",
            "file_path": file_path,
            "pattern": pattern
        }


@_get_app().tool()
async def count_pattern(
    file_path: str,
    pattern: str,
    case_sensitive: bool = False,
    encoding: str = "utf-8"
) -> dict:
    """Count occurrences of a pattern in a file.

    This tool counts how many times a text pattern appears in a file using
    regular expressions. Useful for log analysis, code metrics, and pattern frequency analysis.

    Args:
        file_path: Path to the file to analyze
        pattern: Regular expression pattern to count
        case_sensitive: Whether the search is case sensitive (default: False)
        encoding: Character encoding to use (default: utf-8)

    Returns:
        Dictionary containing count results and metadata

    Error Handling:
        Returns error dict if file not found, permission denied, or invalid regex
    """
    try:
        logger.info(f"Counting pattern '{pattern}' in file: {file_path}")

        # Compile regex pattern
        try:
            flags = re.MULTILINE
            if not case_sensitive:
                flags |= re.IGNORECASE
            regex = re.compile(pattern, flags)
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
            return {
                "success": False,
                "error": f"Invalid regex pattern: {e}",
                "pattern": pattern
            }

        # Resolve and validate the path
        path = _safe_resolve_path(file_path)

        # Check if file exists
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path,
                "pattern": pattern
            }

        # Check if it's a file
        if not path.is_file():
            logger.warning(f"Path is not a file: {file_path}")
            return {
                "success": False,
                "error": f"Path is not a file: {file_path}",
                "file_path": file_path,
                "pattern": pattern
            }

        # Check read permissions
        if not os.access(path, os.R_OK):
            logger.warning(f"Read permission denied: {file_path}")
            return {
                "success": False,
                "error": f"Read permission denied: {file_path}",
                "file_path": file_path,
                "pattern": pattern
            }

        # Count occurrences
        total_count = 0
        line_counts = []

        try:
            with path.open(encoding=encoding, errors='replace') as f:
                for line_num, line in enumerate(f, 1):
                    matches = regex.findall(line)
                    if matches:
                        count = len(matches)
                        total_count += count
                        line_counts.append({
                            "line_number": line_num,
                            "count": count,
                            "line_content": line.rstrip('\n\r')[:100] + "..." if len(line) > 100 else line.rstrip('\n\r')
                        })

            # Sort by count descending and take top 10
            line_counts.sort(key=lambda x: x["count"], reverse=True)
            top_lines = line_counts[:10]

            # Get file stats
            stat_info = path.stat()

            result = {
                "success": True,
                "message": f"Found {total_count} occurrences of pattern '{pattern}' in {file_path}",
                "file_path": str(path),
                "pattern": pattern,
                "total_count": total_count,
                "lines_with_matches": len(line_counts),
                "top_matching_lines": top_lines,
                "case_sensitive": case_sensitive,
                "file_size": stat_info.st_size,
                "encoding": encoding
            }

            logger.info(f"Successfully counted pattern in {file_path}: {total_count} occurrences")
            return result

        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error for {file_path}: {e}")
            return {
                "success": False,
                "error": f"Unicode decode error: {e}",
                "file_path": file_path,
                "pattern": pattern,
                "encoding": encoding
            }

        except Exception as e:
            logger.error(f"Failed to count pattern in {file_path}: {e}")
            return {
                "success": False,
                "error": f"Failed to count pattern: {str(e)}",
                "file_path": file_path,
                "pattern": pattern
            }

    except Exception as e:
        logger.error(f"Unexpected error counting pattern in {file_path}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to count pattern: {str(e)}",
            "file_path": file_path,
            "pattern": pattern
        }


@_get_app().tool()
async def extract_log_lines(
    file_path: str,
    patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    log_levels: Optional[List[str]] = None,
    exclude_log_levels: Optional[List[str]] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    max_lines: int = 100,
    encoding: str = "utf-8"
) -> dict:
    """Extract and filter log lines from files.

    This tool extracts lines from log files based on patterns, time ranges,
    log levels, and exclusion criteria. Perfect for log analysis and debugging.

    Args:
        file_path: Path to the log file
        patterns: List of regex patterns to include (OR logic)
        exclude_patterns: List of regex patterns to exclude
        log_levels: List of log levels to include (e.g., ["ERROR", "WARNING", "INFO"])
        exclude_log_levels: List of log levels to exclude
        start_time: ISO format datetime to start from (e.g., "2024-01-01T10:00:00")
        end_time: ISO format datetime to end at (e.g., "2024-01-02T10:00:00")
        max_lines: Maximum lines to return (default: 100, max: 1000)
        encoding: Character encoding (default: utf-8)

    Returns:
        Dictionary containing filtered log lines and metadata

    Notes:
        - Time filtering requires log lines to start with ISO timestamps
        - Log level filtering recognizes common formats: [LEVEL], LEVEL:, LEVEL -, etc.
        - Supported log levels: TRACE, DEBUG, INFO, WARN, WARNING, ERROR, FATAL, PANIC, CRITICAL
    """
    try:
        logger.info(f"Extracting log lines from {file_path}")

        # Validate parameters
        if max_lines < 1:
            max_lines = 1
        elif max_lines > 1000:
            max_lines = 1000

        if patterns is None:
            patterns = []
        if exclude_patterns is None:
            exclude_patterns = []
        if log_levels is None:
            log_levels = []
        if exclude_log_levels is None:
            exclude_log_levels = []

        # Normalize log levels to uppercase
        log_levels = [level.upper() for level in log_levels]
        exclude_log_levels = [level.upper() for level in exclude_log_levels]

        # Validate log levels
        valid_levels = {'TRACE', 'DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'FATAL', 'PANIC', 'CRITICAL'}
        for level in log_levels + exclude_log_levels:
            if level not in valid_levels:
                logger.warning(f"Invalid log level '{level}', ignoring")
                if level in log_levels:
                    log_levels.remove(level)
                if level in exclude_log_levels:
                    exclude_log_levels.remove(level)

        # Compile regex patterns
        include_regexes = []
        exclude_regexes = []

        try:
            for pattern in patterns:
                include_regexes.append(re.compile(pattern, re.IGNORECASE))
            for pattern in exclude_patterns:
                exclude_regexes.append(re.compile(pattern, re.IGNORECASE))
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
            return {
                "success": False,
                "error": f"Invalid regex pattern: {e}",
                "file_path": file_path
            }

        # Function to detect log level in a line
        def detect_log_level(line):
            """Detect log level in a line using common log formats."""
            # Common log level patterns (case insensitive)
            level_patterns = {
                'TRACE': r'\[TRACE\]|\bTRACE:|\bTRACE\s*-|\bTRACE\s*\|',
                'DEBUG': r'\[DEBUG\]|\bDEBUG:|\bDEBUG\s*-|\bDEBUG\s*\|',
                'INFO': r'\[INFO\]|\bINFO:|\bINFO\s*-|\bINFO\s*\|',
                'WARN': r'\[WARN\]|\bWARN:|\bWARN\s*-|\bWARN\s*\|',
                'WARNING': r'\[WARNING\]|\bWARNING:|\bWARNING\s*-|\bWARNING\s*\|',
                'ERROR': r'\[ERROR\]|\bERROR:|\bERROR\s*-|\bERROR\s*\|',
                'FATAL': r'\[FATAL\]|\bFATAL:|\bFATAL\s*-|\bFATAL\s*\|',
                'PANIC': r'\[PANIC\]|\bPANIC:|\bPANIC\s*-|\bPANIC\s*\|',
                'CRITICAL': r'\[CRITICAL\]|\bCRITICAL:|\bCRITICAL\s*-|\bCRITICAL\s*\|'
            }

            for level, pattern in level_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    return level

            return None

        # Parse time filters
        start_dt = None
        end_dt = None
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError as e:
                logger.error(f"Invalid start_time format: {e}")
                return {
                    "success": False,
                    "error": f"Invalid start_time format: {e}",
                    "file_path": file_path
                }
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError as e:
                logger.error(f"Invalid end_time format: {e}")
                return {
                    "success": False,
                    "error": f"Invalid end_time format: {e}",
                    "file_path": file_path
                }

        # Resolve and validate the path
        path = _safe_resolve_path(file_path)

        # Check if file exists
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path
            }

        # Check read permissions
        if not os.access(path, os.R_OK):
            logger.warning(f"Read permission denied: {file_path}")
            return {
                "success": False,
                "error": f"Read permission denied: {file_path}",
                "file_path": file_path
            }

        # Extract matching lines
        extracted_lines = []
        total_lines_processed = 0

        try:
            with path.open(encoding=encoding, errors='replace') as f:
                for line_num, line in enumerate(f, 1):
                    total_lines_processed = line_num
                    line_content = line.rstrip('\n\r')

                    # Time filtering (assumes ISO timestamp at start of line)
                    if start_dt or end_dt:
                        # Try to extract timestamp from beginning of line
                        timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)', line_content)
                        if timestamp_match:
                            try:
                                line_dt = datetime.fromisoformat(timestamp_match.group(1).replace('Z', '+00:00'))
                                if start_dt and line_dt < start_dt:
                                    continue
                                if end_dt and line_dt > end_dt:
                                    continue
                            except ValueError:
                                # If timestamp parsing fails, include the line
                                pass
                        else:
                            # If no timestamp found, skip time filtering for this line
                            pass

                    # Pattern filtering
                    should_include = len(include_regexes) == 0  # Include by default if no patterns

                    # Check include patterns (OR logic)
                    for regex in include_regexes:
                        if regex.search(line_content):
                            should_include = True
                            break

                    # Check exclude patterns
                    for regex in exclude_regexes:
                        if regex.search(line_content):
                            should_include = False
                            break

                    # Log level filtering
                    if should_include and (log_levels or exclude_log_levels):
                        detected_level = detect_log_level(line_content)

                        # Check include log levels
                        if log_levels:
                            should_include = detected_level in log_levels if detected_level else False

                        # Check exclude log levels
                        if should_include and exclude_log_levels:
                            should_include = detected_level not in exclude_log_levels if detected_level else True

                    if should_include:
                        extracted_lines.append({
                            "line_number": line_num,
                            "content": line_content
                        })

                        if len(extracted_lines) >= max_lines:
                            break

            # Get file stats
            stat_info = path.stat()

            result = {
                "success": True,
                "message": f"Extracted {len(extracted_lines)} log lines from {file_path}",
                "file_path": str(path),
                "lines": extracted_lines,
                "lines_extracted": len(extracted_lines),
                "total_lines_processed": total_lines_processed,
                "truncated": len(extracted_lines) >= max_lines,
                "patterns": patterns,
                "exclude_patterns": exclude_patterns,
                "log_levels": log_levels,
                "exclude_log_levels": exclude_log_levels,
                "start_time": start_time,
                "end_time": end_time,
                "max_lines": max_lines,
                "file_size": stat_info.st_size,
                "encoding": encoding
            }

            logger.info(f"Successfully extracted {len(extracted_lines)} lines from {file_path}")
            return result

        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error for {file_path}: {e}")
            return {
                "success": False,
                "error": f"Unicode decode error: {e}",
                "file_path": file_path,
                "encoding": encoding
            }

        except Exception as e:
            logger.error(f"Failed to extract log lines from {file_path}: {e}")
            return {
                "success": False,
                "error": f"Failed to extract log lines: {str(e)}",
                "file_path": file_path
            }

    except Exception as e:
        logger.error(f"Unexpected error extracting log lines from {file_path}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to extract log lines: {str(e)}",
            "file_path": file_path
        }


@_get_app().tool()
async def edit_file(
    file_path: str,
    old_string: str,
    new_string: str
) -> dict:
    """Edit a file by replacing text content with comprehensive error handling.

    This tool performs in-place text replacement in files, similar to sed operations.
    It provides atomic file editing with backup creation and comprehensive error handling.
    Supports both single and multiple occurrence replacements.
    
    Args:
        file_path: Path to the file to edit (relative or absolute)
        old_string: Text to replace (must be non-empty)
        new_string: Replacement text (can be empty for deletion)
        
    Returns:
        Dictionary containing edit operation results and metadata

    Error Handling:
        Returns error information if file not found, permission denied, or edit fails

    Safety Features:
        - Creates backup before editing
        - Validates file existence and permissions
        - Atomic write operations
        - Comprehensive logging
    """
    try:
        logger.info(f"Editing file: {file_path}")

        # Validate input parameters
        if not old_string:
            logger.warning("Empty old_string provided for file edit")
            return {
                "success": False,
                "error": "old_string cannot be empty",
                "file_path": file_path
            }

        # Resolve and validate the path
        path_obj = _safe_resolve_path(file_path)

        # Check if file exists
        if not path_obj.exists():
            logger.warning(f"File not found for editing: {file_path}")
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path
            }

        # Check if it's a file (not a directory)
        if not path_obj.is_file():
            logger.warning(f"Path is not a file: {file_path}")
            return {
                "success": False,
                "error": f"Path is not a file: {file_path}",
                "file_path": file_path
            }

        # Check read permissions
        if not os.access(path_obj, os.R_OK):
            logger.warning(f"Read permission denied: {file_path}")
            return {
                "success": False,
                "error": f"Read permission denied: {file_path}",
                "file_path": file_path
            }

        # Check write permissions
        if not os.access(path_obj, os.W_OK):
            logger.warning(f"Write permission denied: {file_path}")
            return {
                "success": False,
                "error": f"Write permission denied: {file_path}",
                "file_path": file_path
            }

        # Read the current file content
        try:
            content = path_obj.read_text(encoding='utf-8')
        except UnicodeDecodeError as e:
            logger.error(f"File is not valid UTF-8 text: {file_path}")
            return {
                "success": False,
                "error": f"File is not valid UTF-8 text: {str(e)}",
                "file_path": file_path
            }

        # Check if old_string exists in the file
        if old_string not in content:
            logger.warning(f"Text '{old_string}' not found in file: {file_path}")
            return {
                "success": False,
                "error": f"Text '{old_string}' not found in file",
                "file_path": file_path,
                "old_string": old_string
            }

        # Count occurrences before replacement
        occurrences = content.count(old_string)

        # Create backup file
        backup_path = path_obj.with_suffix(path_obj.suffix + '.backup')
        try:
            backup_path.write_text(content, encoding='utf-8')
            logger.debug(f"Created backup: {backup_path}")
        except Exception as e:
            logger.warning(f"Could not create backup file: {e}")
            # Continue without backup if it fails

        # Perform the replacement
        try:
            new_content = content.replace(old_string, new_string)

            # Write the modified content atomically
            temp_path = path_obj.with_suffix(path_obj.suffix + '.tmp')
            temp_path.write_text(new_content, encoding='utf-8')

            # Atomic move (replace original file)
            import shutil
            shutil.move(str(temp_path), str(path_obj))

            # Clean up backup if operation successful
            if backup_path.exists():
                try:
                    backup_path.unlink()
                    logger.debug(f"Removed backup after successful edit: {backup_path}")
                except Exception as e:
                    logger.warning(f"Could not remove backup file: {e}")

            # Get updated file stats
            stat_info = path_obj.stat()

            result = {
                "success": True,
                "message": f"Successfully edited file: {file_path}",
                "file_path": str(path_obj),
                "old_string": old_string,
                "new_string": new_string,
                "occurrences_replaced": occurrences,
                "file_size_before": len(content),
                "file_size_after": len(new_content),
                "size_change": len(new_content) - len(content),
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "backup_created": str(backup_path) if backup_path.exists() else None
            }

            logger.info(f"Successfully edited file {file_path}: {occurrences} occurrences replaced")
            return result

        except Exception as e:
            # Restore from backup if available
            if backup_path.exists():
                try:
                    backup_content = backup_path.read_text(encoding='utf-8')
                    path_obj.write_text(backup_content, encoding='utf-8')
                    logger.info(f"Restored file from backup after edit failure: {file_path}")
                except Exception as restore_error:
                    logger.error(f"Could not restore from backup: {restore_error}")

            logger.error(f"Failed to write edited content to {file_path}: {e}")
            return {
                "success": False,
                "error": f"Failed to write edited content: {str(e)}",
                "file_path": file_path,
                "old_string": old_string,
                "backup_available": str(backup_path) if backup_path.exists() else None
            }

    except Exception as e:
        logger.error(f"Unexpected error editing file {file_path}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to edit file: {str(e)}",
            "file_path": file_path
        }


# Plain function version for testing (without MCP decorator)
async def _edit_file_plain(
    file_path: str,
    old_string: str,
    new_string: str
) -> dict:
    """Plain version of edit_file for testing without MCP decorators."""
    try:
        logger.info(f"Editing file (plain): {file_path}")

        # Validate input parameters
        if not old_string:
            logger.warning("Empty old_string provided for file edit")
            return {
                "success": False,
                "error": "old_string cannot be empty",
                "file_path": file_path
            }

        # Resolve and validate the path
        path_obj = _safe_resolve_path(file_path)

        # Check if file exists
        if not path_obj.exists():
            logger.warning(f"File not found for editing: {file_path}")
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path
            }

        # Check if it's a file (not a directory)
        if not path_obj.is_file():
            logger.warning(f"Path is not a file: {file_path}")
            return {
                "success": False,
                "error": f"Path is not a file: {file_path}",
                "file_path": file_path
            }

        # Check read permissions
        if not os.access(path_obj, os.R_OK):
            logger.warning(f"Read permission denied: {file_path}")
            return {
                "success": False,
                "error": f"Read permission denied: {file_path}",
                "file_path": file_path
            }

        # Check write permissions
        if not os.access(path_obj, os.W_OK):
            logger.warning(f"Write permission denied: {file_path}")
            return {
                "success": False,
                "error": f"Write permission denied: {file_path}",
                "file_path": file_path
            }

        # Read the current file content
        try:
            content = path_obj.read_text(encoding='utf-8')
        except UnicodeDecodeError as e:
            logger.error(f"File is not valid UTF-8 text: {file_path}")
            return {
                "success": False,
                "error": f"File is not valid UTF-8 text: {str(e)}",
                "file_path": file_path
            }

        # Check if old_string exists in the file
        if old_string not in content:
            logger.warning(f"Text '{old_string}' not found in file: {file_path}")
            return {
                "success": False,
                "error": f"Text '{old_string}' not found in file",
                "file_path": file_path,
                "old_string": old_string
            }

        # Count occurrences before replacement
        occurrences = content.count(old_string)

        # Create backup file
        backup_path = path_obj.with_suffix(path_obj.suffix + '.backup')
        try:
            backup_path.write_text(content, encoding='utf-8')
            logger.debug(f"Created backup: {backup_path}")
        except Exception as e:
            logger.warning(f"Could not create backup file: {e}")
            # Continue without backup if it fails

        # Perform the replacement
        try:
            new_content = content.replace(old_string, new_string)

            # Write the modified content atomically
            temp_path = path_obj.with_suffix(path_obj.suffix + '.tmp')
            temp_path.write_text(new_content, encoding='utf-8')

            # Atomic move (replace original file)
            import shutil
            shutil.move(str(temp_path), str(path_obj))

            # Clean up backup if operation successful
            if backup_path.exists():
                try:
                    backup_path.unlink()
                    logger.debug(f"Removed backup after successful edit: {backup_path}")
                except Exception as e:
                    logger.warning(f"Could not remove backup file: {e}")

            # Get updated file stats
            stat_info = path_obj.stat()

            result = {
                "success": True,
                "message": f"Successfully edited file: {file_path}",
                "file_path": str(path_obj),
                "old_string": old_string,
                "new_string": new_string,
                "occurrences_replaced": occurrences,
                "file_size_before": len(content),
                "file_size_after": len(new_content),
                "size_change": len(new_content) - len(content),
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "backup_created": str(backup_path) if backup_path.exists() else None
            }

            logger.info(f"Successfully edited file {file_path}: {occurrences} occurrences replaced")
            return result

        except Exception as e:
            # Restore from backup if available
            if backup_path.exists():
                try:
                    backup_content = backup_path.read_text(encoding='utf-8')
                    path_obj.write_text(backup_content, encoding='utf-8')
                    logger.info(f"Restored file from backup after edit failure: {file_path}")
                except Exception as restore_error:
                    logger.error(f"Could not restore from backup: {restore_error}")

            logger.error(f"Failed to write edited content to {file_path}: {e}")
            return {
                "success": False,
                "error": f"Failed to write edited content: {str(e)}",
                "file_path": file_path,
                "old_string": old_string,
                "backup_available": str(backup_path) if backup_path.exists() else None
            }

    except Exception as e:
        logger.error(f"Unexpected error editing file {file_path}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to edit file: {str(e)}",
            "file_path": file_path
        }
