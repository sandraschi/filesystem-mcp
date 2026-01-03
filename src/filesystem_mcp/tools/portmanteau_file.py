import logging
import time
from typing import Any, Literal, Optional

from .utils import (
    _clarification_response,
    _error_response,
    _format_file_size,
    _get_app,
    _safe_resolve_path,
    _success_response,
)

logger = logging.getLogger(__name__)


@_get_app().tool()
async def file_ops(
    operation: Literal[
        "read_file",
        "write_file",
        "edit_file",
        "move_file",
        "read_file_lines",
        "read_multiple_files",
        "file_exists",
        "get_file_info",
        "head_file",
        "tail_file",
    ],
    path: Optional[str] = None,
    content: Optional[str] = None,
    encoding: str = "utf-8",
    old_string: Optional[str] = None,
    new_string: Optional[str] = None,
    file_paths: Optional[list[str]] = None,
    destination_path: Optional[str] = None,
    overwrite: bool = False,
    offset: int = 0,
    limit: Optional[int] = None,
    lines: int = 10,
    check_type: Literal["file", "any"] = "file",
    follow_symlinks: bool = True,
    include_content: bool = False,
    max_content_size: int = 1048576,
    create_parents: bool = True,
    no_backup: bool = False,
    max_file_size_mb: float = 10.0,
) -> dict[str, Any]:
    """Basic File IO and Metadata operations.

    Args:
        operation (Literal, required): Available file operations:
            - "read_file": Read file contents with enhanced metadata (requires: path)
            - "write_file": Write content to files with validation (requires: path, content)
            - "edit_file": Edit files by replacing text content (requires: path, old_string, new_string)
            - "move_file": Move/rename files (requires: path, destination_path)
            - "read_file_lines": Read specific line ranges (requires: path, optional: offset, limit)
            - "read_multiple_files": Read multiple files efficiently (requires: file_paths)
            - "file_exists": Check if file exists (requires: path)
            - "get_file_info": Get comprehensive metadata (requires: path)
            - "head_file": Read first N lines (requires: path, lines)
            - "tail_file": Read last N lines (requires: path, lines)

        --- PRIMARY PARAMETERS ---

        path (str | None): Target file path for operations
        content (str | None): Content for write operations
        encoding (str): Text encoding. Default: "utf-8"

        --- FILE EDITING ---

        old_string (str | None): Text to replace in edit operations
        new_string (str | None): Replacement text

        --- MULTI-FILE & MOVEMENT ---

        file_paths (List[str] | None): List of paths for multi-file reading
        destination_path (str | None): Destination for move operations
        overwrite (bool): Overwrite existing destination. Default: False

        --- PAGINATION & LIMITS ---

        offset (int): Line offset for reading. Default: 0
        limit (int | None): Maximum lines to return
        lines (int): Number of lines for head/tail. Default: 10

        --- METADATA & CONTENT ---

        check_type (Literal): Type check for existence. Default: "file"
        follow_symlinks (bool): Follow symbolic links. Default: True
        include_content (bool): Include file content in info. Default: False
        max_content_size (int): Max size for content inclusion. Default: 1MB
        create_parents (bool): Create missing parent directories. Default: True
        no_backup (bool): Skip backup creation for write_file. Default: False (backup created by default)
        max_file_size_mb (float): Max file size in MB for read_multiple_files. Default: 10.0
    """
    try:
        if not operation:
            return _clarification_response(
                "operation", "No operation specified", ["read_file", "write_file", "list_directory"]
            )

        # Check required params for common operations
        if (
            operation
            in [
                "read_file",
                "write_file",
                "edit_file",
                "move_file",
                "read_file_lines",
                "file_exists",
                "get_file_info",
                "head_file",
                "tail_file",
            ]
            and not path
        ):
            return _clarification_response("path", f"Path is required for {operation}")

        if operation == "read_file":
            return await _read_file(path, encoding)
        elif operation == "write_file":
            if content is None:
                return _clarification_response("content", "Content is required for write_file")
            return await _write_file(path, content, encoding, create_parents, no_backup)
        elif operation == "edit_file":
            if not old_string or not new_string:
                return _clarification_response(
                    "old_string/new_string",
                    "Both old_string and new_string are required for edit_file",
                )
            return await _edit_file(path, old_string, new_string)
        elif operation == "move_file":
            if not destination_path:
                return _clarification_response(
                    "destination_path", "destination_path is required for move_file"
                )
            return await _move_file(path, destination_path, overwrite)
        elif operation == "read_file_lines":
            return await _read_file_lines(path, offset, limit, encoding)
        elif operation == "read_multiple_files":
            if not file_paths:
                return _clarification_response(
                    "file_paths", "file_paths list is required for read_multiple_files"
                )
            return await _read_multiple_files(file_paths, encoding, max_file_size_mb)
        elif operation == "file_exists":
            return await _file_exists(path, check_type, follow_symlinks)
        elif operation == "get_file_info":
            return await _get_file_info(path, follow_symlinks, include_content, max_content_size)
        elif operation == "head_file":
            return await _head_file(path, lines, encoding)
        elif operation == "tail_file":
            return await _tail_file(path, lines, encoding)
        else:
            return _error_response(f"Unknown operation: {operation}", "unsupported_operation")
    except Exception as e:
        logger.error(f"File operation '{operation}' failed: {e}", exc_info=True)
        return _error_response(str(e), "internal_error")


