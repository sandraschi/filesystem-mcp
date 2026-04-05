"""
Concurrency-safe file operations for FileSystem-MCP with FastMCP 3.2+ support.

Provides atomic file operations with proper per-path asyncio.Lock() to prevent
corruption when multiple clients access the same files simultaneously.

Design notes:
- One asyncio.Lock per canonical file path, created lazily in a dict.
- modify_file_safe writes back via os.replace() directly rather than calling
  write_file_atomic, avoiding a deadlock (lock is not reentrant).
- All blocking I/O (os.replace, shutil) is run in asyncio.to_thread() so the
  event loop is never blocked.
"""

import asyncio
import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import aiofiles
import structlog

logger = structlog.get_logger(__name__)


class FileOperationError(Exception):
    """Raised when file operations fail due to concurrency or I/O issues."""
    pass


class ConcurrencySafeFileManager:
    """
    Manages file/directory operations with per-path asyncio.Lock() concurrency safety.

    Each canonical path gets exactly one Lock, created on first access and kept for
    the lifetime of the process.  Lock acquisition never busy-loops — asyncio handles
    the wait queue internally.
    """

    def __init__(self) -> None:
        self._file_locks: Dict[str, asyncio.Lock] = {}
        self._dir_locks: Dict[str, asyncio.Lock] = {}
        self._meta_lock = asyncio.Lock()   # guards the dicts themselves

    # ── Lock accessors ────────────────────────────────────────────────────────

    async def _get_file_lock(self, path: str) -> asyncio.Lock:
        key = str(Path(path).resolve())
        async with self._meta_lock:
            if key not in self._file_locks:
                self._file_locks[key] = asyncio.Lock()
            return self._file_locks[key]

    async def _get_dir_lock(self, path: str) -> asyncio.Lock:
        key = f"dir:{Path(path).resolve()}"
        async with self._meta_lock:
            if key not in self._dir_locks:
                self._dir_locks[key] = asyncio.Lock()
            return self._dir_locks[key]

    # ── Internal atomic write (no lock — callers hold the lock already) ───────

    async def _write_atomic_unlocked(self, file_path: str, content: str, create_parents: bool) -> None:
        """
        Write content to file_path atomically via a temp file + os.replace().
        Caller must already hold the file lock for file_path.
        Never blocks the event loop.
        """
        path = Path(file_path)
        if create_parents:
            await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)

        tmp_path = str(path.parent / f".tmp.{uuid.uuid4().hex}")
        try:
            async with aiofiles.open(tmp_path, "w", encoding="utf-8") as f:
                await f.write(content)
            # os.replace is atomic on Windows (same drive) and POSIX
            await asyncio.to_thread(os.replace, tmp_path, file_path)
        except Exception as exc:
            # Best-effort cleanup
            try:
                await asyncio.to_thread(os.unlink, tmp_path)
            except OSError:
                pass
            raise FileOperationError(f"Atomic write failed for {file_path}: {exc}") from exc

    # ── Public API ────────────────────────────────────────────────────────────

    async def write_file_atomic(
        self, file_path: str, content: str, create_parents: bool = False
    ) -> dict:
        lock = await self._get_file_lock(file_path)
        async with lock:
            await self._write_atomic_unlocked(file_path, content, create_parents)
        return {
            "success": True,
            "path": file_path,
            "bytes_written": len(content.encode("utf-8")),
            "atomic": True,
            "concurrency_safe": True,
        }

    async def modify_file_safe(
        self, file_path: str, modifications: List[dict]
    ) -> dict:
        """
        Read → apply modifications → write back atomically.
        Does NOT call write_file_atomic to avoid re-acquiring the lock (deadlock).
        """
        lock = await self._get_file_lock(file_path)
        async with lock:
            try:
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    content = await f.read()
            except FileNotFoundError:
                raise FileOperationError(f"File not found: {file_path}")

            modified = content
            changes = 0
            for mod in modifications:
                search = mod.get("search", "")
                replace = mod.get("replace", "")
                if not search:
                    continue
                opts = mod.get("options", {})
                if search in modified:
                    if opts.get("global", False):
                        count = modified.count(search)
                        modified = modified.replace(search, replace)
                        changes += count
                    else:
                        modified = modified.replace(search, replace, 1)
                        changes += 1
                else:
                    logger.warning("modify_file_safe: text not found",
                                   path=file_path, search=search[:60])

            if changes > 0:
                # Write directly — lock already held, don't call write_file_atomic
                await self._write_atomic_unlocked(file_path, modified, create_parents=False)

        return {
            "success": True,
            "path": file_path,
            "changes_made": changes,
            "modifications_applied": len(modifications),
            "concurrency_safe": True,
        }

    async def delete_file_safe(self, file_path: str) -> dict:
        lock = await self._get_file_lock(file_path)
        async with lock:
            try:
                await asyncio.to_thread(os.unlink, file_path)
                deleted = True
            except FileNotFoundError:
                deleted = False
            except OSError as exc:
                raise FileOperationError(f"Delete failed for {file_path}: {exc}") from exc
        return {"success": True, "path": file_path, "deleted": deleted, "concurrency_safe": True}

    async def copy_file_safe(
        self, src_path: str, dst_path: str, create_parents: bool = False
    ) -> dict:
        # Acquire both locks in canonical order to avoid cross-lock deadlock
        src_key = str(Path(src_path).resolve())
        dst_key = str(Path(dst_path).resolve())
        locks = sorted(
            [await self._get_file_lock(src_path), await self._get_file_lock(dst_path)],
            key=id,
        )
        async with locks[0]:
            async with locks[1]:
                if create_parents:
                    await asyncio.to_thread(Path(dst_path).parent.mkdir,
                                            parents=True, exist_ok=True)
                try:
                    await asyncio.to_thread(shutil.copy2, src_path, dst_path)
                except OSError as exc:
                    raise FileOperationError(
                        f"Copy failed {src_path} → {dst_path}: {exc}"
                    ) from exc
        return {
            "success": True, "source": src_path, "destination": dst_path,
            "copied": True, "concurrency_safe": True,
        }

    async def move_file_safe(
        self, src_path: str, dst_path: str, create_parents: bool = False
    ) -> dict:
        locks = sorted(
            [await self._get_file_lock(src_path), await self._get_file_lock(dst_path)],
            key=id,
        )
        async with locks[0]:
            async with locks[1]:
                if create_parents:
                    await asyncio.to_thread(Path(dst_path).parent.mkdir,
                                            parents=True, exist_ok=True)
                try:
                    await asyncio.to_thread(os.replace, src_path, dst_path)
                except OSError as exc:
                    raise FileOperationError(
                        f"Move failed {src_path} → {dst_path}: {exc}"
                    ) from exc
        return {
            "success": True, "source": src_path, "destination": dst_path,
            "moved": True, "concurrency_safe": True,
        }

    async def create_directory_safe(self, dir_path: str, parents: bool = True) -> dict:
        lock = await self._get_dir_lock(dir_path)
        async with lock:
            try:
                await asyncio.to_thread(Path(dir_path).mkdir, parents=parents, exist_ok=True)
            except OSError as exc:
                raise FileOperationError(
                    f"Directory creation failed for {dir_path}: {exc}"
                ) from exc
        return {"success": True, "path": dir_path, "created": True,
                "parents": parents, "concurrency_safe": True}

    async def delete_directory_safe(self, dir_path: str, recursive: bool = False) -> dict:
        lock = await self._get_dir_lock(dir_path)
        async with lock:
            if not os.path.exists(dir_path):
                return {"success": True, "path": dir_path, "deleted": False,
                        "concurrency_safe": True}
            try:
                if recursive:
                    await asyncio.to_thread(shutil.rmtree, dir_path)
                else:
                    await asyncio.to_thread(os.rmdir, dir_path)
            except OSError as exc:
                raise FileOperationError(
                    f"Directory deletion failed for {dir_path}: {exc}"
                ) from exc
        return {"success": True, "path": dir_path, "deleted": True,
                "recursive": recursive, "concurrency_safe": True}

    def get_lock_status(self) -> dict:
        """Return current lock state for debugging."""
        return {
            "file_locks": {
                k: {"locked": v.locked()} for k, v in self._file_locks.items()
            },
            "dir_locks": {
                k: {"locked": v.locked()} for k, v in self._dir_locks.items()
            },
            "total_file_locks": len(self._file_locks),
            "total_dir_locks": len(self._dir_locks),
        }


# Global singleton — shared across all tool handlers in this process
file_manager = ConcurrencySafeFileManager()
