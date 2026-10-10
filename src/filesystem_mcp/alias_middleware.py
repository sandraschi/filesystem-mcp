"""Alias-normalization middleware for filesystem-mcp tool calls.

LLM clients constantly send camelCase arguments (newString, oldString,
containerId, ...) to snake_case tools. FastMCP validates arguments strictly,
so the call dies with a validation error before the tool ever runs.

This middleware remaps misnamed keys to the tool's real parameter names
*before* validation, using each tool's own JSON Schema as ground truth:

- ``newString`` -> ``new_string`` (only if the tool actually has that param)
- keys that already match are never touched
- keys with no valid snake_case target pass through untouched, so genuine
  typos are still rejected by validation instead of silently rewritten

Covers every registered tool (portmanteau + atomic), stdio and HTTP, with
zero per-tool code.
"""

import logging
import re
from typing import Any

from fastmcp.server.middleware import Middleware, MiddlewareContext
from mcp.types import CallToolRequestParams

logger = logging.getLogger(__name__)

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


def to_snake_case(name: str) -> str:
    """Convert camelCase/PascalCase to snake_case. snake_case passes through."""
    return _CAMEL_BOUNDARY.sub("_", name).lower()


def remap_arguments(args: dict[str, Any], valid_params: set[str] | None) -> dict[str, str]:
    """Compute old->new key remaps for one tool call.

    A key is remapped only when it is not itself valid, its snake_case form
    is valid, and the snake_case form was not also supplied (explicit wins).
    Without ground truth (valid_params None) nothing is remapped: a proxied
    tool may legitimately own a camelCase parameter. Returns an empty dict
    when nothing should change.
    """
    remapped: dict[str, str] = {}
    if valid_params is None:
        return remapped
    for key in args:
        if key in valid_params:
            continue
        snake = to_snake_case(key)
        if snake == key:
            continue
        if snake in args:
            continue
        if snake not in valid_params:
            continue
        remapped[key] = snake
    return remapped


class AliasNormalizationMiddleware(Middleware):
    """Rewrite camelCase tool arguments to snake_case before validation."""

    def __init__(self) -> None:
        # Tool name -> frozenset of valid parameter names. Tools are static
        # after startup; misses are never cached so dynamic (proxied) tools
        # are re-resolved on every call until known.
        self._param_cache: dict[str, frozenset[str]] = {}

    async def _valid_params(self, fastmcp: Any, tool_name: str) -> set[str] | None:
        cached = self._param_cache.get(tool_name)
        if cached is not None:
            return set(cached)
        try:
            tool = await fastmcp.get_tool(tool_name)
        except Exception as e:
            # Unknown tool or lookup failure: leave args alone, validation
            # (or the unknown-tool error) will fail loud downstream.
            logger.debug(f"alias-middleware: tool lookup failed for {tool_name}: {e}")
            return None
        properties = (getattr(tool, "parameters", None) or {}).get("properties", {})
        valid = frozenset(properties)
        self._param_cache[tool_name] = valid
        return set(valid)

    async def on_call_tool(
        self,
        context: MiddlewareContext[CallToolRequestParams],
        call_next: Any,
    ) -> Any:
        message = context.message
        args = message.arguments
        if isinstance(args, dict) and args:
            fastmcp = getattr(getattr(context, "fastmcp_context", None), "fastmcp", None)
            if fastmcp is not None:
                valid = await self._valid_params(fastmcp, message.name)
                remapped = remap_arguments(args, valid)
                for old_key, new_key in remapped.items():
                    args[new_key] = args.pop(old_key)
                if remapped:
                    logger.info(f"alias-middleware: {message.name} remapped {remapped}")
        return await call_next(context)
