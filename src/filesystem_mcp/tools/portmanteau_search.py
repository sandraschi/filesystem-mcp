import asyncio
import difflib
import fnmatch
import hashlib
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from .utils import (
    READ_ONLY,
    _clarification_response,
    _error_response,
    _get_app,
    _safe_resolve_path,
    _success_response,
)

logger = logging.getLogger(__name__)


@_get_app().tool(annotations=READ_ONLY, version="2.3.0")
async def search_ops(
    operation: Literal[
        "grep_file",
        "count_pattern",
        "search_files",
        "extract_log_lines",
        "compare_files",
        "find_duplicate_files",
        "find_large_files",
    ],
    path: str | None = None,
    encoding: str = "utf-8",
    recursive: bool = False,
    include_hidden: bool = False,
    search_pattern: str | None = None,
    case_sensitive: bool = False,
    max_matches: int = 100,
    context_lines: int = 0,
    start_time: str | None = None,
    end_time: str | None = None,
    log_levels: list[str] | None = None,
    exclude_log_levels: list[str] | None = None,
    max_lines: int = 100,
    path2: str | None = None,
    min_size_mb: float = 100.0,
    min_size: int = 1,
    max_results: int = 100,
    hash_algorithm: Literal["md5", "sha256"] = "md5",
    max_duplicates: int | None = None,
    early_exit: bool = True,
) -> dict[str, Any]:
    """Content Analysis, Grep, and Comparison operations.

    Operations: grep_file, count_pattern, search_files, extract_log_lines,
    compare_files, find_duplicate_files, find_large_files.

    Args:
        operation: Operation to perform (required)
        path: Base path for search/analysis
        search_pattern: Regex or glob pattern (required for grep/count/search)
        path2: Second file for compare_files
        recursive: Search subdirectories (grep_file on a directory, search_files,
            find_*). Default: False
        case_sensitive: Pattern sensitivity. Default: False
        max_matches (int): Limit grep results. Default: 100
        context_lines: Lines around grep matches. Default: 0
        start_time/end_time: ISO timestamps for extract_log_lines
        log_levels/exclude_log_levels: Log level filters
        min_size_mb: Threshold for find_large_files. Default: 100.0
        min_size: Threshold for find_duplicate_files (bytes). Default: 1
        hash_algorithm: "md5" or "sha256". Default: "md5"
        max_duplicates: Stop after finding N duplicates. Default: None
        early_exit: Exit early when max_results reached. Default: True
    """
    try:
        if not operation:
            return _clarification_response(
                "operation", "No operation specified", ["grep_file", "search_files"]
            )

        if not path:
            return _clarification_response("path", f"Path is required for {operation}")

        if operation == "grep_file":
            if not search_pattern:
                return _clarification_response(
                    "search_pattern", "search_pattern is required for grep_file"
                )
            return await _grep_file(
                path,
                search_pattern,
                case_sensitive,
                max_matches,
                context_lines,
                encoding,
                recursive,
                include_hidden,
            )
        elif operation == "count_pattern":
            if not search_pattern:
                return _clarification_response(
                    "search_pattern", "search_pattern is required for count_pattern"
                )
            return await _count_pattern(path, search_pattern, case_sensitive, encoding)
        elif operation == "search_files":
            if not search_pattern:
                return _clarification_response(
                    "search_pattern", "search_pattern (glob) is required for search_files"
                )
            return await _search_files(path, search_pattern, recursive, include_hidden, max_results)
        elif operation == "extract_log_lines":
            return await _extract_log_lines(
                path,
                search_pattern,
                None,
                log_levels,
                exclude_log_levels,
                start_time,
                end_time,
                max_lines,
                encoding,
            )
        elif operation == "compare_files":
            if not path2:
                return _clarification_response("path2", "path2 is required for compare_files")
            return await _compare_files(path, path2, encoding)
        elif operation == "find_duplicate_files":
            return await _find_duplicate_files(
                path, recursive, min_size, include_hidden, max_results, hash_algorithm, max_duplicates
            )
        elif operation == "find_large_files":
            return await _find_large_files(
                path, min_size_mb, recursive, max_results, include_hidden, early_exit
            )
        else:
            return _error_response(f"Unknown operation: {operation}", "unsupported_operation")
    except Exception as e:
        logger.error(f"Search operation '{operation}' failed: {e}", exc_info=True)
        return _error_response(str(e), "internal_error")


