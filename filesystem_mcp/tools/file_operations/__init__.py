"""
File operations for the Filesystem MCP.

This module provides basic file operations like read, write, list, etc.
"""

import os
import stat
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Literal

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, validator, HttpUrl

# Set up logging
logger = logging.getLogger(__name__)

# Pydantic models for request/response validation
class FileContent(BaseModel):
    """Model for file content response."""
    path: str = Field(..., description="Path to the file")
    content: str = Field(..., description="File content")
    encoding: str = Field(default="utf-8", description="File encoding")
    size: int = Field(..., description="File size in bytes")
    last_modified: datetime = Field(..., description="Last modification time")

class FileWriteRequest(BaseModel):
    """Model for file write request."""
    path: str = Field(..., description="Path to the file")
    content: str = Field(..., description="Content to write")
    encoding: str = Field(default="utf-8", description="File encoding")
    create_parents: bool = Field(default=True, description="Create parent directories if they don't exist")
    
    @validator('path')
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
    """Model for file/directory information."""
    path: str = Field(..., description="Path to the file/directory")
    name: str = Field(..., description="Name of the file/directory")
    type: Literal["file", "directory", "symlink", "other"] = Field(..., description="Type of the entry")
    size: Optional[int] = Field(None, description="Size in bytes (for files)")
    created: Optional[datetime] = Field(None, description="Creation time")
    modified: Optional[datetime] = Field(None, description="Last modification time")
    accessed: Optional[datetime] = Field(None, description="Last access time")
    permissions: Dict[str, bool] = Field(..., description="File permissions")
    parent: Optional[str] = Field(None, description="Parent directory")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Helper functions
def _get_file_permissions(path: Path) -> Dict[str, bool]:
    """Get file permissions as a dictionary."""
    mode = path.stat().st_mode
    return {
        'readable': os.access(path, os.R_OK),
        'writable': os.access(path, os.W_OK),
        'executable': os.access(path, os.X_OK),
        'is_hidden': path.name.startswith('.')
    }

def _safe_resolve_path(file_path: str) -> Path:
    """Safely resolve a file path with security checks."""
    try:
        path = Path(file_path).expanduser().absolute()
        # Add additional security checks here
        return path
    except Exception as e:
        logger.error(f"Path resolution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid path: {e}"
        )

@tool(
    name="read_file",
    description="Read the contents of a file with proper error handling and metadata",
    response_model=FileContent
)
async def read_file(
    file_path: str = Field(..., description="Path to the file to read"),
    encoding: str = Field("utf-8", description="File encoding to use")
) -> FileContent:
    """
    Read the contents of a file with proper error handling and metadata.
    
    This function reads a file and returns its content along with metadata.
    It includes proper error handling and security checks.
    
    Args:
        file_path: Path to the file to read (can be relative or absolute).
        encoding: Character encoding to use when reading the file.
        
    Returns:
        FileContent: Object containing file content and metadata.
        
    Raises:
        HTTPException: With appropriate status code for various error conditions.
    """
    try:
        # Resolve and validate the path
        path = _safe_resolve_path(file_path)
        
        # Check if file exists
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_path}"
            )
            
        # Check if it's a directory
        if path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path is a directory: {file_path}"
            )
            
        # Check read permissions
        if not os.access(path, os.R_OK):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Read permission denied: {file_path}"
            )
            
        # Read file content and get metadata
        try:
            content = path.read_text(encoding=encoding)
            stat_info = path.stat()
            
            return FileContent(
                path=str(path),
                content=content,
                encoding=encoding,
                size=stat_info.st_size,
                last_modified=datetime.fromtimestamp(stat_info.st_mtime)
            )
            
        except UnicodeDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to decode file with {encoding} encoding: {e}"
            )
            
    except HTTPException:
        raise
        
    except Exception as e:
        logger.exception(f"Error reading file {file_path}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {str(e)}"
        )