async def _read_file(file_path: str, encoding: str) -> dict[str, Any]:
    """Read file contents with enhanced metadata and suggestions."""
    start_time = time.time()
    try:
        path_obj = _safe_resolve_path(file_path)
        if not path_obj.exists():
            return _error_response(
                f"File does not exist: {file_path}",
                "file_not_found",
                ["Check if the file path is correct", "Verify file permissions"],
            )
        if not path_obj.is_file():
            return _error_response(
                f"Path is not a file: {file_path}",
                "not_a_file",
                ["Use list_directory for directories", "Check the path and try again"],
            )

        content = path_obj.read_text(encoding=encoding)
        execution_time = time.time() - start_time

        # Analyze content for suggestions
        lines = content.splitlines()
        file_size_mb = len(content) / (1024 * 1024)

        recommendations = []
        if len(lines) > 1000:
            recommendations.append(
                "File is quite large - consider using read_file_lines with offset/limit"
            )
        if file_size_mb > 10:
            recommendations.append("Large file detected - consider processing in chunks")

        # Detect file type for additional suggestions
        file_ext = path_obj.suffix.lower()
        if file_ext in [".json", ".yaml", ".yml", ".xml"]:
            recommendations.append(
                "Structured file detected - consider using appropriate parsing tools"
            )
        elif file_ext in [".md", ".txt"]:
            recommendations.append("Text file - consider grep_file for searching content")
        elif file_ext in [".log"]:
            recommendations.append("Log file detected - consider extract_log_lines for analysis")

        return _success_response(
            {
                "content": content,
                "size": len(content),
                "size_human": _format_file_size(len(content)),
                "lines": len(lines),
                "encoding": encoding,
                "path": str(path_obj),
                "execution_time": round(execution_time, 3),
                "file_type": file_ext or "no_extension",
                "recommendations": recommendations,
            },
            next_steps=[
                f"grep_file(path='{file_path}', search_pattern='search_term')"
                if file_ext in [".md", ".txt", ".log"]
                else None,
                f"read_file_lines(path='{file_path}', limit=50)" if len(lines) > 100 else None,
                f"get_file_info(path='{file_path}')",
            ],
            related_ops=[
                "grep_file" if file_ext in [".md", ".txt", ".log"] else None,
                "read_file_lines" if len(lines) > 50 else None,
                "get_file_info",
            ],
        )

    except UnicodeDecodeError as e:
        return _error_response(
            f"Cannot decode as {encoding}: {str(e)}",
            "encoding_error",
            ["Try a different encoding (utf-8, latin-1, cp1252)", "Check if file is binary"],
        )
    except Exception as e:
        return _error_response(
            f"Failed to read file: {str(e)}",
            "io_error",
            ["Check file permissions", "Verify the file is not locked by another process"],
        )


async def _write_file(
    file_path: str, content: str, encoding: str, create_parents: bool, no_backup: bool
) -> dict[str, Any]:
    """Write content to file with optional backup."""
    import shutil

    try:
        path_obj = _safe_resolve_path(file_path)
        
        # Create backup if file exists and backup not disabled
        backup_path = None
        if path_obj.exists() and path_obj.is_file() and not no_backup:
            backup_path = path_obj.with_suffix(path_obj.suffix + ".backup")
            shutil.copy2(path_obj, backup_path)
        
        if create_parents:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
        path_obj.write_text(content, encoding=encoding)
        
        result = {
            "path": str(path_obj),
            "size": len(content),
            "encoding": encoding,
        }
        if backup_path:
            result["backup_path"] = str(backup_path)
        
        return _success_response(
            result,
            next_steps=[f"read_file(path='{file_path}')"],
        )
    except Exception as e:
        return _error_response(f"Failed to write file: {str(e)}", "io_error")