_GREP_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".ruff_cache",
    ".pytest_cache",
    ".mypy_cache",
    "target",
    "dist",
    "build",
    ".tox",
    ".eggs",
}
_GREP_MAX_FILE_BYTES = 5 * 1024 * 1024  # skip files larger than 5 MB in directory grep
_GREP_MAX_FILES = 10_000  # hard cap on files visited in one directory grep


def _looks_binary(file_path: Path) -> bool:
    """Cheap binary sniff: NUL byte in the first 1 KiB."""
    try:
        with open(file_path, "rb") as f:
            return b"\x00" in f.read(1024)
    except OSError:
        return True


def _grep_lines(
    lines: list[str],
    regex: re.Pattern,
    max_matches: int,
    context_lines: int,
    file_path: str | None = None,
) -> list[dict[str, Any]]:
    """Collect match dicts from pre-split lines (sync, CPU-bound)."""
    matches: list[dict[str, Any]] = []
    for i, line in enumerate(lines):
        m = regex.search(line)
        if not m:
            continue
        match_info: dict[str, Any] = {
            "line_number": i + 1,
            "content": line,
            "match": m.group(0),
        }
        if file_path is not None:
            match_info["file"] = file_path
        if context_lines > 0:
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            match_info["context"] = {"before": lines[start:i], "after": lines[i + 1 : end]}
        matches.append(match_info)
        if len(matches) >= max_matches:
            break
    return matches


async def _grep_file(
    file_path: str,
    pattern: str,
    case_sensitive: bool,
    max_matches: int,
    context_lines: int,
    encoding: str,
    recursive: bool = False,
    include_hidden: bool = False,
) -> dict[str, Any]:
    """Grep a single file, or every text file under a directory.

    All file IO and regex work runs in a worker thread (asyncio.to_thread) so a
    large file or tree can never block the server event loop.
    """
    path_obj = _safe_resolve_path(file_path)
    if not path_obj.exists():
        return _error_response(f"Path does not exist: {file_path}", "not_found")

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return _error_response(f"Invalid regex pattern: {e!s}", "invalid_regex")

    if path_obj.is_dir():
        return await asyncio.to_thread(
            _grep_directory_sync,
            path_obj,
            regex,
            pattern,
            max_matches,
            context_lines,
            encoding,
            recursive,
            include_hidden,
        )
    return await asyncio.to_thread(
        _grep_single_file_sync, path_obj, regex, pattern, max_matches, context_lines, encoding
    )


def _grep_single_file_sync(
    path_obj: Path,
    regex: re.Pattern,
    pattern: str,
    max_matches: int,
    context_lines: int,
    encoding: str,
) -> dict[str, Any]:
    """Grep one file. Runs in a worker thread."""
    try:
        content = path_obj.read_text(encoding=encoding)
    except UnicodeDecodeError as e:
        return _error_response(f"Cannot decode as {encoding}: {e!s}", "encoding_error")
    except OSError as e:
        return _error_response(f"Failed to grep file: {e!s}", "io_error")

    matches = _grep_lines(content.splitlines(), regex, max_matches, context_lines)
    return _success_response(
        {
            "pattern": pattern,
            "matches": matches,
            "total_matches": len(matches),
            "max_matches_reached": len(matches) >= max_matches,
            "file_path": str(path_obj),
            "encoding": encoding,
        },
        next_steps=[f"file_ops(operation='read_file', path='{path_obj}')"],
        related_operations=["count_pattern", "edit_file"],
    )


