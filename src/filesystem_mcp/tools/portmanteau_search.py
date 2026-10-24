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


@_get_app().tool(annotations=READ_ONLY, version="2.4.0")
async def search_ops(
    operation: Literal[
        "grep_file",
        "count_pattern",
        "search_files",
        "extract_log_lines",
        "compare_files",
        "find_duplicate_files",
        "find_large_files",
        "find_todos",
        "find_symbols",
        "validate_json",
        "analyze_project",
        "run_linter",
        "validate_config",
    ]
    | None = None,
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
    fix: bool = False,
) -> dict[str, Any]:
    """Content Analysis, Grep, and Comparison operations.

    Operations: grep_file, count_pattern, search_files, extract_log_lines,
    compare_files, find_duplicate_files, find_large_files,
    find_todos, find_symbols, validate_json,
    analyze_project, run_linter, validate_config.
    find_todos, find_symbols, validate_json.

    Pattern semantics (read this before picking an operation):
    - grep_file / count_pattern take a CONTENT regex searched inside file text.
    - search_files takes a FILENAME glob (fnmatch, e.g. "*.py", "test_*") matched
      against file names only — it never looks at file content. For content
      search across a tree, use grep_file with recursive=True.

    Args: See Parameters block.

    ## Return Format
    {"success": bool, "action": str, "message": str, "result": {...}}
    - grep_file: {"matches": [{"file": str, "line": int, "text": str}], "count": int}
    - count_pattern: {"count": int}
    - compare_files: {"diff": str, "lines": int}

    ## Examples
    search_ops(operation="grep_file", path="D:/Dev/repos", search_pattern="assfix", recursive=True)
    search_ops(operation="find_large_files", path="D:/data", min_size_mb=500)
    search_ops(operation="compare_files", path="a.txt", path2="b.txt")
    """
    try:
        if not operation:
            return _clarification_response("operation", "No operation specified", ["grep_file", "search_files"])

        if not path:
            return _clarification_response("path", f"Path is required for {operation}")

        if operation == "grep_file":
            if not search_pattern:
                return _clarification_response("search_pattern", "search_pattern is required for grep_file")
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
                return _clarification_response("search_pattern", "search_pattern is required for count_pattern")
            return await _count_pattern(path, search_pattern, case_sensitive, encoding)
        elif operation == "search_files":
            if not search_pattern:
                return _clarification_response("search_pattern", "search_pattern (glob) is required for search_files")
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
            return await _find_large_files(path, min_size_mb, recursive, max_results, include_hidden, early_exit)
        elif operation == "find_todos":
            return await _find_todos(path, recursive, include_hidden, max_matches, encoding, search_pattern)
        elif operation == "find_symbols":
            return await _find_symbols(path, recursive, include_hidden, max_matches, encoding, search_pattern)
        elif operation == "validate_json":
            return await _validate_json(path, encoding)
        elif operation == "analyze_project":
            return await _analyze_project(path, max_results)
        elif operation == "run_linter":
            return await _run_linter(path, fix, timeout_s=120)
        elif operation == "validate_config":
            return await _validate_config(path, encoding)
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
            d for d in dirnames if d not in _GREP_EXCLUDED_DIRS and (include_hidden or not d.startswith("."))
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
            matches.extend(_grep_lines(content.splitlines(), regex, remaining, context_lines, file_path=str(file_path)))

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


async def _count_pattern(file_path: str, pattern: str, case_sensitive: bool, encoding: str) -> dict[str, Any]:
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

        for root, _dirs, files in os.walk(path_obj) if recursive else [(str(path_obj), [], os.listdir(path_obj))]:
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
                        line_dt = datetime.fromisoformat(timestamp_match.group(1).replace("Z", "+00:00"))
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

        gen = os.walk(path_obj) if recursive else [(str(path_obj), [], os.listdir(str(path_obj)))]
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
                        duplicates.append({"hash": file_hash, "files": [str(file_hashes[file_hash]), str(file_path)]})
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

        gen = os.walk(path_obj) if recursive else [(str(path_obj), [], os.listdir(str(path_obj)))]
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


_TODO_DEFAULT = r"\b(TODO|FIXME|HACK|XXX|BUG)\b\s*:?\s*(.*)"


