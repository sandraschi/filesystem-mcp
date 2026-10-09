"""PyInstaller entrypoint for filesystem-mcp HTTP sidecar."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    base = Path(sys._MEIPASS)
else:
    base = Path(__file__).resolve().parent
if str(base / "src") not in sys.path:
    sys.path.insert(0, str(base / "src"))

os.environ.setdefault("MCP_TRANSPORT", "http")

# Frozen-exe safety: stdlib C extensions + mcp bootstrap must be imported eagerly
# (hiddenimports alone is not enough). See TAURI_PRODUCTION_PITFALLS sec E.
import _datetime  # noqa: F401
import _strptime  # noqa: F401

import mcp.types  # noqa: F401

if __name__ == "__main__":
    import uvicorn

    from filesystem_mcp.server import app

    host = os.environ.get("FILESYSTEM_HOST", "127.0.0.1")
    port = int(os.environ.get("FILESYSTEM_PORT", os.environ.get("MCP_PORT", "10742")))
    log_level = os.environ.get("FILESYSTEM_LOG_LEVEL", "info")
    uvicorn.run(app, host=host, port=port, log_level=log_level)
