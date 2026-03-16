import difflib
import fnmatch
import hashlib
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Optional

from .utils import (
    _clarification_response,
    _error_response,
    _get_app,
    _safe_resolve_path,
    _success_response,
)

logger = logging.getLogger(__name__)


@_get_app().tool()
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
    path: Optional[str] = None,
    encoding: str = "utf-8",
    recursive: bool = False,
    include_hidden: bool = False,
    search_pattern: Optional[str] = None,
    case_sensitive: bool = False,
    max_matches: int = 100,
    context_lines: int = 0,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    log_levels: Optional[list[str]] = None,
    exclude_log_levels: Optional[list[str]] = None,
    max_lines: int = 100,
    path2: Optional[str] = None,
    min_size_mb: float = 100.0,
    min_size: int = 1,
    max_results: int = 100,
    hash_algorithm: Literal["md5", "sha256"] = "md5",
    max_duplicates: Optional[int] = None,
    early_exit: bool = True,
) -> dict[str, Any]:
    """Content Analysis, Grep, and Comparison operations.

    Args:
        operation (Literal, required): Available search operations:
            - "grep_file": Regex search in file (requires: path, search_pattern)
            - "count_pattern": Count occurrences (requires: path, search_pattern)
            - "search_files": Find files by name (requires: path, search_pattern as pattern)
            - "extract_log_lines": Filter logs (requires: path)
            - "compare_files": Diff two files (requires: path, path2)
            - "find_duplicate_files": Hash-based detection (requires: path)
            - "find_large_files": Locate big files (requires: path)

        --- PRIMARY PARAMETERS ---

        path (str | None): Base path for search/analysis
        encoding (str): Text encoding. Default: "utf-8"
        recursive (bool): Search subdirectories. Default: False
        include_hidden (bool): Include hidden items. Default: False

        --- SEARCH & PATTERN MATCHING ---

        search_pattern (str | None): Regex or glob pattern
        case_sensitive (bool): Pattern sensitivity. Default: False
        max_matches (int): Limit grep results. Default: 100
        context_lines (int): Lines around grep matches. Default: 0

        --- LOG EXTRACTION ---

        start_time (str | None): ISO timestamp start
        end_time (str | None): ISO timestamp end
        log_levels (List[str] | None): Levels to include
        exclude_log_levels (List[str] | None): Levels to skip
        max_lines (int): Max log lines. Default: 100

        --- COMPARISON & ANALYSIS ---

        path2 (str | None): Second file for comparison
        min_size_mb (float): Threshold for large files. Default: 100.0
        min_size (int): Threshold for duplicates (bytes). Default: 1
        max_results (int): Limit result count. Default: 100
        hash_algorithm (Literal): Hashing for duplicates. Default: "md5"
        max_duplicates (int | None): Stop after finding N duplicates. Default: None (no limit)
        early_exit (bool): Exit early when max_results reached in find_large_files. Default: True
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
                path, search_pattern, case_sensitive, max_matches, context_lines, encoding
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


async def _grep_file(
    file_path: str,
    pattern: str,
    case_sensitive: bool,
    max_matches: int,
    context_lines: int,
    encoding: str,
) -> dict[str, Any]:
    """Search for patterns in file with original full logic."""
    try:
        path_obj = _safe_resolve_path(file_path)
        if not path_obj.exists():
            return _error_response(f"File does not exist: {file_path}", "not_found")
        if not path_obj.is_file():
            return _error_response(f"Path is not a file: {file_path}", "not_a_file")

        content = path_obj.read_text(encoding=encoding)
        lines = content.splitlines()

        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return _error_response(f"Invalid regex pattern: {str(e)}", "invalid_regex")

        matches = []
        for i, line in enumerate(lines):
            if regex.search(line):
                match_info = {
                    "line_number": i + 1,
                    "content": line,
                    "match": regex.search(line).group(0) if regex.search(line) else "",
                }

                if context_lines > 0:
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    match_info["context"] = {"before": lines[start:i], "after": lines[i + 1 : end]}

                matches.append(match_info)

                if len(matches) >= max_matches:
                    break

        return _success_response(
            {
                "pattern": pattern,
                "matches": matches,
                "total_matches": len(matches),
                "max_matches_reached": len(matches) >= max_matches,
                "file_path": str(path_obj),
                "encoding": encoding,
            },
            next_steps=[f"file_ops(operation='read_file', path='{file_path}')"],
            related_operations=["count_pattern", "edit_file"],
        )

    except UnicodeDecodeError as e:
        return _error_response(f"Cannot decode as {encoding}: {str(e)}", "encoding_error")
    except Exception as e:
        return _error_response(f"Failed to grep file: {str(e)}", "io_error")


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
            return _error_response(f"Invalid regex pattern: {str(e)}", "invalid_regex")

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
        return _error_response(f"Cannot decode as {encoding}: {str(e)}", "encoding_error")
    except Exception as e:
        return _error_response(f"Failed to count pattern: {str(e)}", "io_error")


async def _search_files(
    directory_path: str, pattern: str, recursive: bool, include_hidden: bool, max_results: int
) -> dict[str, Any]:
    """Search for files matching pattern."""
    try:
        path_obj = _safe_resolve_path(directory_path)
        if not path_obj.exists() or not path_obj.is_dir():
            return _error_response(f"Invalid directory path: {directory_path}", "not_found")

        matching_files = []

        for root, dirs, files in (
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
        return _error_response(f"Failed to search files: {str(e)}", "io_error")


async def _extract_log_lines(
    file_path: str,
    patterns: Optional[str],
    exclude_patterns: Optional[list[str]],
    log_levels: Optional[list[str]],
    exclude_log_levels: Optional[list[str]],
    start_time: Optional[str],
    end_time: Optional[str],
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
                    if log_levels and level not in [l.upper() for l in log_levels]:
                        continue
                    if exclude_log_levels and level in [l.upper() for l in exclude_log_levels]:
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
        return _error_response(f"Cannot decode as {encoding}: {str(e)}", "encoding_error")
    except Exception as e:
        return _error_response(f"Failed to extract log lines: {str(e)}", "io_error")


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
        return _error_response(f"Failed to compare files: {str(e)}", "io_error")


async def _find_duplicate_files(
    directory_path: str,
    recursive: bool,
    min_size: int,
    include_hidden: bool,
    max_files: int,
    hash_algorithm: str,
    max_duplicates: Optional[int],
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
        for root, dirs, files in gen:
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
        return _error_response(f"Failed to find duplicates: {str(e)}", "io_error")


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
        for root, dirs, files in gen:
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
        return _error_response(f"Failed to find large files: {str(e)}", "io_error")
