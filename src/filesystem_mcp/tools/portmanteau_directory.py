import logging
import os
import shutil
from pathlib import Path
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
async def dir_ops(
    operation: Literal[
        "list_directory",
        "create_directory",
        "remove_directory",
        "directory_tree",
        "calculate_directory_size",
        "find_empty_directories",
    ],
    path: Optional[str] = None,
    recursive: bool = False,
    include_hidden: bool = False,
    create_parents: bool = True,
    exist_ok: bool = True,
    max_depth: int = 3,
    pattern: Optional[str] = None,
    exclude_patterns: Optional[list[str]] = None,
    output_format: Literal["text", "json"] = "text",
    human_readable: bool = True,
    max_files: int = 1000,
) -> dict[str, Any]:
    """Directory structure and management operations.

    Args:
        operation (Literal, required): Available directory operations:
            - "list_directory": List contents with metadata (requires: path)
            - "create_directory": Create new directory (requires: path)
            - "remove_directory": Remove directory (requires: path)
            - "directory_tree": Generate visual tree (requires: path)
            - "calculate_directory_size": Get total size (requires: path)
            - "find_empty_directories": Locate empty dirs (requires: path)

        --- PRIMARY PARAMETERS ---

        path (str | None): Target directory path
        recursive (bool): Operate recursively. Default: False
        include_hidden (bool): Show hidden files. Default: False

        --- DIRECTORY CONFIGURATION ---

        create_parents (bool): Create missing parents. Default: True
        exist_ok (bool): Don't error if exists. Default: True
        max_depth (int): Max recursion depth for tree. Default: 3
        pattern (str | None): Filter pattern for tree
        exclude_patterns (List[str] | None): Patterns to skip
        output_format (Literal): Tree format (text/json). Default: "text"

        --- SIZE & LIMITS ---

        human_readable (bool): Format sizes. Default: True
        max_files (int): Max items to list. Default: 1000
    """
    try:
        if not operation:
            return _clarification_response(
                "operation", "No operation specified", ["list_directory", "create_directory"]
            )

        if not path:
            return _clarification_response("path", f"Path is required for {operation}")

        if operation == "list_directory":
            return await _list_directory(
                path, recursive, include_hidden, max_files, exclude_patterns, True
            )
        elif operation == "create_directory":
            return await _create_directory(path, create_parents, exist_ok)
        elif operation == "remove_directory":
            return await _remove_directory(path, recursive)
        elif operation == "directory_tree":
            return await _directory_tree(path, max_depth, True, pattern, exclude_patterns, "text")
        elif operation == "calculate_directory_size":
            return await _calculate_directory_size(path, include_hidden, human_readable)
        elif operation == "find_empty_directories":
            return await _find_empty_directories(path, recursive, include_hidden)
        else:
            return _error_response(f"Unknown operation: {operation}", "unsupported_operation")
    except Exception as e:
        logger.error(f"Directory operation '{operation}' failed: {e}", exc_info=True)
        return _error_response(str(e), "internal_error")


