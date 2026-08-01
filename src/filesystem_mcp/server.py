"""
ASGI entry point for uvicorn (webapp backend).

Use: uvicorn filesystem_mcp.server:app --host 127.0.0.1 --port 10742
"""

from filesystem_mcp import http_app

app = http_app()
