"""Server lifecycle tools: graceful shutdown.

Consolidates self-termination into a single tool with an explicit confirm
guard per fleet TOOL_DESIGN_STANDARDS (destructive ops require agent-visible
confirmation).
"""

import asyncio
import logging
import threading

from .utils import DESTRUCTIVE, _clarification_response, _get_app, _success_response

logger = logging.getLogger(__name__)


@_get_app().tool(annotations=DESTRUCTIVE, version="2.2.0")
async def server_shutdown(confirm: bool = False) -> dict:
    """Shut down the filesystem-mcp server process gracefully.

    Schedules an orderly exit after a short delay so in-flight responses can
    flush. Intended for the HTTP daemon; stdio instances exit when the parent
    closes the stream anyway.

    ## Return Format
    {"success": bool, "operation": "shutdown", "result": {"shutdown_in_seconds": int}}

    ## Examples
    server_shutdown(confirm=True)
    """
    if not confirm:
        return _clarification_response(
            ambiguities=["confirm"],
            options={"confirm": "Pass confirm=True to proceed."},
            suggested_questions=["Are you sure you want to shut down the server?"],
        )
    logger.warning("server_shutdown called with confirm=True — scheduling exit")

    def _exit() -> None:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.call_later(1.0, lambda: __import__("os")._exit(0))
            else:
                __import__("os")._exit(0)
        except Exception:
            __import__("os")._exit(0)

    threading.Thread(target=_exit, daemon=True).start()
    return _success_response(
        result={"shutdown_in_seconds": 1},
        operation="shutdown",
    )
