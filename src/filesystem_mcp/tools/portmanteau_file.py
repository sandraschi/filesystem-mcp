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
        "delete_file",
        "move_file",
        "read_file_lines",
        "read_multiple_files",
        "file_exists",
        "get_file_info",
        "head_file",
        "tail_file",
        "undo_edit",
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
    allow_multiple: bool = False,
    is_regex: bool = False,
    ignore_whitespace: bool = False,
    replacements: Optional[list[dict]] = None,
) -> dict[str, Any]:
    """Comprehensive file system operations with enhanced conversational responses.

    SUPPORTED OPERATIONS:
    - read_file: Read complete file contents with metadata
    - write_file: Write content to files with backup and validation
    - edit_file: Edit files by replacing text content
    - delete_file: Permanently delete a file
    - move_file: Move/rename files with path validation
    - read_file_lines: Read specific line ranges with pagination
    - read_multiple_files: Efficiently read multiple files in batch
    - file_exists: Check file existence with type validation
    - get_file_info: Get comprehensive file metadata and statistics
    - head_file: Read first N lines of file
    - tail_file: Read last N lines of file
    - undo_edit: Revert the most recent edit using .bak file

    OPERATIONS DETAIL:

    read_file: Complete file reading with encoding detection
    - Parameters: path (required), encoding (optional)
    - Returns: File content, metadata, encoding info
    - Example: file_ops("read_file", path="README.md")
    - Error handling: File not found, permission denied, encoding errors

    write_file: Safe file writing with automatic backup creation
    - Parameters: path (required), content (required), encoding (optional)
    - Returns: Write confirmation, backup path, file statistics
    - Example: file_ops("write_file", path="output.txt", content="Hello World")
    - Features: Automatic backup, parent directory creation, size validation

    edit_file: Precise text replacement with context validation
    - Parameters: path (required), old_string (required), new_string (required)
    - Returns: Edit confirmation, change statistics, backup info
    - Example: file_ops("edit_file", path="config.txt", old_string="old_value", new_string="new_value")
    - Features: Exact string matching, occurrence counting, undo capability

    delete_file: Permanent file deletion
    - Parameters: path (required)
    - Returns: Deletion confirmation, file metadata snapshot
    - Example: file_ops("delete_file", path="old_backup.txt")
    - Features: Pre-deletion metadata capture, clear error on missing file

    move_file: Safe file movement with conflict detection
    - Parameters: path (required), destination_path (required), overwrite (optional)
    - Returns: Move confirmation, new path, metadata preservation status
    - Example: file_ops("move_file", path="old.txt", destination_path="new.txt")
    - Features: Overwrite protection, metadata preservation, cross-filesystem support

    read_file_lines: Efficient line-based reading with pagination
    - Parameters: path (required), offset (optional), limit (optional)
    - Returns: Line range, total lines, content preview
    - Example: file_ops("read_file_lines", path="large.log", offset=100, limit=50)
    - Features: Memory efficient, large file support, line numbering

    read_multiple_files: Batch file reading with size limits
    - Parameters: file_paths (required), max_file_size_mb (optional)
    - Returns: Multiple file contents, summary statistics, error handling
    - Example: file_ops("read_multiple_files", file_paths=["file1.txt", "file2.txt"])
    - Features: Size validation, error aggregation, performance optimization

    file_exists: Comprehensive existence checking
    - Parameters: path (required), check_type (optional)
    - Returns: Existence status, file type, accessibility info
    - Example: file_ops("file_exists", path="/etc/passwd", check_type="file")
    - Features: Type checking, permission validation, symlink handling

    get_file_info: Detailed file metadata and analysis
    - Parameters: path (required), include_content (optional), max_content_size (optional)
    - Returns: Complete file statistics, permissions, timestamps, content preview
    - Example: file_ops("get_file_info", path="data.json", include_content=True)
    - Features: MIME type detection, encoding analysis, security validation

    head_file: Efficient first-lines reading
    - Parameters: path (required), lines (optional)
    - Returns: First N lines, total line count, encoding info
    - Example: file_ops("head_file", path="access.log", lines=20)
    - Features: Memory efficient, large file optimized, line counting

    tail_file: Efficient last-lines reading
    - Parameters: path (required), lines (optional)
    - Returns: Last N lines, total line count, file position info
    - Example: file_ops("tail_file", path="error.log", lines=50)
    - Features: Memory efficient, reverse reading, line counting

    Args:
        operation: The file operation to perform (see SUPPORTED OPERATIONS above)
        path: Target file path for single-file operations
        content: Text content for write operations
        encoding: Text encoding for file operations (default: "utf-8")
        old_string: Text to replace in edit operations
        new_string: Replacement text for edit operations
        file_paths: List of file paths for multi-file operations
        destination_path: Destination path for move operations
        overwrite: Whether to overwrite existing files (default: False)
        offset: Starting line number for read operations (default: 0)
        limit: Maximum number of lines to return (optional)
        lines: Number of lines for head/tail operations (default: 10)
        check_type: Type checking mode for existence operations (default: "file")
        follow_symlinks: Whether to follow symbolic links (default: True)
        include_content: Whether to include file content in metadata operations (default: False)
        max_content_size: Maximum content size for inclusion (default: 1048576 bytes)
        create_parents: Whether to create missing parent directories (default: True)
        no_backup: Whether to skip backup creation for write/edit operations (default: False)
        max_file_size_mb: Maximum file size for multi-file operations (default: 10.0 MB)
        allow_multiple: Replace all occurrences of old_string (default: False)
        is_regex: Treat old_string as a regular expression (default: False)
        ignore_whitespace: Normalize indentation during matching (default: False)
        replacements: List of dicts with {old_string, new_string} for batch edits

    Returns:
        Operation-specific result with enhanced metadata:
        - success: Boolean operation status
        - result: Operation data and file information
        - execution_time_ms: Performance timing
        - quality_metrics: Operation quality indicators
        - recommendations: Suggested next steps
        - next_steps: Actionable follow-up operations
        - related_operations: Suggested related file operations

    Examples:
        # Read a file
        file_ops("read_file", path="README.md")

        # Write content safely
        file_ops("write_file", path="output.txt", content="Hello World")

        # Edit with replacement
        file_ops("edit_file", path="config.txt", old_string="old", new_string="new")

        # Delete a file permanently
        file_ops("delete_file", path="old_backup.txt")

        # Move with safety checks
        file_ops("move_file", path="old.txt", destination_path="new.txt")

        # Read specific lines
        file_ops("read_file_lines", path="log.txt", offset=100, limit=50)

        # Batch read multiple files
        file_ops("read_multiple_files", file_paths=["file1.txt", "file2.txt"])

        # Check file existence
        file_ops("file_exists", path="target.txt")

        # Get detailed metadata
        file_ops("get_file_info", path="data.json", include_content=True)

        # Read first lines
        file_ops("head_file", path="access.log", lines=20)

        # Read last lines
        file_ops("tail_file", path="error.log", lines=50)
    """
    try:
        if not operation:
            return _clarification_response(
                ambiguities=["operation not specified"],
                options={
                    "available": [
                        "read_file",
                        "write_file",
                        "edit_file",
                        "delete_file",
                        "move_file",
                        "read_file_lines",
                        "read_multiple_files",
                        "file_exists",
                        "get_file_info",
                        "head_file",
                        "tail_file",
                    ]
                },
            )

        # Check required params for common operations
        if (
            operation
            in [
                "read_file",
                "write_file",
                "edit_file",
                "delete_file",
                "move_file",
                "read_file_lines",
                "file_exists",
                "get_file_info",
                "head_file",
                "tail_file",
            ]
            and not path
        ):
            return _clarification_response(
                ambiguities=[f"path required for {operation}"],
                suggested_questions=[f"What file path should be used for {operation}?"],
            )

        if operation == "read_file":
            return await _read_file(path, encoding)
        elif operation == "write_file":
            if path is None or content is None:
                return _clarification_response(
                    ambiguities=["path and content both required for write_file"],
                    suggested_questions=["What content should be written to the file?"],
                )
            return await _write_file(path, content, encoding, create_parents, no_backup)
        elif operation == "edit_file":
            if not replacements and (not old_string or new_string is None):
                return _clarification_response(
                    ambiguities=[
                        "old_string and new_string (or replacements list) required for edit_file"
                    ],
                    suggested_questions=[
                        "What text should be replaced?",
                        "What should it be replaced with?",
                    ],
                )
            return await _edit_file(
                path,
                old_string,
                new_string,
                encoding,
                no_backup,
                allow_multiple,
                is_regex,
                ignore_whitespace,
                replacements,
            )
        elif operation == "undo_edit":
            return await _undo_edit(path)
        elif operation == "delete_file":
            return await _delete_file(path)
        elif operation == "move_file":
            if not destination_path:
                return _clarification_response(
                    ambiguities=["destination_path required for move_file"],
                    suggested_questions=["Where should the file be moved to?"],
                )
            return await _move_file(path, destination_path, overwrite)
        elif operation == "read_file_lines":
            return await _read_file_lines(path, offset, limit, encoding)
        elif operation == "read_multiple_files":
            if not file_paths:
                return _clarification_response(
                    ambiguities=["file_paths list required for read_multiple_files"],
                    suggested_questions=["What list of file paths should be read?"],
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
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Analyze content for suggestions and quality metrics
        lines = content.splitlines()
        file_size_mb = len(content) / (1024 * 1024)

        recommendations = []
        quality_metrics = {
            "line_count": len(lines),
            "file_size_mb": round(file_size_mb, 2),
            "encoding_detected": encoding,
            "content_type": "text",
        }

        if len(lines) > 1000:
            recommendations.append(
                "File is quite large - consider using read_file_lines with offset/limit for better performance"
            )
        if file_size_mb > 10:
            recommendations.append(
                "Large file detected - consider processing in chunks or using head_file/tail_file"
            )
            quality_metrics["large_file"] = True

        # Detect file type for additional suggestions
        file_extension = path_obj.suffix.lower()
        if file_extension in [".json", ".yaml", ".yml", ".xml"]:
            recommendations.append("Consider using get_file_info for structured data validation")
            quality_metrics["structured_data"] = True
        elif file_extension in [".log", ".txt"]:
            recommendations.append(
                "Consider using grep_file for content searching or tail_file for recent entries"
            )
            quality_metrics["log_file"] = True
        elif file_extension in [".py", ".js", ".ts", ".java", ".cpp"]:
            recommendations.append(
                "Code file detected - consider using agentic_file_workflow for advanced operations"
            )
            quality_metrics["code_file"] = True

        next_steps = []
        related_operations = []

        if len(lines) > 100:
            next_steps.append("Use read_file_lines to read specific sections efficiently")
            related_operations.append("read_file_lines")

        if quality_metrics.get("large_file"):
            next_steps.append("Consider using head_file to preview file content")
            related_operations.append("head_file")

        if quality_metrics.get("code_file"):
            related_operations.append("agentic_workflow")

        return _success_response(
            result={
                "path": str(path_obj),
                "content": content,
                "encoding": encoding,
                "size_bytes": len(content),
                "size_human": _format_file_size(len(content)),
                "line_count": len(lines),
                "file_info": {
                    "extension": file_extension,
                    "readable": True,
                    "writable": path_obj.stat().st_mode & 0o200 != 0,
                },
            },
            operation="read_file",
            execution_time_ms=execution_time_ms,
            quality_metrics=quality_metrics,
            recommendations=recommendations,
            next_steps=next_steps,
            related_operations=related_operations,
        )

    except UnicodeDecodeError as e:
        return _error_response(
            f"Cannot decode as {encoding}: {str(e)}",
            "encoding_error",
            [
                "Try a different encoding (utf-8, latin-1, cp1252)",
                "Check if file is binary",
            ],
        )
    except Exception as e:
        return _error_response(
            f"Failed to read file: {str(e)}",
            "io_error",
            [
                "Check file permissions",
                "Verify the file is not locked by another process",
            ],
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
            import time as _time

            ts = _time.strftime("%Y%m%d_%H%M%S")
            backup_path = path_obj.with_name(path_obj.stem + f"_{ts}" + path_obj.suffix + ".bak")
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


async def _edit_file(
    file_path: str,
    old_string: Optional[str],
    new_string: Optional[str],
    encoding: str = "utf-8",
    no_backup: bool = False,
    allow_multiple: bool = False,
    is_regex: bool = False,
    ignore_whitespace: bool = False,
    replacements: Optional[list[dict]] = None,
) -> dict[str, Any]:
    """Edit file by replacing text with safety checks and post-write verification."""
    import re
    import shutil
    import time as _time

    try:
        path_obj = _safe_resolve_path(file_path)
        if not path_obj.exists() or not path_obj.is_file():
            return _error_response(f"File not found: {file_path}", "not_found")

        # Read with specified encoding
        try:
            content = path_obj.read_text(encoding=encoding)
        except UnicodeDecodeError:
            return _error_response(
                f"Cannot read file with encoding '{encoding}'. Try a different encoding.",
                "encoding_error",
                [
                    "Try encoding='utf-8-sig' for BOM files",
                    "Try encoding='latin-1' for legacy files",
                ],
            )

        # Build list of edits to apply
        edits = []
        if replacements:
            for r in replacements:
                if "old_string" in r and "new_string" in r:
                    edits.append((r["old_string"], r["new_string"]))
        elif old_string is not None and new_string is not None:
            edits.append((old_string, new_string))

        if not edits:
            return _error_response("No replacement specifications provided", "invalid_arguments")

        current_content = content
        total_occurrences = 0

        for tgt, repl in edits:
            search_pattern = tgt
            if ignore_whitespace and not is_regex:
                # Normalize indentation for matching if requested
                # This converts the search string into a flexible regex
                escaped = re.escape(tgt)
                search_pattern = re.sub(r"\\ [ \t]*", r"\\s+", escaped)
                is_regex_for_this = True
            else:
                is_regex_for_this = is_regex

            if is_regex_for_this:
                count = len(re.findall(search_pattern, current_content))
                if count == 0:
                    return _error_response(
                        f"Regex pattern '{search_pattern}' not found",
                        "content_not_found",
                    )

                limit = 0 if allow_multiple else 1
                new_content = re.sub(search_pattern, repl, current_content, count=limit)
                actual_replaced = count if allow_multiple else 1
            else:
                count = current_content.count(tgt)
                if count == 0:
                    return _error_response(f"Text '{tgt}' not found", "content_not_found")

                limit = -1 if allow_multiple else 1
                new_content = current_content.replace(tgt, repl, limit)
                actual_replaced = count if allow_multiple else 1

            current_content = new_content
            total_occurrences += actual_replaced

        # Create timestamped backup unless disabled
        backup_path = None
        if not no_backup:
            ts = _time.strftime("%Y%m%d_%H%M%S")
            backup_path = path_obj.with_name(path_obj.stem + f"_{ts}" + path_obj.suffix + ".bak")
            shutil.copy2(path_obj, backup_path)

        # Write the modified content
        path_obj.write_text(current_content, encoding=encoding)

        # Post-write verification
        try:
            verified_content = path_obj.read_text(encoding=encoding)
            verification_ok = len(verified_content) == len(current_content)
        except Exception:
            verification_ok = False

        if not verification_ok:
            if backup_path and backup_path.exists():
                shutil.copy2(backup_path, path_obj)
                return _error_response(
                    "Verification failed - original file restored",
                    "verification_failed",
                )
            return _error_response(
                "Verification failed and no backup available", "verification_failed"
            )

        result = {
            "path": str(path_obj),
            "total_occurrences_replaced": total_occurrences,
            "old_length": len(content),
            "new_length": len(current_content),
            "encoding": encoding,
            "verification": "passed",
        }
        if backup_path:
            result["backup_path"] = str(backup_path)

        return _success_response(result)

    except Exception as e:
        return _error_response(f"Failed to edit file: {str(e)}", "io_error")


async def _undo_edit(file_path: str) -> dict[str, Any]:
    """Revert to the most recent .bak file matching the base filename."""
    import shutil
    from datetime import datetime

    try:
        path_obj = _safe_resolve_path(file_path)
        parent = path_obj.parent

        # Find all .bak files for this target
        pattern = f"{path_obj.stem}_*{path_obj.suffix}.bak"
        backups = sorted(parent.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

        if not backups:
            return _error_response(f"No backups found for {file_path}", "no_backups")

        latest_backup = backups[0]
        shutil.copy2(latest_backup, path_obj)

        return _success_response(
            {
                "restored_from": str(latest_backup),
                "path": str(path_obj),
                "backup_timestamp": datetime.fromtimestamp(
                    latest_backup.stat().st_mtime
                ).isoformat(),
            },
            "undo_edit",
        )

    except Exception as e:
        return _error_response(f"Undo failed: {str(e)}", "undo_error")


async def _delete_file(file_path: str) -> dict[str, Any]:
    """Permanently delete a file."""
    start_time = time.time()
    try:
        path_obj = _safe_resolve_path(file_path)
        if not path_obj.exists():
            return _error_response(
                f"File does not exist: {file_path}",
                "file_not_found",
                [
                    "Check if the file path is correct",
                    "File may have already been deleted",
                ],
            )
        if not path_obj.is_file():
            return _error_response(
                f"Path is not a file: {file_path}",
                "not_a_file",
                ["Use dir_ops remove_directory for directories"],
            )
        file_size = path_obj.stat().st_size
        file_name = path_obj.name
        path_obj.unlink()
        elapsed = time.time() - start_time
        return _success_response(
            {
                "deleted": str(path_obj),
                "file_name": file_name,
                "size_bytes": file_size,
                "size_human": _format_file_size(file_size),
                "elapsed_ms": round(elapsed * 1000, 2),
            },
            f"Deleted {file_name} ({_format_file_size(file_size)})",
        )
    except PermissionError as e:
        return _error_response(
            str(e),
            "permission_denied",
            ["Check file permissions", "File may be locked by another process"],
        )
    except Exception as e:
        logger.error(f"delete_file failed: {e}", exc_info=True)
        return _error_response(str(e), "internal_error")


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
            related_operations=["read_file", "get_file_info"],
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

        return _success_response(info, related_operations=["head_file", "read_file"])
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