async def _list_directory(
    directory_path: str,
    recursive: bool,
    include_hidden: bool,
    max_files: int,
    exclude_patterns: Optional[list[str]],
    follow_symlinks: bool,
) -> dict[str, Any]:
    """List directory contents with FULL original metadata and logic."""
    try:
        path_obj = _safe_resolve_path(directory_path)
        if not path_obj.exists():
            return _error_response(f"Directory not found: {directory_path}", "not_found")
        if not path_obj.is_dir():
            return _error_response(f"Not a directory: {directory_path}", "not_a_directory")

        import re

        # Compile exclude patterns
        exclude_regexes = []
        if exclude_patterns:
            for pattern in exclude_patterns:
                try:
                    exclude_regexes.append(re.compile(pattern))
                except re.error:
                    logger.warning(f"Invalid exclude pattern: {pattern}")

        files = []
        total_size = 0
        file_count = 0
        dir_count = 0

        def should_exclude(name: str) -> bool:
            if not include_hidden and name.startswith("."):
                return True
            for regex in exclude_regexes:
                if regex.search(name):
                    return True
            return False

        def scan_dir(dir_path: Path) -> None:
            nonlocal file_count, dir_count, total_size
            if len(files) >= max_files:
                return

            try:
                entries = list(os.scandir(dir_path))
                for entry in entries:
                    if len(files) >= max_files:
                        return

                    if should_exclude(entry.name):
                        continue

                    try:
                        stat = entry.stat(follow_symlinks=follow_symlinks)
                        is_dir = entry.is_dir(follow_symlinks=follow_symlinks)

                        item = {
                            "name": entry.name,
                            "path": str(Path(entry.path)),
                            "type": "directory" if is_dir else "file",
                            "size": stat.st_size if not is_dir else 0,
                            "modified": stat.st_mtime,
                            "permissions": oct(stat.st_mode)[-3:],
                        }

                        if is_dir:
                            dir_count += 1
                            if recursive:
                                scan_dir(Path(entry.path))
                        else:
                            file_count += 1
                            total_size += stat.st_size

                        files.append(item)

                    except (PermissionError, FileNotFoundError):
                        pass

            except (PermissionError, FileNotFoundError):
                pass

        scan_dir(path_obj)

        recommendations = []
        if len(files) >= max_files:
            recommendations.append(
                f"Results truncated at {max_files} items - consider using filters or smaller directories"
            )
        if dir_count > file_count * 2:
            recommendations.append(
                "Directory-heavy structure detected - consider recursive=true for deeper exploration"
            )
        if total_size > 100 * 1024 * 1024:  # 100MB
            recommendations.append(
                "Large directory detected - consider find_large_files to identify space usage"
            )

        next_steps = []
        if file_count > 0:
            next_steps.append(f"file_ops(operation='read_file', path='{path_obj}/<filename>')")
        if dir_count > 0 and not recursive:
            next_steps.append(f"dir_ops(operation='list_directory', path='{path_obj}', recursive=True)")
        if total_size > 10 * 1024 * 1024:  # 10MB
            next_steps.append(f"dir_ops(operation='calculate_directory_size', path='{path_obj}')")

        return _success_response(
            {
                "directory": str(path_obj),
                "files": files,
                "total_files": file_count,
                "total_directories": dir_count,
                "total_items": file_count + dir_count,
                "total_size": total_size,
                "total_size_human": _format_file_size(total_size),
                "max_files_reached": len(files) >= max_files,
                "recommendations": recommendations,
                "summary": {
                    "structure": "directory_heavy" if dir_count > file_count else "file_heavy",
                    "size_category": "large"
                    if total_size > 100 * 1024 * 1024
                    else "medium"
                    if total_size > 1024 * 1024
                    else "small",
                },
            },
            next_steps=next_steps,
            related_ops=["calculate_directory_size", "find_large_files", "search_ops"],
        )
    except Exception as e:
        return _error_response(f"Failed to list directory: {str(e)}", "directory_access_error")


async def _create_directory(
    directory_path: str, create_parents: bool, exist_ok: bool
) -> dict[str, Any]:
    """Create directory."""
    try:
        path_obj = _safe_resolve_path(directory_path)
        if path_obj.exists() and not exist_ok:
            return _error_response(f"Directory already exists: {directory_path}", "already_exists")

        path_obj.mkdir(parents=create_parents, exist_ok=exist_ok)
        return _success_response(
            {
                "path": str(path_obj),
                "created": True,
                "parents_created": create_parents,
            }
        )
    except Exception as e:
        return _error_response(f"Failed to create directory: {str(e)}", "io_error")


async def _remove_directory(directory_path: str, recursive: bool) -> dict[str, Any]:
    """Remove directory."""
    try:
        path_obj = _safe_resolve_path(directory_path)
        if not path_obj.exists():
            return _error_response(f"Directory does not exist: {directory_path}", "not_found")
        if not path_obj.is_dir():
            return _error_response(f"Path is not a directory: {directory_path}", "not_a_directory")

        if recursive:
            shutil.rmtree(path_obj)
        else:
            path_obj.rmdir()
        return _success_response({"path": str(path_obj), "recursive": recursive})
    except Exception as e:
        return _error_response(f"Failed to remove directory: {str(e)}", "io_error")