async def _find_todos(
    target: str,
    recursive: bool,
    include_hidden: bool,
    max_matches: int,
    encoding: str,
    override_pattern: str | None,
) -> dict[str, Any]:
    """Find TODO/FIXME-style comments. Thin wrapper over the grep machinery."""
    pattern = override_pattern or _TODO_DEFAULT
    try:
        re.compile(pattern)
    except re.error as e:
        return _error_response(f"Invalid regex pattern: {e!s}", "invalid_regex")
    res = await _grep_file(target, pattern, False, max_matches, 0, encoding, recursive, include_hidden)
    if not res.get("success"):
        return res
    result = res.get("result", {})
    matches = result.get("matches", [])
    todos = []
    for m in matches:
        fp = str(m.get("file") or "")
        if fp.endswith(".bak") or fp.endswith(".bak.json"):
            continue
        content = m.get("content", "")
        tag = re.search(r"\b(TODO|FIXME|HACK|XXX|BUG)\b", content, re.IGNORECASE)
        todos.append(
            {
                "file": m.get("file"),
                "line_number": m.get("line_number"),
                "tag": (tag.group(1).upper() if tag else "TODO"),
                "text": content.strip()[:300],
            }
        )
    return _success_response(
        {
            "pattern": pattern,
            "todos": todos,
            "total_matches": len(todos),
            "max_matches_reached": result.get("max_matches_reached", False),
            "files_scanned": result.get("files_scanned"),
            "files_skipped": result.get("files_skipped"),
        },
        related_operations=["grep_file", "read_file"],
    )


_SYMBOL_DEF = re.compile(
    r"^\s*(?:"
    r"(?:async\s+)?def\s+(?P<pydef>[A-Za-z_][A-Za-z0-9_]*)"
    r"|class\s+(?P<pyclass>[A-Za-z_][A-Za-z0-9_]*)"
    r"|function\s+(?P<jsfunc>[A-Za-z_$][A-Za-z0-9_$]*)"
    r"|(?:export\s+)?(?:async\s+)?(?:const|let|var)\s+(?P<jsconst>[A-Za-z_$][A-Za-z0-9_$]*)\s*="
    r"|(?:export\s+)?(?:interface|enum|type)\s+(?P<tstype>[A-Za-z_$][A-Za-z0-9_$]*)"
    r")"
)


async def _find_symbols(
    target: str,
    recursive: bool,
    include_hidden: bool,
    max_matches: int,
    encoding: str,
    filter_substring: str | None,
) -> dict[str, Any]:
    """Find def/class/function/const/interface definitions, optionally filtered by substring."""
    path_obj = _safe_resolve_path(target)
    if not path_obj.exists():
        return _error_response(f"Path does not exist: {target}", "not_found")
    filt = (filter_substring or "").lower()

    def _scan_file(fp: Path) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        if fp.suffix == ".bak" or fp.name.endswith(".bak"):
            return out
        try:
            if fp.stat().st_size > 5 * 1024 * 1024 or _looks_binary(fp):
                return out
            text = fp.read_text(encoding=encoding)
        except (UnicodeDecodeError, OSError):
            return out
        for i, line in enumerate(text.splitlines(), start=1):
            m = _SYMBOL_DEF.match(line)
            if not m:
                continue
            name = next((g for g in m.groups() if g), "")
            kind = (
                "def"
                if m.group("pydef")
                else "class"
                if m.group("pyclass")
                else "function"
                if m.group("jsfunc")
                else "const"
                if m.group("jsconst")
                else "type"
            )
            if filt and filt not in name.lower() and filt not in line.lower():
                continue
            out.append({"file": str(fp), "line_number": i, "kind": kind, "name": name, "text": line.strip()[:200]})
        return out

    async def _scan_dir(root: Path) -> list[dict[str, Any]]:
        def _walk() -> list[dict[str, Any]]:
            acc: list[dict[str, Any]] = []
            walker = os.walk(root) if recursive else [(str(root), [], os.listdir(str(root)))]
            for dirpath, dirnames, filenames in walker:
                dirnames[:] = [
                    d for d in dirnames if d not in _GREP_EXCLUDED_DIRS and (include_hidden or not d.startswith("."))
                ]
                for name in filenames:
                    if len(acc) >= max_matches:
                        return acc
                    if not include_hidden and name.startswith("."):
                        continue
                    fp = Path(dirpath) / name
                    acc.extend(_scan_file(fp))
                    if len(acc) >= max_matches:
                        return acc[:max_matches]
            return acc[:max_matches]

        return await asyncio.to_thread(_walk)

    try:
        if path_obj.is_dir():
            symbols = await _scan_dir(path_obj)
        else:
            symbols = await asyncio.to_thread(_scan_file, path_obj)
            symbols = symbols[:max_matches]
        return _success_response(
            {
                "symbols": symbols,
                "total_matches": len(symbols),
                "max_matches_reached": len(symbols) >= max_matches,
                "filter": filter_substring,
                "directory": str(path_obj) if path_obj.is_dir() else None,
                "file_path": str(path_obj) if path_obj.is_file() else None,
            },
            related_operations=["grep_file", "read_file"],
        )
    except Exception as e:
        return _error_response(f"Failed to find symbols: {e!s}", "io_error")


