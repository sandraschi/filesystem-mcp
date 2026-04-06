"""
Concurrency-safe file operations for FileSystem-MCP with FastMCP 3.2+ support.

All write operations use atomic patterns and asyncio.Lock() per path to prevent
corruption when multiple clients access the same files simultaneously.
"""

import logging
from pathlib import Path
from typing import Any, Literal, Optional

import aiofiles

from ..concurrency import FileOperationError, file_manager
from .utils import (
    _clarification_response,
    _error_response,
    _get_app,
    _safe_resolve_path,
    _success_response,
)

logger = logging.getLogger(__name__)


@_get_app().tool()
async def file_ops_safe(
    operation: Literal[
        "read_file",
        "write_file",
        "edit_file",
        "delete_file",
        "move_file",
        "copy_file",
        "read_file_lines",
        "read_multiple_files",
        "file_exists",
        "get_file_info",
        "head_file",
        "tail_file",
        "create_directory",
        "delete_directory",
    ],
    path: Optional[str] = None,
    content: Optional[str] = None,
    encoding: str = "utf-8",
    old_string: Optional[str] = None,
    new_string: Optional[str] = None,
    old_str: Optional[str] = None,       # alias accepted from Claude str_replace tool
    new_str: Optional[str] = None,       # alias accepted from Claude str_replace tool
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
) -> dict[str, Any]:
    """
    Perform file operations with concurrency safety and atomic operations.

    This is the upgraded version of file_ops with FastMCP 3.2+ concurrency safety.
    All write operations use atomic patterns and proper locking to prevent
    corruption when multiple clients access the same files simultaneously.

    Args:
        operation: Type of file operation to perform
        path: File path for single-file operations
        content: Content to write (for write_file)
        encoding: File encoding (default: utf-8)
        old_string/new_string: Text to replace (for edit_file)
        old_str/new_str: Alias for old_string/new_string (Claude compatibility)
        file_paths: List of file paths (for read_multiple_files)
        destination_path: Target path (for move_file, copy_file)
        overwrite: Whether to overwrite existing files
        offset: Line number offset (for read_file_lines, head_file, tail_file)
        limit: Maximum number of lines/items to return
        lines: Number of lines for head/tail operations
        check_type: Check if path exists as file or any
        follow_symlinks: Whether to follow symbolic links
        include_content: Include file content in response (read_file always returns content)
        max_content_size: Maximum content size to include
        create_parents: Create parent directories if they don't exist

    Returns:
        Result of the file operation with concurrency safety information
    """
    try:
        # ── Write operations (concurrency-safe) ───────────────────────────────

        if operation == "write_file":
            if not path:
                return _error_response("path is required for write_file")
            safe_path = _safe_resolve_path(path)
            result = await file_manager.write_file_atomic(
                safe_path, content or "", create_parents=create_parents
            )
            return _success_response(f"File written atomically: {safe_path}", result)

        elif operation == "edit_file":
            if not path:
                return _error_response("path is required for edit_file")
            search_text = old_string or old_str or ""
            replace_text = new_string or new_str or ""
            if not search_text:
                return _error_response("old_string (or old_str) is required for edit_file")
            safe_path = _safe_resolve_path(path)
            modifications = [{"search": search_text, "replace": replace_text,
                               "options": {"global": False}}]
            result = await file_manager.modify_file_safe(safe_path, modifications)
            return _success_response(
                f"File modified: {result['changes_made']} change(s) applied", result
            )

        elif operation == "delete_file":
            if not path:
                return _error_response("path is required for delete_file")
            safe_path = _safe_resolve_path(path)
            result = await file_manager.delete_file_safe(safe_path)
            if result["deleted"]:
                return _success_response(f"File deleted: {safe_path}", result)
            return _clarification_response(f"File not found: {safe_path}", result)

        elif operation == "move_file":
            if not path or not destination_path:
                return _error_response("path and destination_path required for move_file")
            safe_src = _safe_resolve_path(path)
            safe_dst = _safe_resolve_path(destination_path)
            result = await file_manager.move_file_safe(
                safe_src, safe_dst, create_parents=create_parents
            )
            return _success_response(f"File moved: {safe_src} → {safe_dst}", result)

        elif operation == "copy_file":
            if not path or not destination_path:
                return _error_response("path and destination_path required for copy_file")
            safe_src = _safe_resolve_path(path)
            safe_dst = _safe_resolve_path(destination_path)
            result = await file_manager.copy_file_safe(
                safe_src, safe_dst, create_parents=create_parents
            )
            return _success_response(f"File copied: {safe_src} → {safe_dst}", result)

        elif operation == "create_directory":
            if not path:
                return _error_response("path is required for create_directory")
            safe_path = _safe_resolve_path(path)
            result = await file_manager.create_directory_safe(safe_path, parents=create_parents)
            return _success_response(f"Directory created: {safe_path}", result)

        elif operation == "delete_directory":
            if not path:
                return _error_response("path is required for delete_directory")
            safe_path = _safe_resolve_path(path)
            result = await file_manager.delete_directory_safe(safe_path, recursive=True)
            if result["deleted"]:
                return _success_response(f"Directory deleted: {safe_path}", result)
            return _clarification_response(f"Directory not found: {safe_path}", result)

        # ── Read operations (no locking needed) ───────────────────────────────

        elif operation == "read_file":
            if not path:
                return _error_response("path is required for read_file")
            safe_path = _safe_resolve_path(path)
            try:
                async with aiofiles.open(safe_path, "r", encoding=encoding) as f:
                    file_content = await f.read()
                return _success_response(
                    f"File read: {safe_path}",
                    {
                        "path": safe_path,
                        "content": file_content,
                        "size": len(file_content),
                        "encoding": encoding,
                        "concurrency_safe": "read_only",
                    },
                )
            except FileNotFoundError:
                return _error_response(f"File not found: {safe_path}")
            except Exception as exc:
                return _error_response(f"Failed to read {safe_path}: {exc}")

        elif operation == "read_file_lines":
            if not path:
                return _error_response("path is required for read_file_lines")
            safe_path = _safe_resolve_path(path)
            try:
                async with aiofiles.open(safe_path, "r", encoding=encoding) as f:
                    all_lines = await f.readlines()
                sliced = all_lines[offset:]
                if limit is not None:
                    sliced = sliced[:limit]
                return _success_response(
                    f"Read {len(sliced)} lines from {safe_path}",
                    {"path": safe_path, "lines": [l.rstrip("\n") for l in sliced],
                     "count": len(sliced), "offset": offset},
                )
            except FileNotFoundError:
                return _error_response(f"File not found: {safe_path}")
            except Exception as exc:
                return _error_response(f"Failed to read lines from {safe_path}: {exc}")

        elif operation == "head_file":
            if not path:
                return _error_response("path is required for head_file")
            safe_path = _safe_resolve_path(path)
            try:
                async with aiofiles.open(safe_path, "r", encoding=encoding) as f:
                    head_lines = []
                    async for line in f:
                        head_lines.append(line.rstrip("\n"))
                        if len(head_lines) >= lines:
                            break
                return _success_response(
                    f"Head {len(head_lines)} lines of {safe_path}",
                    {"path": safe_path, "lines": head_lines, "count": len(head_lines)},
                )
            except FileNotFoundError:
                return _error_response(f"File not found: {safe_path}")
            except Exception as exc:
                return _error_response(f"Failed to read head of {safe_path}: {exc}")

        elif operation == "tail_file":
            if not path:
                return _error_response("path is required for tail_file")
            safe_path = _safe_resolve_path(path)
            try:
                async with aiofiles.open(safe_path, "r", encoding=encoding) as f:
                    all_lines = await f.readlines()
                tail_lines = [l.rstrip("\n") for l in all_lines[-lines:]]
                return _success_response(
                    f"Tail {len(tail_lines)} lines of {safe_path}",
                    {"path": safe_path, "lines": tail_lines, "count": len(tail_lines)},
                )
            except FileNotFoundError:
                return _error_response(f"File not found: {safe_path}")
            except Exception as exc:
                return _error_response(f"Failed to read tail of {safe_path}: {exc}")

        elif operation == "read_multiple_files":
            if not file_paths:
                return _error_response("file_paths is required for read_multiple_files")
            results = []
            for fp in file_paths:
                safe_path = _safe_resolve_path(fp)
                try:
                    async with aiofiles.open(safe_path, "r", encoding=encoding) as f:
                        fc = await f.read()
                    entry: dict = {"path": safe_path, "size": len(fc),
                                   "encoding": encoding, "concurrency_safe": "read_only"}
                    if include_content and len(fc) <= max_content_size:
                        entry["content"] = fc
                    elif include_content:
                        entry["content"] = fc[:max_content_size] + "\n[TRUNCATED]"
                    results.append(entry)
                except FileNotFoundError:
                    results.append({"path": safe_path, "error": "File not found"})
                except Exception as exc:
                    results.append({"path": safe_path, "error": str(exc)})
            return _success_response(
                f"Read {len(results)} file(s)",
                {"files": results, "count": len(results), "concurrency_safe": "read_only"},
            )

        elif operation == "file_exists":
            if not path:
                return _error_response("path is required for file_exists")
            safe_path = _safe_resolve_path(path)
            p = Path(safe_path)
            exists = p.exists() if follow_symlinks else p.exists()
            if check_type == "file":
                exists = exists and p.is_file()
            return {
                "success": True, "path": safe_path,
                "exists": exists, "concurrency_safe": "read_only",
            }

        elif operation == "get_file_info":
            if not path:
                return _error_response("path is required for get_file_info")
            safe_path = _safe_resolve_path(path)
            p = Path(safe_path)
            if not p.exists():
                return _error_response(f"Path not found: {safe_path}")
            st = p.stat()
            return _success_response(
                f"File info: {safe_path}",
                {
                    "path": safe_path,
                    "size": st.st_size,
                    "modified": st.st_mtime,
                    "created": st.st_ctime,
                    "is_file": p.is_file(),
                    "is_directory": p.is_dir(),
                    "is_symlink": p.is_symlink(),
                    "concurrency_safe": "read_only",
                },
            )

        else:
            return _error_response(f"Unknown operation: {operation}")

    except FileOperationError as exc:
        return _error_response(f"Concurrency/file error: {exc}")
    except Exception as exc:
        return _error_response(f"Unexpected error in {operation}: {exc}")