def _grep_directory_sync(
    root: Path,
    regex: re.Pattern,
    pattern: str,
    max_matches: int,
    context_lines: int,
    encoding: str,
    recursive: bool,
    include_hidden: bool,
) -> dict[str, Any]:
    """Grep every text file under a directory. Runs in a worker thread.

    Prunes VCS/build/cache dirs, skips binary and oversized files, and stops at
    max_matches or _GREP_MAX_FILES, whichever comes first.
    """
    matches: list[dict[str, Any]] = []
    files_scanned = 0
    files_skipped = 0
    done = False

    walker = os.walk(root) if recursive else [(str(root), [], os.listdir(str(root)))]
    for dirpath, dirnames, filenames in walker:
        if done:
            break
        dirnames[:] = [
            d
            for d in dirnames
            if d not in _GREP_EXCLUDED_DIRS and (include_hidden or not d.startswith("."))
        ]
        for name in filenames:
            if len(matches) >= max_matches or files_scanned >= _GREP_MAX_FILES:
                done = True
                break
            if not include_hidden and name.startswith("."):
                continue

            file_path = Path(dirpath) / name
            try:
                if not file_path.is_file():
                    continue
                if file_path.stat().st_size > _GREP_MAX_FILE_BYTES or _looks_binary(file_path):
                    files_skipped += 1
                    continue
                content = file_path.read_text(encoding=encoding)
            except (UnicodeDecodeError, OSError):
                files_skipped += 1
                continue

            files_scanned += 1
            remaining = max_matches - len(matches)
            matches.extend(
                _grep_lines(
                    content.splitlines(), regex, remaining, context_lines, file_path=str(file_path)
                )
            )

    return _success_response(
        {
            "pattern": pattern,
            "matches": matches,
            "total_matches": len(matches),
            "max_matches_reached": len(matches) >= max_matches,
            "directory": str(root),
            "recursive": recursive,
            "files_scanned": files_scanned,
            "files_skipped": files_skipped,
            "files_cap_reached": files_scanned >= _GREP_MAX_FILES,
            "encoding": encoding,
        },
        next_steps=["file_ops(operation='read_file', path='<match file>')"],
        related_operations=["search_files", "count_pattern"],
    )


async def _count_pattern(
    file_path: str, pattern: str, case_sensitive: bool, encoding: str
) -> dict[str, Any]:
    """Count pattern occurrences in file."""
    try:
        path_obj = _safe_resolve_path(file_path)
        if not path_obj.exists():
            return _error_response(f"File does not exist: {file_path}", "not_found")
        if not path_obj.is_file():
            return _error_response(f"Path is not a file: {file_path}", "not_a_file")

        content = path_obj.read_text(encoding=encoding)

        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return _error_response(f"Invalid regex pattern: {e!s}", "invalid_regex")

        matches = regex.findall(content)
        count = len(matches)

        return _success_response(
            {
                "pattern": pattern,
                "count": count,
                "file_path": str(path_obj),
                "encoding": encoding,
            }
        )

    except UnicodeDecodeError as e:
        return _error_response(f"Cannot decode as {encoding}: {e!s}", "encoding_error")
    except Exception as e:
        return _error_response(f"Failed to count pattern: {e!s}", "io_error")


async def _search_files(
    directory_path: str, pattern: str, recursive: bool, include_hidden: bool, max_results: int
) -> dict[str, Any]:
    """Search for files matching pattern."""
    try:
        path_obj = _safe_resolve_path(directory_path)
        if not path_obj.exists() or not path_obj.is_dir():
            return _error_response(f"Invalid directory path: {directory_path}", "not_found")

        matching_files = []

        for root, _dirs, files in (
            os.walk(path_obj) if recursive else [(str(path_obj), [], os.listdir(path_obj))]
        ):
            for file in files:
                if not include_hidden and file.startswith("."):
                    continue

                if fnmatch.fnmatch(file, pattern):
                    file_path = Path(root) / file
                    try:
                        stat = file_path.stat()
                        matching_files.append(
                            {
                                "path": str(file_path),
                                "name": file,
                                "size": stat.st_size,
                                "modified": stat.st_mtime,
                            }
                        )

                        if len(matching_files) >= max_results:
                            break
                    except OSError:
                        pass

        return _success_response(
            {
                "directory": str(path_obj),
                "pattern": pattern,
                "matching_files": matching_files,
                "total_matches": len(matching_files),
                "max_results_reached": len(matching_files) >= max_results,
            }
        )

    except Exception as e:
        return _error_response(f"Failed to search files: {e!s}", "io_error")


