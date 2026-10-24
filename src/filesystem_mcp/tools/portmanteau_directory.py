import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Literal

from .utils import (
    MUTATING,
    _clarification_response,
    _error_response,
    _format_file_size,
    _get_app,
    _safe_resolve_path,
    _success_response,
)

logger = logging.getLogger(__name__)


@_get_app().tool(annotations=MUTATING, version="2.3.0")
async def dir_ops(
    operation: Literal[
        "list_directory",
        "create_directory",
        "remove_directory",
        "directory_tree",
        "calculate_directory_size",
        "find_empty_directories",
        "copy_tree",
    ]
    | None = None,
    path: str | None = None,
    recursive: bool = False,
    include_hidden: bool = False,
    create_parents: bool = True,
    exist_ok: bool = True,
    max_depth: int = 3,
    pattern: str | None = None,
    exclude_patterns: list[str] | None = None,
    output_format: Literal["text", "json"] = "text",
    human_readable: bool = True,
    max_files: int = 1000,
    destination_path: str | None = None,
    engine: Literal["auto", "shutil", "robocopy"] = "auto",
    mirror: bool = False,
    dry_run: bool = False,
    overwrite: bool = False,
    timeout: int = 300,
) -> dict[str, Any]:
    """Directory structure and management operations.

    Operations: list_directory, create_directory, remove_directory, directory_tree,
    calculate_directory_size, find_empty_directories, copy_tree.

    Args: See Parameters block.

    ## Return Format
    {"success": bool, "action": str, "message": str, "result": {...}}
    - result for list_directory: {"items": [...], "total": int}
    - result for calculate_directory_size: {"size_bytes": int, "human_readable": str}

    ## Examples
    dir_ops(operation="list_directory", path="D:/Dev/repos", recursive=True)
    dir_ops(operation="directory_tree", path="D:/Dev/repos/arxiv-mcp/src", max_depth=2)
    dir_ops(operation="calculate_directory_size", path="D:/data", human_readable=True)
    """
    try:
        if not operation:
            return _clarification_response(
                "operation", "No operation specified", ["list_directory", "create_directory"]
            )

        if not path:
            return _clarification_response("path", f"Path is required for {operation}")

        if operation == "list_directory":
            return await _list_directory(path, recursive, include_hidden, max_files, exclude_patterns, True)
        elif operation == "create_directory":
            return await _create_directory(path, create_parents, exist_ok)
        elif operation == "remove_directory":
            return await _remove_directory(path, recursive)
        elif operation == "copy_tree":
            if not destination_path:
                return _clarification_response("destination_path", "destination_path is required for copy_tree")
            assert path is not None
            return await _copy_tree(path, destination_path, engine, mirror, dry_run, overwrite, timeout)
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
    exclude_patterns: list[str] | None,
    follow_symlinks: bool,
) -> dict[str, Any]:
    """List directory contents with FULL original metadata and logic."""
    try:
        path_obj = _safe_resolve_path(directory_path)
        if not path_obj.exists():
            return _error_response(f"Directory not found: {directory_path}", "not_found")
        if not path_obj.is_dir():
            return _error_response(
                f"Not a directory: {directory_path}",
                "not_a_directory",
                [
                    "Use fileops:file_ops with operation='read_file' to read a file",
                    "Use fileops:file_ops with operation='get_file_info' for file metadata",
                ],
            )

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
            recommendations.append("Large directory detected - consider find_large_files to identify space usage")

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
            related_operations=["calculate_directory_size", "find_large_files", "search_ops"],
        )
    except Exception as e:
        return _error_response(f"Failed to list directory: {e!s}", "directory_access_error")


async def _create_directory(directory_path: str, create_parents: bool, exist_ok: bool) -> dict[str, Any]:
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
        return _error_response(f"Failed to create directory: {e!s}", "io_error")