@_get_app().tool()
async def get_lock_status() -> dict:
    """
    Get current file operation lock status for debugging concurrency issues.

    Returns:
        Current lock status — active locks and their locked/unlocked state.
    """
    return file_manager.get_lock_status()


@_get_app().tool()
async def test_concurrency_safety(operation: str = "write", num_clients: int = 5) -> dict:
    """
    Test file operation concurrency safety with multiple simultaneous clients.

    Simulates concurrent operations to verify that locking mechanisms prevent
    data corruption.  Supported operations: write, edit.

    Args:
        operation: Type of operation to test (write, edit)
        num_clients: Number of concurrent clients to simulate (default: 5)

    Returns:
        Test results showing whether concurrency safety is working.
    """
    import asyncio
    import tempfile
    import time

    test_dir = tempfile.mkdtemp()
    test_file = f"{test_dir}/test_{operation}_{num_clients}.txt"

    try:
        if operation == "write":
            async def write_client(client_id: int):
                return await file_manager.write_file_atomic(
                    test_file, f"Content from client {client_id} at {time.time()}"
                )
            results = await asyncio.gather(
                *[write_client(i) for i in range(num_clients)], return_exceptions=True
            )

        elif operation == "edit":
            await file_manager.write_file_atomic(test_file, "Initial content for testing")
            async def edit_client(client_id: int):
                return await file_manager.modify_file_safe(test_file, [
                    {"search": "content", "replace": f"content_c{client_id}"}
                ])
            results = await asyncio.gather(
                *[edit_client(i) for i in range(num_clients)], return_exceptions=True
            )

        else:
            return {"error": f"Test not implemented for operation: {operation}",
                    "concurrency_safe": False}

        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        errors = [str(r) for r in results if isinstance(r, Exception)]
        return {
            "test_operation": operation,
            "num_clients": num_clients,
            "successful": successful,
            "errors": errors,
            "concurrency_safe": len(errors) == 0,
        }
    finally:
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