async def _extract_log_lines(
    file_path: str,
    patterns: str | None,
    exclude_patterns: list[str] | None,
    log_levels: list[str] | None,
    exclude_log_levels: list[str] | None,
    start_time: str | None,
    end_time: str | None,
    max_lines: int,
    encoding: str,
) -> dict[str, Any]:
    """Extract and filter log lines with FULL original logic."""
    try:
        path_obj = _safe_resolve_path(file_path)
        if not path_obj.exists():
            return _error_response(f"File does not exist: {file_path}", "not_found")
        if not path_obj.is_file():
            return _error_response(f"Path is not a file: {file_path}", "not_a_file")

        content = path_obj.read_text(encoding=encoding)
        lines = content.splitlines()

        # Time filtering
        start_dt = None
        end_dt = None
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            except ValueError:
                pass
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Compile patterns
        include_patterns_compiled = []
        if patterns:
            try:
                include_patterns_compiled.append(re.compile(patterns, re.IGNORECASE))
            except re.error:
                pass

        exclude_regexes = []
        if exclude_patterns:
            for pattern in exclude_patterns:
                try:
                    exclude_regexes.append(re.compile(pattern, re.IGNORECASE))
                except re.error:
                    pass

        filtered_lines = []
        for line in lines:
            if len(filtered_lines) >= max_lines:
                break

            # Time filtering (basic ISO timestamp detection)
            if start_dt or end_dt:
                timestamp_match = re.match(
                    r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)", line
                )
                if timestamp_match:
                    try:
                        line_dt = datetime.fromisoformat(
                            timestamp_match.group(1).replace("Z", "+00:00")
                        )
                        if start_dt and line_dt < start_dt:
                            continue
                        if end_dt and line_dt > end_dt:
                            continue
                    except ValueError:
                        pass

            # Log level filtering
            if log_levels or exclude_log_levels:
                level_match = re.search(
                    r"\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL|TRACE)\b", line, re.IGNORECASE
                )
                if level_match:
                    level = level_match.group(1).upper()
                    if log_levels and level not in [lv.upper() for lv in log_levels]:
                        continue
                    if exclude_log_levels and level in [lv.upper() for lv in exclude_log_levels]:
                        continue

            # Pattern filtering
            if include_patterns_compiled:
                included = False
                for pattern in include_patterns_compiled:
                    if pattern.search(line):
                        included = True
                        break
                if not included:
                    continue

            # Exclude patterns
            excluded = False
            for pattern in exclude_regexes:
                if pattern.search(line):
                    excluded = True
                    break
            if excluded:
                continue

            filtered_lines.append(line)

        return _success_response(
            {
                "lines": filtered_lines,
                "total_lines": len(filtered_lines),
                "max_lines_reached": len(filtered_lines) >= max_lines,
                "file_path": str(path_obj),
                "encoding": encoding,
                "filters_applied": {
                    "patterns": bool(patterns),
                    "exclude_patterns": bool(exclude_patterns),
                    "log_levels": bool(log_levels),
                    "exclude_log_levels": bool(exclude_log_levels),
                    "time_range": bool(start_time or end_time),
                },
            }
        )

    except UnicodeDecodeError as e:
        return _error_response(f"Cannot decode as {encoding}: {e!s}", "encoding_error")
    except Exception as e:
        return _error_response(f"Failed to extract log lines: {e!s}", "io_error")


async def _compare_files(file_path_1: str, file_path_2: str, encoding: str) -> dict[str, Any]:
    """Compare two files."""
    try:
        path1 = _safe_resolve_path(file_path_1)
        path2 = _safe_resolve_path(file_path_2)

        if not path1.exists() or not path1.is_file():
            return _error_response(f"Invalid first file: {file_path_1}", "not_found")
        if not path2.exists() or not path2.is_file():
            return _error_response(f"Invalid second file: {file_path_2}", "not_found")

        content1 = path1.read_text(encoding=encoding)
        content2 = path2.read_text(encoding=encoding)

        diff = list(
            difflib.unified_diff(
                content1.splitlines(keepends=True),
                content2.splitlines(keepends=True),
                fromfile=str(path1),
                tofile=str(path2),
            )
        )

        return _success_response(
            {
                "file1": str(path1),
                "file2": str(path2),
                "are_identical": content1 == content2,
                "diff": "".join(diff),
                "diff_lines": len(diff),
            }
        )

    except Exception as e:
        return _error_response(f"Failed to compare files: {e!s}", "io_error")