async def _remove_directory(directory_path: str, recursive: bool) -> dict[str, Any]:
    """Remove directory."""
    try:
        path_obj = _safe_resolve_path(directory_path)
        if not path_obj.exists():
            return _error_response(f"Directory does not exist: {directory_path}", "not_found")
        if not path_obj.is_dir():
            return _error_response(
                f"Path is not a directory: {directory_path}",
                "not_a_directory",
                [
                    "Use fileops:file_ops with operation='read_file' to read a file",
                    "Use fileops:file_ops with operation='get_file_info' for file metadata",
                ],
            )

        if recursive:
            await asyncio.to_thread(shutil.rmtree, path_obj)
        else:
            path_obj.rmdir()
        return _success_response({"path": str(path_obj), "recursive": recursive})
    except Exception as e:
        return _error_response(f"Failed to remove directory: {e!s}", "io_error")


async def _directory_tree(
    directory_path: str,
    max_depth: int,
    include_files: bool,
    pattern: str | None,
    exclude_patterns: list[str] | None,
    output_format: str,
) -> dict[str, Any]:
    """Generate directory tree."""
    try:
        path_obj = _safe_resolve_path(directory_path)
        if not path_obj.exists():
            return _error_response(f"Directory does not exist: {directory_path}", "not_found")
        if not path_obj.is_dir():
            return _error_response(
                f"Path is not a directory: {directory_path}",
                "not_a_directory",
                [
                    "Use fileops:file_ops with operation='read_file' to read a file",
                    "Use fileops:file_ops with operation='get_file_info' for file metadata",
                ],
            )

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
        return _error_response(f"Failed to generate directory tree: {e!s}", "io_error")


async def _calculate_directory_size(directory_path: str, include_hidden: bool, human_readable: bool) -> dict[str, Any]:
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
        return _error_response(f"Failed to calculate size: {e!s}", "io_error")


async def _find_empty_directories(directory_path: str, recursive: bool, include_hidden: bool) -> dict[str, Any]:
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
        return _error_response(f"Failed to find empty directories: {e!s}", "io_error")


async def _copy_tree(
    source: str,
    destination: str,
    engine: str,
    mirror: bool,
    dry_run: bool,
    overwrite: bool,
    timeout: int,
) -> dict[str, Any]:
    """Copy a directory tree. shutil is default; robocopy is explicit opt-in on Windows.

    mirror=True maps to robocopy /MIR (deletes dest extras) and is refused
    unless engine='robocopy'. dry_run maps to robocopy /L or a shutil walk-through.
    """
    try:
        src = _safe_resolve_path(source)
        dst = _safe_resolve_path(destination)
    except Exception as e:
        return _error_response(f"Invalid path: {e!s}", "invalid_arguments")
    if not src.exists() or not src.is_dir():
        return _error_response(f"Invalid source directory: {source}", "not_found")
    if src == dst:
        return _error_response("Source and destination are the same", "invalid_arguments")
    try:
        # Refuse dst-inside-src (would recurse forever) on either engine.
        dst.relative_to(src)
        return _error_response(
            "Destination inside source would recurse forever",
            "invalid_arguments",
            ["Choose a destination outside the source tree"],
        )
    except ValueError:
        pass

    requested = (engine or "auto").lower()
    use_robocopy = requested == "robocopy"
    if requested not in ("auto", "shutil", "robocopy"):
        return _error_response(
            f"Unknown engine: {engine}",
            "invalid_arguments",
            ["Use auto (shutil), shutil, or robocopy (Windows opt-in)"],
        )
    if mirror and not use_robocopy:
        return _error_response(
            "mirror=True requires engine='robocopy' (/MIR deletes dest extras)",
            "invalid_arguments",
            ["Re-run with engine='robocopy', mirror=True", "Or drop mirror for an additive copy"],
        )
    if use_robocopy:
        import sys

        if sys.platform != "win32":
            return _error_response(
                "engine='robocopy' is Windows-only",
                "unsupported_platform",
                ["Use engine='shutil' on this platform"],
            )
        if shutil.which("robocopy") is None:
            return _error_response(
                "robocopy not found on PATH",
                "missing_dependency",
                ["Use engine='shutil' instead"],
            )
        return await _copy_tree_robocopy(src, dst, mirror, dry_run, timeout)
    return await _copy_tree_shutil(src, dst, overwrite, dry_run)