async def _edit_file(file_path: str, old_string: str, new_string: str) -> dict[str, Any]:
    """Edit file by replacing text."""
    import shutil

    try:
        path_obj = _safe_resolve_path(file_path)
        if not path_obj.exists() or not path_obj.is_file():
            return _error_response(f"Invalid file path: {file_path}", "not_found")
        content = path_obj.read_text(encoding="utf-8")
        if old_string not in content:
            return _error_response("Text to replace not found in file", "content_not_found")

        new_content = content.replace(old_string, new_string, 1)

        # Create backup
        backup_path = path_obj.with_suffix(path_obj.suffix + ".backup")
        shutil.copy2(path_obj, backup_path)

        path_obj.write_text(new_content, encoding="utf-8")
        return _success_response(
            {
                "path": str(path_obj),
                "backup_path": str(backup_path),
                "old_length": len(content),
                "new_length": len(new_content),
            },
            next_steps=[f"read_file(path='{file_path}')"],
        )
    except Exception as e:
        return _error_response(f"Failed to edit file: {str(e)}", "io_error")


async def _move_file(source_path: str, destination_path: str, overwrite: bool) -> dict[str, Any]:
    """Move file or directory."""
    import shutil

    try:
        source = _safe_resolve_path(source_path)
        dest = _safe_resolve_path(destination_path)
        if not source.exists():
            return _error_response(f"Source does not exist: {source_path}", "not_found")
        if dest.exists() and not overwrite:
            return _error_response(f"Destination exists: {destination_path}", "already_exists")
        shutil.move(str(source), str(dest))
        return _success_response(
            {
                "source": str(source),
                "destination": str(dest),
                "overwritten": dest.exists() if overwrite else False,
            }
        )
    except Exception as e:
        return _error_response(f"Failed to move: {str(e)}", "io_error")


async def _read_file_lines(
    file_path: str, offset: int, limit: Optional[int], encoding: str
) -> dict[str, Any]:
    """Read specific lines from file."""
    try:
        path_obj = _safe_resolve_path(file_path)
        if not path_obj.exists() or not path_obj.is_file():
            return _error_response(f"Invalid file path: {file_path}", "not_found")
        content = path_obj.read_text(encoding=encoding)
        lines = content.splitlines(keepends=True)

        if offset >= len(lines):
            selected_lines = []
            end = offset
        else:
            end = len(lines) if limit is None else min(offset + limit, len(lines))
            selected_lines = lines[offset:end]

        return _success_response(
            {
                "content": "".join(selected_lines),
                "offset": offset,
                "limit": limit,
                "lines_returned": len(selected_lines),
                "total_lines": len(lines),
            },
            next_steps=[f"read_file_lines(path='{file_path}', offset={end}, limit={limit})"]
            if end < len(lines)
            else [],
        )
    except Exception as e:
        return _error_response(f"Failed to read lines: {str(e)}", "io_error")


async def _read_multiple_files(
    file_paths: list[str], encoding: str, max_file_size_mb: float
) -> dict[str, Any]:
    """Read multiple files with size protection."""
    try:
        results = {}
        success_count = 0
        skipped_count = 0
        max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)
        
        for file_path in file_paths:
            try:
                path_obj = _safe_resolve_path(file_path)
                if path_obj.exists() and path_obj.is_file():
                    file_size = path_obj.stat().st_size
                    if file_size > max_file_size_bytes:
                        results[file_path] = {
                            "success": False,
                            "error": f"File too large: {_format_file_size(file_size)} (max: {max_file_size_mb}MB)",
                        }
                        skipped_count += 1
                    else:
                        results[file_path] = {
                            "success": True,
                            "content": path_obj.read_text(encoding=encoding),
                            "size": file_size,
                        }
                        success_count += 1
                else:
                    results[file_path] = {"success": False, "error": "File not found"}
            except Exception as e:
                results[file_path] = {"success": False, "error": str(e)}

        return _success_response(
            {
                "results": results,
                "total_files": len(file_paths),
                "successful_reads": success_count,
                "skipped_large_files": skipped_count,
                "max_file_size_mb": max_file_size_mb,
            },
            related_ops=["read_file", "get_file_info"],
        )
    except Exception as e:
        return _error_response(f"Failed to read multiple files: {str(e)}", "io_error")