async def _directory_tree(
    directory_path: str,
    max_depth: int,
    include_files: bool,
    pattern: Optional[str],
    exclude_patterns: Optional[list[str]],
    output_format: str,
) -> dict[str, Any]:
    """Generate directory tree."""
    try:
        path_obj = _safe_resolve_path(directory_path)
        if not path_obj.exists():
            return _error_response(f"Directory does not exist: {directory_path}", "not_found")
        if not path_obj.is_dir():
            return _error_response(f"Path is not a directory: {directory_path}", "not_a_directory")

        import fnmatch

        tree_lines = []
        file_count = 0
        dir_count = 0

        def build_tree(path: Path, prefix: str = "", depth: int = 0):
            nonlocal file_count, dir_count
            if depth > max_depth:
                return

            try:
                entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))
                for i, entry in enumerate(entries):
                    is_last = i == len(entries) - 1
                    entry_path = Path(entry.path)

                    if not include_files and entry.is_file():
                        continue

                    if pattern and not fnmatch.fnmatch(entry.name, pattern):
                        continue

                    if exclude_patterns:
                        excluded = False
                        for exclude in exclude_patterns:
                            if fnmatch.fnmatch(entry.name, exclude):
                                excluded = True
                                break
                        if excluded:
                            continue

                    connector = "└── " if is_last else "├── "
                    tree_lines.append(f"{prefix}{connector}{entry.name}")

                    if entry.is_dir():
                        dir_count += 1
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        build_tree(entry_path, next_prefix, depth + 1)
                    else:
                        file_count += 1

            except PermissionError:
                pass

        tree_lines.append(path_obj.name)
        build_tree(path_obj)

        return _success_response(
            {
                "directory": str(path_obj),
                "tree": "\n".join(tree_lines),
                "file_count": file_count,
                "directory_count": dir_count,
            }
        )
    except Exception as e:
        return _error_response(f"Failed to generate directory tree: {str(e)}", "io_error")


async def _calculate_directory_size(
    directory_path: str, include_hidden: bool, human_readable: bool
) -> dict[str, Any]:
    """Calculate directory size."""
    try:
        path_obj = _safe_resolve_path(directory_path)
        if not path_obj.exists() or not path_obj.is_dir():
            return _error_response(f"Invalid directory path: {directory_path}", "not_found")

        total_size = 0
        file_count = 0

        for root, _, files in os.walk(path_obj):
            for file in files:
                if not include_hidden and file.startswith("."):
                    continue
                try:
                    total_size += os.path.getsize(os.path.join(root, file))
                    file_count += 1
                except OSError:
                    pass

        result = {
            "directory": str(path_obj),
            "total_bytes": total_size,
            "file_count": file_count,
        }

        if human_readable:
            result["human_readable"] = _format_file_size(total_size)

        return _success_response(result)
    except Exception as e:
        return _error_response(f"Failed to calculate size: {str(e)}", "io_error")


async def _find_empty_directories(
    directory_path: str, recursive: bool, include_hidden: bool
) -> dict[str, Any]:
    """Find empty directories."""
    try:
        path_obj = _safe_resolve_path(directory_path)
        if not path_obj.exists() or not path_obj.is_dir():
            return _error_response(f"Invalid directory path: {directory_path}", "not_found")

        empty_dirs = []
        for root, dirs, files in os.walk(path_obj):
            # Filter hidden items
            if not include_hidden:
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                files = [f for f in files if not f.startswith(".")]

            if not dirs and not files:
                empty_dirs.append(root)

        return _success_response(
            {
                "directory": str(path_obj),
                "empty_directories": empty_dirs,
                "total_empty": len(empty_dirs),
            }
        )
    except Exception as e:
        return _error_response(f"Failed to find empty directories: {str(e)}", "io_error")