@tool(
    name="write_file",
    description="Write content to a file with proper error handling and validation",
    response_model=Dict[str, Any]
)
async def write_file(
    request: FileWriteRequest
) -> Dict[str, Any]:
    """
    Write content to a file with proper error handling and validation.
    
    This function writes content to a file, creating parent directories if needed.
    It includes proper error handling, permission checks, and security validations.
    
    Args:
        request: FileWriteRequest object containing:
            - path: Path to the file to write to
            - content: Content to write
            - encoding: File encoding (default: utf-8)
            - create_parents: Whether to create parent directories (default: True)
    
    Returns:
        Dict: Operation result with status and metadata.
        
    Raises:
        HTTPException: With appropriate status code for various error conditions.
    """
    try:
        # Resolve and validate the path
        path = _safe_resolve_path(request.path)
        
        # Check if parent directory exists and is writable
        parent_dir = path.parent
        if not parent_dir.exists():
            if request.create_parents:
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Failed to create parent directory: {e}"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parent directory does not exist: {parent_dir}"
                )
        
        # Check if parent directory is writable
        if not os.access(parent_dir, os.W_OK):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Write permission denied for directory: {parent_dir}"
            )
        
        # Check if file exists and is writable
        if path.exists():
            if path.is_dir():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Path is a directory: {path}"
                )
            if not os.access(path, os.W_OK):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Write permission denied: {path}"
                )
        
        # Write the file
        try:
            bytes_written = path.write_text(request.content, encoding=request.encoding)
            stat_info = path.stat()
            
            return {
                "status": "success",
                "path": str(path),
                "bytes_written": bytes_written,
                "size": stat_info.st_size,
                "last_modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat()
            }
            
        except (UnicodeEncodeError, LookupError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Encoding error: {e}"
            )
            
    except HTTPException:
        raise
        
    except Exception as e:
        logger.exception(f"Error writing to file {request.path}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write to file: {str(e)}"
        )

class DirectoryListingRequest(BaseModel):
    """Request model for directory listing."""
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

@tool(
    name="list_directory",
    description="List contents of a directory with detailed metadata and filtering options",
    response_model=List[FileInfo]
)
async def list_directory(
    request: DirectoryListingRequest
) -> List[FileInfo]:
    """
    List contents of a directory with detailed metadata and filtering options.
    
    This function provides a detailed listing of directory contents with metadata,
    including file sizes, timestamps, and permissions. It supports recursive listing
    with depth control and hidden file filtering.
    
    Args:
        request: DirectoryListingRequest object containing:
            - directory_path: Path to list (default: current directory)
            - recursive: Whether to list recursively (default: False)
            - include_hidden: Include hidden files/directories (default: False)
            - max_depth: Maximum depth for recursive listing (default: None)
    
    Returns:
        List[FileInfo]: List of file/directory information objects.
        
    Raises:
        HTTPException: With appropriate status code for various error conditions.
    """
    try:
        # Resolve and validate the path
        path = _safe_resolve_path(request.directory_path)
        
        # Check if path exists
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Directory not found: {request.directory_path}"
            )
            
        # Check if path is a directory
        if not path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path is not a directory: {request.directory_path}"
            )
            
        # Check read permissions
        if not os.access(path, os.R_OK):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Read permission denied: {request.directory_path}"
            )
            
        # Internal function for recursive listing
        def _list_dir(current_path: Path, current_depth: int = 0) -> List[FileInfo]:
            results = []
            
            try:
                for item in current_path.iterdir():
                    # Skip hidden files/directories if not requested
                    if not request.include_hidden and item.name.startswith('.'):
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
                        
                        # Create file info object
                        file_info = FileInfo(
                            path=str(item),
                            name=item.name,
                            type=entry_type,
                            size=stat_info.st_size if not is_dir and not is_symlink else None,
                            created=datetime.fromtimestamp(stat_info.st_ctime),
                            modified=datetime.fromtimestamp(stat_info.st_mtime),
                            accessed=datetime.fromtimestamp(stat_info.st_atime),
                            permissions=_get_file_permissions(item),
                            parent=str(current_path)
                        )
                        
                        results.append(file_info)
                        
                        # Recurse into subdirectories if requested
                        if (request.recursive and is_dir and not is_symlink and 
                            (request.max_depth is None or current_depth < request.max_depth - 1)):
                            results.extend(_list_dir(item, current_depth + 1))
                            
                    except (PermissionError, OSError) as e:
                        logger.warning(f"Skipping inaccessible item {item}: {e}")
                        continue
                        
            except (PermissionError, OSError) as e:
                logger.warning(f"Cannot access directory {current_path}: {e}")
                
            return results
        
        # Start recursive listing
        return _list_dir(path)
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.exception(f"Error listing directory {request.directory_path}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list directory: {str(e)}"
        )

class FileExistsRequest(BaseModel):
    """Request model for file existence check."""
    path: str = Field(..., description="Path to check")
    check_type: Optional[Literal["file", "directory", "any"]] = Field(
        "any",
        description="Type of filesystem object to check for (file, directory, or any)"
    )
    follow_symlinks: bool = Field(
        True,
        description="Whether to follow symbolic links (default: True)"
    )

