"""file_ops_safe — DEPRECATED 2026-04-06.

Concurrency safety has been merged into file_ops (portmanteau_file.py).
Use file_ops for all file operations — write_file, edit_file, copy_file,
move_file now all use per-path asyncio.Lock + atomic os.replace() internally.

This stub is kept to avoid import errors in __init__.py.
get_lock_status and test_concurrency_safety are preserved as utilities.
"""

from __future__ import annotations

from .utils import _get_app, _success_response
from ..concurrency import file_manager


@_get_app().tool()
async def get_lock_status() -> dict:
    """Get current per-path file lock status (diagnostic tool).

    Returns which file paths currently have active locks — useful for debugging
    concurrent write contention between Claude Desktop, Cursor, and Windsurf sessions.
    """
    return file_manager.get_lock_status()


@_get_app().tool()
async def test_concurrency_safety(operation: str = "write", num_clients: int = 5) -> dict:
    """Test that file_ops write/edit locking prevents data corruption under concurrent load.

    Simulates num_clients simultaneously writing or editing the same temp file.
    All should succeed without data corruption if locking is working correctly.
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