async def _validate_json(file_path: str, encoding: str) -> dict[str, Any]:
    """Parse JSON and report structure summary or the first syntax error."""
    import json

    try:
        path_obj = _safe_resolve_path(file_path)
        if not path_obj.exists() or not path_obj.is_file():
            return _error_response(f"Invalid file path: {file_path}", "not_found")
        text = path_obj.read_text(encoding=encoding)
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            return _success_response(
                {"path": str(path_obj), "valid": False, "error": str(e), "line": e.lineno, "column": e.colno}
            )
        summary: dict[str, Any] = {"type": type(data).__name__}
        if isinstance(data, dict):
            summary["keys"] = sorted(map(str, data.keys()))[:50]
            summary["key_count"] = len(data)
        elif isinstance(data, list):
            summary["length"] = len(data)
            if data:
                summary["first_item_type"] = type(data[0]).__name__
        return _success_response({"path": str(path_obj), "valid": True, "summary": summary})
    except UnicodeDecodeError as e:
        return _error_response(f"Cannot decode as {encoding}: {e!s}", "encoding_error")
    except Exception as e:
        return _error_response(f"Failed to validate JSON: {e!s}", "io_error")


_PROJECT_MARKERS: dict[str, str] = {
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "setup.py": "python",
    "package.json": "node",
    "pnpm-lock.yaml": "node",
    "Cargo.toml": "rust",
    "go.mod": "go",
    "pom.xml": "java",
    "build.gradle": "java",
    "CMakeLists.txt": "cpp",
    "Dockerfile": "docker",
    "docker-compose.yml": "docker",
}


async def _analyze_project(target: str, max_results: int) -> dict[str, Any]:
    """Detect project type via marker files + extension census (read-only, capped)."""
    from collections import Counter

    try:
        root = _safe_resolve_path(target)
        if not root.exists():
            return _error_response(f"Path does not exist: {target}", "not_found")
        if root.is_file():
            root = root.parent
        markers = {}
        for name, kind in _PROJECT_MARKERS.items():
            if (root / name).exists():
                markers[name] = kind
        kinds = sorted(set(markers.values()))
        project_type = kinds[0] if len(kinds) == 1 else ("polyglot" if kinds else "unknown")

        def _walk() -> Counter:
            counter: Counter = Counter()
            for _dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in _GREP_EXCLUDED_DIRS and not d.startswith(".")]
                for name in filenames:
                    if name.startswith(".") or name.endswith(".bak"):
                        continue
                    suffix = Path(name).suffix.lower() or "(no-ext)"
                    counter[suffix] += 1
            return counter

        counter = await asyncio.to_thread(_walk)
        top_ext = [{"extension": ext, "count": n} for ext, n in counter.most_common(max_results)]
        frameworks: list[str] = []
        try:
            pkg = root / "package.json"
            if pkg.exists():
                import json as _json

                data = _json.loads(pkg.read_text(encoding="utf-8", errors="replace"))
                deps = {**(data.get("dependencies", {})), **(data.get("devDependencies", {}))}
                for known in ("react", "vite", "next", "express", "fastify", "vue", "svelte"):
                    if known in deps:
                        frameworks.append(known)
        except Exception as e:
            logger.warning("analyze_project package.json read failed: %s", e)
        try:
            req = root / "requirements.txt"
            if req.exists():
                text = req.read_text(encoding="utf-8", errors="replace").lower()
                for known in ("fastapi", "starlette", "django", "flask", "pydantic", "pytest"):
                    if known in text:
                        frameworks.append(known)
            pyproject = root / "pyproject.toml"
            if pyproject.exists():
                text = pyproject.read_text(encoding="utf-8", errors="replace").lower()
                for known in ("fastmcp", "fastapi", "pydantic", "pytest", "ruff"):
                    if known in text and known not in frameworks:
                        frameworks.append(known)
        except Exception as e:
            logger.warning("analyze_project python deps read failed: %s", e)
        return _success_response(
            {
                "directory": str(root),
                "project_type": project_type,
                "markers": markers,
                "frameworks": sorted(set(frameworks)),
                "top_extensions": top_ext,
                "total_files": sum(counter.values()),
            },
            related_operations=["find_symbols", "find_todos"],
        )
    except Exception as e:
        return _error_response(f"Failed to analyze project: {e!s}", "io_error")