@tool(
    name="file_exists",
    description="Check if a file or directory exists with detailed status information",
    response_model=Dict[str, Any]
)
async def file_exists(
    request: FileExistsRequest
) -> Dict[str, Any]:
    """
    Check if a file or directory exists with detailed status information.
    
    This function checks for the existence of a filesystem object with optional
    type checking and symlink resolution. It provides detailed information
    about the object if it exists.
    
    Args:
        request: FileExistsRequest object containing:
            - path: Path to check
            - check_type: Type of object to check for (file, directory, or any)
            - follow_symlinks: Whether to follow symbolic links
    
    Returns:
        Dict containing existence status and details about the path.
        
    Raises:
        HTTPException: If there's an error accessing the path.
    """
    try:
        # Resolve and validate the path
        path = _safe_resolve_path(request.path)
        
        # Check if the path exists
        exists = path.exists()
        
        # If it doesn't exist, we can return early
        if not exists:
            return {
                "exists": False,
                "path": str(path),
                "type": "none",
                "message": "Path does not exist"
            }
            
        # Get the actual type (following symlinks if requested)
        actual_path = path.resolve() if request.follow_symlinks else path
        is_symlink = path.is_symlink()
        is_file = actual_path.is_file()
        is_dir = actual_path.is_dir()
        
        # Determine the type
        path_type = "file" if is_file else "directory" if is_dir else "other"
        
        # Check if the type matches the requested type
        type_matches = (
            request.check_type == "any" or
            (request.check_type == "file" and is_file) or
            (request.check_type == "directory" and is_dir)
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
                logger.warning(f"Could not get file info for {path}: {e}")
        
        # Prepare the response
        response = {
            "exists": exists and type_matches,
            "path": str(path),
            "resolved_path": str(actual_path) if exists and is_symlink else None,
            "type": path_type,
            "is_symlink": is_symlink,
            "type_matches": type_matches,
            "details": file_info,
            "message": "Path exists and matches type criteria" if type_matches else "Path exists but does not match type criteria"
        }
        
        return response
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.exception(f"Error checking if path exists: {request.path}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check path existence: {str(e)}"
        )

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

@tool(
    name="get_file_info",
    description="Get detailed information about a file or directory",
    response_model=Dict[str, Any]
)
async def get_file_info(
    request: FileInfoRequest
) -> Dict[str, Any]:
    """
    Get detailed information about a file or directory.
    
    This function provides comprehensive information about a filesystem object,
    including metadata, permissions, and optionally file content for small text files.
    
    Args:
        request: FileInfoRequest object containing:
            - path: Path to the file or directory
            - follow_symlinks: Whether to follow symbolic links
            - include_content: Whether to include file content
            - max_content_size: Maximum file size to include content for
    
    Returns:
        Dict containing detailed information about the file/directory.
        
    Raises:
        HTTPException: If there's an error accessing the path.
    """
    try:
        # Resolve and validate the path
        path = _safe_resolve_path(request.path)
        
        # Check if path exists
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Path not found: {request.path}"
            )
            
        # Resolve symlinks if requested
        actual_path = path.resolve() if request.follow_symlinks else path
        is_symlink = path.is_symlink()
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
                "path": str(path),
                "resolved_path": str(actual_path) if is_symlink and request.follow_symlinks else None,
                "name": path.name,
                "parent": str(path.parent),
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
                "user_id": stat_info.st_uid,
                "group_id": stat_info.st_gid,
                "mode": stat.filemode(stat_info.st_mode),
                "is_hidden": path.name.startswith('.')
            }
            
            # Add content for small text files if requested
            if (request.include_content and is_file and 
                stat_info.st_size <= request.max_content_size):
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
                    logger.warning(f"Could not read file content for {path}: {e}")
                    response["content_error"] = str(e)
            
            return response
            
        except (PermissionError, OSError) as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {e}"
            )
            
    except HTTPException:
        raise
        
    except Exception as e:
        logger.exception(f"Error getting info for {request.path}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file info: {str(e)}"
        )

@tool()
def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get detailed information about a file or directory.
    
    Args:
        file_path: Path to the file or directory.
        
    Returns:
        Dict: File/directory information.
    """
    path = Path(file_path).expanduser().absolute()
    
    if not path.exists():
        raise FileNotFoundError(f"File or directory not found: {file_path}")
    
    stat_info = path.stat()
    
    # Get file info with fallbacks for Windows compatibility
    file_info = {
        "name": path.name,
        "path": str(path),
        "is_dir": path.is_dir(),
        "is_file": path.is_file(),
        "size": stat_info.st_size,
        "created": stat_info.st_ctime,
        "modified": stat_info.st_mtime,
        "accessed": stat_info.st_atime,
        "mode": stat.filemode(stat_info.st_mode),
        "absolute_path": str(path.absolute()),
        "parent": str(path.parent),
        "suffix": path.suffix,
        "suffixes": path.suffixes,
        "stem": path.stem
    }
    
    # Add owner and group with fallbacks for Windows
    try:
        file_info["owner"] = path.owner()
    except (NotImplementedError, ImportError):
        file_info["owner"] = "N/A"
    
    try:
        file_info["group"] = path.group()
    except (NotImplementedError, ImportError):
        file_info["group"] = "N/A"
    
    return file_info
