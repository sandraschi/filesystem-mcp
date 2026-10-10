"""Unit + end-to-end tests for alias-normalization middleware.

LLM clients send camelCase arguments (newString, destinationPath, ...) to
snake_case tools. The middleware remaps them before FastMCP validation
using each tool's own JSON Schema as ground truth.
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from mcp.types import CallToolRequestParams

from filesystem_mcp.alias_middleware import (
    AliasNormalizationMiddleware,
    remap_arguments,
    to_snake_case,
)


def test_to_snake_case():
    assert to_snake_case("newString") == "new_string"
    assert to_snake_case("oldString") == "old_string"
    assert to_snake_case("destinationPath") == "destination_path"
    assert to_snake_case("maxResults") == "max_results"
    assert to_snake_case("snake_case") == "snake_case"
    assert to_snake_case("path") == "path"
    assert to_snake_case("already_snake_case") == "already_snake_case"


def test_remap_camel_to_snake():
    valid = {"operation", "path", "old_string", "new_string"}
    remapped = remap_arguments(
        {"operation": "edit_file", "path": "a", "oldString": "x", "newString": "y"},
        valid,
    )
    assert remapped == {"oldString": "old_string", "newString": "new_string"}


def test_remap_leaves_valid_keys_alone():
    valid = {"operation", "path", "old_string"}
    assert remap_arguments({"operation": "x", "path": "y", "old_string": "z"}, valid) == {}


def test_remap_explicit_canonical_wins():
    valid = {"old_string"}
    args = {"old_string": "keep", "oldString": "drop"}
    assert remap_arguments(args, valid) == {}


def test_remap_unknown_target_passes_through():
    # No valid snake target: genuine typo must still fail validation downstream.
    valid = {"operation", "path"}
    assert remap_arguments({"operation": "x", "nweString": "y"}, valid) == {}


def test_remap_without_ground_truth_passes_through():
    assert remap_arguments({"newString": "y"}, None) == {}


def _stub_context(tool_name, args, properties):
    message = CallToolRequestParams(name=tool_name, arguments=dict(args))
    tool = SimpleNamespace(parameters={"properties": properties})
    fastmcp = SimpleNamespace(get_tool=AsyncMock(return_value=tool))
    return SimpleNamespace(message=message, fastmcp_context=SimpleNamespace(fastmcp=fastmcp))


def test_middleware_rewrites_before_handler():
    mw = AliasNormalizationMiddleware()
    ctx = _stub_context(
        "file_ops",
        {"operation": "edit_file", "path": "a", "oldString": "x", "newString": "y"},
        {"operation": {}, "path": {}, "old_string": {}, "new_string": {}},
    )
    seen = {}

    async def call_next(c):
        seen.update(c.message.arguments)
        return {"ok": True}

    async def run():
        return await mw.on_call_tool(ctx, call_next)

    result = asyncio.run(run())
    assert result == {"ok": True}
    assert seen == {"operation": "edit_file", "path": "a", "old_string": "x", "new_string": "y"}


def test_middleware_caches_tool_schema():
    mw = AliasNormalizationMiddleware()
    props = {"path": {}}
    ctx = _stub_context("dir_ops", {"path": "a"}, props)

    async def run_one(c):
        return await mw.on_call_tool(c, AsyncMock(return_value={}))

    asyncio.run(run_one(ctx))
    get_tool = ctx.fastmcp_context.fastmcp.get_tool
    assert get_tool.await_count == 1
    ctx2 = _stub_context("dir_ops", {"path": "b"}, props)
    ctx2.fastmcp_context.fastmcp.get_tool = get_tool
    # Share the middleware cache: second call must not re-fetch.
    cached_calls = get_tool.await_count
    asyncio.run(run_one(ctx2))
    assert get_tool.await_count == cached_calls  # cache hit, no new fetch


def test_end_to_end_camel_case_edit(tmp_path):
    """The exact failure from the field: oldString/newString via real stack."""
    from fastmcp import Client

    from filesystem_mcp import app

    target = tmp_path / "edit_me.txt"
    target.write_text("fooBARbaz", encoding="utf-8")

    async def run():
        async with Client(app) as client:
            # Control: canonical snake_case still works.
            res = await client.call_tool(
                "file_ops",
                {"operation": "read_file", "path": str(target)},
            )
            assert "fooBARbaz" in str(res.content)

            # camelCase previously died in validation before the tool ever ran.
            await client.call_tool(
                "file_ops",
                {
                    "operation": "edit_file",
                    "path": str(target),
                    "oldString": "BAR",
                    "newString": "QUX",
                },
            )

    asyncio.run(run())
    assert "QUX" in target.read_text(encoding="utf-8")


def test_end_to_end_garbage_key_still_rejected(tmp_path):
    """Pass-through safety: genuine typos must still fail, not misroute."""
    from fastmcp import Client
    from fastmcp.exceptions import ToolError

    from filesystem_mcp import app

    target = tmp_path / "edit_me.txt"
    target.write_text("hello", encoding="utf-8")

    async def run():
        async with Client(app) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "file_ops",
                    {"operation": "read_file", "path": str(target), "nweString": "x"},
                )

    asyncio.run(run())