async def _file_exists(file_path: str, check_type: str, follow_symlinks: bool) -> dict[str, Any]:
    """Check if file/directory exists."""
    try:
        path_obj = _safe_resolve_path(file_path)
        exists = path_obj.exists()
        if not exists:
            return _success_response({"exists": False, "path": str(path_obj)})

        is_file = path_obj.is_file()
        is_dir = path_obj.is_dir()
        type_matches = (
            (check_type == "any")
            or (check_type == "file" and is_file)
            or (check_type == "directory" and is_dir)
        )

        return _success_response(
            {
                "exists": True,
                "path": str(path_obj),
                "is_file": is_file,
                "is_dir": is_dir,
                "type_matches": type_matches,
                "check_type": check_type,
            },
            next_steps=[f"read_file(path='{file_path}')"] if is_file else [],
        )
    except Exception as e:
        return _error_response(f"Failed to check existence: {str(e)}", "io_error")


async def _get_file_info(
    file_path: str, follow_symlinks: bool, include_content: bool, max_content_size: int
) -> dict[str, Any]:
    """Get detailed file information."""
    try:
        path_obj = _safe_resolve_path(file_path)
        if not path_obj.exists():
            return _error_response(f"Path does not exist: {file_path}", "not_found")

        stat = path_obj.stat(follow_symlinks=follow_symlinks)
        info = {
            "path": str(path_obj),
            "name": path_obj.name,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "accessed": stat.st_atime,
            "permissions": oct(stat.st_mode)[-3:],
            "is_file": path_obj.is_file(),
            "is_dir": path_obj.is_dir(),
            "is_symlink": path_obj.is_symlink(),
            "human_size": _format_file_size(stat.st_size),
        }

        if include_content and path_obj.is_file() and stat.st_size <= max_content_size:
            try:
                info["content"] = path_obj.read_text(encoding="utf-8", errors="ignore")
                info["content_included"] = True
            except Exception:
                info["content_included"] = False
        else:
            info["content_included"] = False

        return _success_response(info, related_ops=["head_file", "read_file"])
    except Exception as e:
        return _error_response(f"Failed to get file info: {str(e)}", "io_error")


async def _head_file(file_path: str, lines: int, encoding: str) -> dict[str, Any]:
    """Read first N lines of file."""
    try:
        path_obj = _safe_resolve_path(file_path)
        if not path_obj.exists():
            return _error_response(f"File does not exist: {file_path}", "not_found")
        if not path_obj.is_file():
            return _error_response(f"Path is not a file: {file_path}", "not_a_file")

        content = path_obj.read_text(encoding=encoding)
        all_lines = content.splitlines(keepends=True)
        selected_lines = all_lines[:lines]

        return _success_response(
            {
                "content": "".join(selected_lines),
                "lines_requested": lines,
                "lines_returned": len(selected_lines),
                "total_lines": len(all_lines),
                "encoding": encoding,
                "path": str(path_obj),
            },
            next_steps=[f"read_file_lines(path='{file_path}', offset={lines})"]
            if len(all_lines) > lines
            else [],
        )
    except Exception as e:
        return _error_response(f"Failed to read head: {str(e)}", "io_error")


async def _tail_file(file_path: str, lines: int, encoding: str) -> dict[str, Any]:
    """Read last N lines of file."""
    try:
        path_obj = _safe_resolve_path(file_path)
        if not path_obj.exists():
            return _error_response(f"File does not exist: {file_path}", "not_found")
        if not path_obj.is_file():
            return _error_response(f"Path is not a file: {file_path}", "not_a_file")

        content = path_obj.read_text(encoding=encoding)
        all_lines = content.splitlines(keepends=True)
        selected_lines = all_lines[-lines:] if lines > 0 else []

        return _success_response(
            {
                "content": "".join(selected_lines),
                "lines_requested": lines,
                "lines_returned": len(selected_lines),
                "total_lines": len(all_lines),
                "encoding": encoding,
                "path": str(path_obj),
            }
        )
    except Exception as e:
        return _error_response(f"Failed to read tail: {str(e)}", "io_error")
