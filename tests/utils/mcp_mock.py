"""
Mock implementation of the MCP module for testing.

This provides a simplified version of the MCP module that can be used for testing
without requiring the actual FastMCP 2.10 package.
"""

from functools import wraps
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")

from typing import TypeVar

T = TypeVar("T")


class Application:
    """Mock Application class for testing with FastAPI-like functionality."""

    def __init__(self, name: str):
        self.name = name
        self._tools: dict[str, Callable] = {}
        self._routes: dict[str, dict[str, Callable]] = {}

    def tool(self, func: Optional[Callable] = None, **kwargs) -> Callable:
        """Mock decorator to register a tool."""
        if func is None:
            return lambda f: self.tool(f, **kwargs)

        self._tools[func.__name__] = func

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    def get(self, path: str, **kwargs):
        """Mock FastAPI route decorator for GET requests."""

        def decorator(func: Callable):
            if path not in self._routes:
                self._routes[path] = {}
            self._routes[path]["GET"] = func
            return func

        return decorator

    def post(self, path: str, **kwargs):
        """Mock FastAPI route decorator for POST requests."""

        def decorator(func: Callable):
            if path not in self._routes:
                self._routes[path] = {}
            self._routes[path]["POST"] = func
            return func

        return decorator

    async def __call__(self, scope, receive, send):
        """Mock ASGI callable for testing."""
        # This is a simplified version for testing
        path = scope["path"]
        method = scope["method"]

        if path in self._routes and method in self._routes[path]:
            handler = self._routes[path][method]
            response = handler()
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"application/json"]],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": str(response).encode("utf-8"),
                }
            )
        else:
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [[b"content-type", b"application/json"]],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"detail":"Not Found"}',
                }
            )

    def list_tools(self) -> dict[str, dict[str, Any]]:
        """List all registered tools."""
        return {
            name: {"name": name, "description": func.__doc__ or "", "parameters": {}}
            for name, func in self._tools.items()
        }

    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a tool by name."""
        return self._tools.get(name)


# Create a mock application instance
app = Application("filesystem-mcp")


def tool(func: Optional[Callable] = None, **kwargs) -> Callable:
    """Mock tool decorator for testing."""
    return app.tool(func, **kwargs)