async def _run_linter(target: str, fix: bool, timeout_s: int = 120) -> dict[str, Any]:
    """Run ruff check (and optional --fix) on a file or directory. No other linters."""
    import shutil

    try:
        resolved = _safe_resolve_path(target)
        if not resolved.exists():
            return _error_response(f"Path does not exist: {target}", "not_found")
        ruff = shutil.which("ruff")
        if ruff is None:
            return _error_response(
                "ruff not found on PATH",
                "missing_dependency",
                ["Install ruff (uv tool install ruff) or run just lint in the repo"],
            )
        cmd = [ruff, "check", str(resolved)]
        if fix:
            cmd.append("--fix")
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
            except TimeoutError:
                try:
                    proc.kill()
                except Exception as kill_err:
                    logger.warning("ruff kill after timeout failed: %s", kill_err)
                return _error_response(
                    f"ruff timed out after {timeout_s}s",
                    "timeout",
                    ["Retry on a smaller path"],
                )
        except Exception as e:
            return _error_response(f"Failed to launch ruff: {e!s}", "internal_error")
        out = (stdout or b"").decode(errors="replace")
        err = (stderr or b"").decode(errors="replace")
        return _success_response(
            {
                "path": str(resolved),
                "fix": fix,
                "exit_code": proc.returncode or 0,
                "clean": (proc.returncode or 0) == 0,
                "output": (out + err)[-4000:],
            }
        )
    except Exception as e:
        return _error_response(f"Failed to run linter: {e!s}", "io_error")


async def _validate_config(file_path: str, encoding: str) -> dict[str, Any]:
    """Validate JSON/YAML/TOML/INI by extension. JSON reuses _validate_json."""
    try:
        path_obj = _safe_resolve_path(file_path)
        if not path_obj.exists() or not path_obj.is_file():
            return _error_response(f"Invalid file path: {file_path}", "not_found")
        suffix = path_obj.suffix.lower()
        if suffix == ".json":
            return await _validate_json(file_path, encoding)
        if suffix in (".yaml", ".yml"):
            try:
                import yaml  # type: ignore
            except ImportError:
                return _error_response(
                    "pyyaml not installed",
                    "missing_dependency",
                    ["uv add pyyaml or validate as text"],
                )
            try:
                data = yaml.safe_load(path_obj.read_text(encoding=encoding))
            except Exception as e:
                return _success_response({"path": str(path_obj), "valid": False, "error": str(e)})
            summary: dict[str, Any] = {"type": type(data).__name__}
            if isinstance(data, dict):
                summary["keys"] = sorted(map(str, data.keys()))[:50]
                summary["key_count"] = len(data)
            return _success_response({"path": str(path_obj), "valid": True, "summary": summary})
        if suffix == ".toml":
            try:
                import tomllib
            except ImportError:
                return _error_response("tomllib unavailable (needs Python 3.11+)", "missing_dependency")
            try:
                with path_obj.open("rb") as fh:
                    data = tomllib.load(fh)
            except Exception as e:
                return _success_response({"path": str(path_obj), "valid": False, "error": str(e)})
            summary = {"type": "dict", "keys": sorted(map(str, data.keys()))[:50], "key_count": len(data)}
            return _success_response({"path": str(path_obj), "valid": True, "summary": summary})
        if suffix == ".ini":
            import configparser

            parser = configparser.ConfigParser()
            try:
                parser.read(path_obj, encoding=encoding)
                sections = parser.sections()
            except Exception as e:
                return _success_response({"path": str(path_obj), "valid": False, "error": str(e)})
            return _success_response({"path": str(path_obj), "valid": True, "summary": {"sections": sections[:50]}})
        return _error_response(
            f"Unsupported config type: {suffix or '(no extension)'}",
            "invalid_arguments",
            ["Use .json, .yaml/.yml, .toml, or .ini"],
        )
    except UnicodeDecodeError as e:
        return _error_response(f"Cannot decode as {encoding}: {e!s}", "encoding_error")
    except Exception as e:
        return _error_response(f"Failed to validate config: {e!s}", "io_error")