async def _find_duplicate_files(
    directory_path: str,
    recursive: bool,
    min_size: int,
    include_hidden: bool,
    max_files: int,
    hash_algorithm: str,
    max_duplicates: int | None,
) -> dict[str, Any]:
    """Find duplicate files with early exit protection."""
    try:
        path_obj = _safe_resolve_path(directory_path)
        if not path_obj.exists() or not path_obj.is_dir():
            return _error_response(f"Invalid directory path: {directory_path}", "not_found")

        file_hashes = {}
        duplicates = []
        files_processed = 0

        gen = (
            os.walk(path_obj) if recursive else [(str(path_obj), [], os.listdir(str(path_obj)))]
        )
        for root, _dirs, files in gen:
            # Early exit if max_duplicates reached
            if max_duplicates and len(duplicates) >= max_duplicates:
                break

            for file in files:
                # Early exit if max_duplicates reached
                if max_duplicates and len(duplicates) >= max_duplicates:
                    break

                if not include_hidden and file.startswith("."):
                    continue

                file_path = Path(root) / file
                try:
                    if file_path.stat().st_size < min_size:
                        continue

                    files_processed += 1
                    if files_processed > max_files:
                        break

                    # Full logic for hashing
                    hasher = hashlib.new(hash_algorithm)
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hasher.update(chunk)
                    file_hash = hasher.hexdigest()

                    if file_hash in file_hashes:
                        duplicates.append(
                            {"hash": file_hash, "files": [str(file_hashes[file_hash]), str(file_path)]}
                        )
                    else:
                        file_hashes[file_hash] = file_path

                except OSError:
                    pass

        return _success_response(
            {
                "directory": str(path_obj),
                "duplicates": duplicates,
                "total_duplicates": len(duplicates),
                "files_processed": files_processed,
                "max_duplicates_reached": max_duplicates is not None and len(duplicates) >= max_duplicates,
            }
        )

    except Exception as e:
        return _error_response(f"Failed to find duplicates: {e!s}", "io_error")


async def _find_large_files(
    directory_path: str, min_size_mb: float, recursive: bool, max_results: int, include_hidden: bool, early_exit: bool
) -> dict[str, Any]:
    """Find large files with proper early exit."""
    try:
        path_obj = _safe_resolve_path(directory_path)
        if not path_obj.exists() or not path_obj.is_dir():
            return _error_response(f"Invalid directory path: {directory_path}", "not_found")

        min_size_bytes = int(min_size_mb * 1024 * 1024)
        large_files = []
        done = False

        gen = (
            os.walk(path_obj) if recursive else [(str(path_obj), [], os.listdir(str(path_obj)))]
        )
        for root, _dirs, files in gen:
            if done and early_exit:
                break
            for file in files:
                if done and early_exit:
                    break

                if not include_hidden and file.startswith("."):
                    continue

                file_path = Path(root) / file
                try:
                    size = file_path.stat().st_size
                    if size >= min_size_bytes:
                        large_files.append(
                            {
                                "path": str(file_path),
                                "size_bytes": size,
                                "size_mb": round(size / (1024 * 1024), 2),
                            }
                        )

                        if len(large_files) >= max_results:
                            done = True
                            if early_exit:
                                break

                except OSError:
                    pass

        large_files.sort(key=lambda x: x["size_bytes"], reverse=True)

        return _success_response(
            {
                "directory": str(path_obj),
                "large_files": large_files,
                "min_size_mb": min_size_mb,
                "total_found": len(large_files),
                "max_results_reached": len(large_files) >= max_results,
            }
        )

    except Exception as e:
        return _error_response(f"Failed to find large files: {e!s}", "io_error")