async def _copy_tree_shutil(src: Path, dst: Path, overwrite: bool, dry_run: bool) -> dict[str, Any]:
    """Cross-platform copy via shutil. dry_run walks without writing."""
    try:
        total_bytes = 0
        file_count = 0
        for root, _, files in os.walk(src):
            for name in files:
                try:
                    total_bytes += os.path.getsize(os.path.join(root, name))
                    file_count += 1
                except OSError:
                    pass
        if dry_run:
            return _success_response(
                {
                    "source": str(src),
                    "destination": str(dst),
                    "engine": "shutil",
                    "dry_run": True,
                    "file_count": file_count,
                    "total_bytes": total_bytes,
                    "total_human": _format_file_size(total_bytes),
                }
            )
        if dst.exists():
            if not overwrite:
                return _error_response(
                    f"Destination exists: {dst}",
                    "already_exists",
                    ["Re-run with overwrite=True to merge into it"],
                )
            if not dst.is_dir():
                return _error_response(f"Destination is not a directory: {dst}", "not_a_directory")
            await asyncio.to_thread(shutil.copytree, src, dst, dirs_exist_ok=True)
        else:
            if dst.parent and not dst.parent.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(shutil.copytree, src, dst)
        return _success_response(
            {
                "source": str(src),
                "destination": str(dst),
                "engine": "shutil",
                "file_count": file_count,
                "total_bytes": total_bytes,
                "total_human": _format_file_size(total_bytes),
                "mirror": False,
            }
        )
    except Exception as e:
        return _error_response(f"Failed to copy tree: {e!s}", "io_error")


async def _copy_tree_robocopy(src: Path, dst: Path, mirror: bool, dry_run: bool, timeout: int) -> dict[str, Any]:
    """Windows-only robocopy harness. Fixed flag allowlist, no shell=True.

    Exit codes 0-7 are success per robocopy docs; >= 8 is failure.
    """
    # Fixed allowlist — never accept freeform flags.
    cmd = ["robocopy", str(src), str(dst), "/E", "/R:2", "/W:1", "/MT:8", "/NP"]
    if mirror:
        # /MIR implies /E; replace /E with /MIR to keep intent explicit.
        cmd = ["robocopy", str(src), str(dst), "/MIR", "/R:2", "/W:1", "/MT:8", "/NP"]
    if dry_run:
        cmd.append("/L")
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            try:
                proc.kill()
            except Exception as kill_err:
                logger.warning("robocopy kill after timeout failed: %s", kill_err)
            return _error_response(
                f"robocopy timed out after {timeout}s",
                "timeout",
                ["Retry with a larger timeout", "Or use engine='shutil'"],
            )
        code = proc.returncode or 0
        out = (stdout or b"").decode(errors="replace")
        err = (stderr or b"").decode(errors="replace")
        # Keep output bounded — robocopy is chatty.
        tail = "\n".join(out.splitlines()[-25:])
        if code >= 8:
            return _error_response(
                f"robocopy failed with exit code {code}",
                "copy_error",
                ["Check source/dest permissions and long paths", "Or retry with engine='shutil'"],
                diagnostic_info={"exit_code": code, "stdout_tail": tail, "stderr": err[:2000]},
            )
        return _success_response(
            {
                "source": str(src),
                "destination": str(dst),
                "engine": "robocopy",
                "mirror": mirror,
                "dry_run": dry_run,
                "exit_code": code,
                "stdout_tail": tail,
            }
        )
    except Exception as e:
        return _error_response(f"robocopy harness failed: {e!s}", "internal_error")
