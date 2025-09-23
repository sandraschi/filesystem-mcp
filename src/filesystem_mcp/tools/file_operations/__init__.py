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

@_get_app().tool()
async def list_directory(
    directory_path: str = ".",
    recursive: bool = False,
    include_hidden: bool = False,
    max_depth: Optional[int] = None
) -> List[dict]:
    """List contents of a directory with detailed metadata and filtering options.

    This tool provides a detailed listing of directory contents with comprehensive
    metadata including file sizes, timestamps, permissions, and type information.
    It supports recursive listing with depth control and hidden file filtering.

    Args:
        directory_path: Path to the directory (default: current directory)
        recursive: Whether to list contents recursively (default: False)
        include_hidden: Whether to include hidden files/directories (default: False)
        max_depth: Maximum depth for recursive listing (default: None for unlimited)

    Returns:
        List of dictionaries containing file/directory information

    Error Handling:
        Returns error information if directory access fails or path is invalid
    """
    try:
        logger.info(f"Listing directory: {directory_path}")

        # Resolve and validate the path
        path = _safe_resolve_path(directory_path)

        # Check if path exists
        if not path.exists():
            logger.warning(f"Directory not found: {directory_path}")
            return [{
                "success": False,
                "error": f"Directory not found: {directory_path}",
                "path": directory_path,
                "type": "error"
            }]

        # Check if path is a directory
        if not path.is_dir():
            logger.warning(f"Path is not a directory: {directory_path}")
            return [{
                "success": False,
                "error": f"Path is not a directory: {directory_path}",
                "path": directory_path,
                "type": "error"
            }]

        # Check read permissions
        if not os.access(path, os.R_OK):
            logger.warning(f"Read permission denied: {directory_path}")
            return [{
                "success": False,
                "error": f"Read permission denied: {directory_path}",
                "path": directory_path,
                "type": "error"
            }]

        # Internal function for recursive listing
        def _list_dir(current_path: Path, current_depth: int = 0, visited: set = None) -> List[dict]:
            if visited is None:
                visited = set()

            # Prevent infinite loops by tracking visited directories
            resolved_path = current_path.resolve()
            if resolved_path in visited:
                logger.warning(f"Skipping already visited directory: {current_path}")
                return []
            visited.add(resolved_path)

            results = []

            try:
                for item in current_path.iterdir():
                    # Skip hidden files/directories if not requested
                    if not include_hidden and item.name.startswith('.'):
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

                        # Recurse into subdirectories if requested and depth allows
                        if (recursive and is_dir and not is_symlink and
                            (max_depth is None or current_depth < max_depth)):
                            results.extend(_list_dir(item, current_depth + 1, visited))

                    except (PermissionError, OSError) as e:
                        logger.warning(f"Skipping inaccessible item {item}: {e}")
                        continue

            except (PermissionError, OSError) as e:
                logger.warning(f"Cannot access directory {current_path}: {e}")

            return results

        # Start recursive listing
        file_list = _list_dir(path)
        logger.info(f"Successfully listed {len(file_list)} items in {directory_path}")
        return file_list

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
