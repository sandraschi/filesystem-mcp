"""Unit tests for the edit_file replace_all flag (alias of allow_multiple)."""

import asyncio

from filesystem_mcp.tools.portmanteau_file import file_ops


def _write(tmp_path, text):
    target = tmp_path / "edit_me.txt"
    target.write_text(text, encoding="utf-8")
    return target


def test_replace_all_replaces_every_occurrence(tmp_path):
    target = _write(tmp_path, "foo foo foo")
    res = asyncio.run(
        file_ops(operation="edit_file", path=str(target), old_string="foo", new_string="bar", replace_all=True)
    )
    assert res["success"] is True
    assert target.read_text(encoding="utf-8") == "bar bar bar"


def test_default_replaces_first_only(tmp_path):
    target = _write(tmp_path, "foo foo foo")
    res = asyncio.run(file_ops(operation="edit_file", path=str(target), old_string="foo", new_string="bar"))
    assert res["success"] is True
    assert target.read_text(encoding="utf-8") == "bar foo foo"


def test_allow_multiple_still_works(tmp_path):
    target = _write(tmp_path, "foo foo foo")
    res = asyncio.run(
        file_ops(operation="edit_file", path=str(target), old_string="foo", new_string="bar", allow_multiple=True)
    )
    assert res["success"] is True
    assert target.read_text(encoding="utf-8") == "bar bar bar"


def test_replace_all_no_match_is_error(tmp_path):
    target = _write(tmp_path, "hello world")
    res = asyncio.run(
        file_ops(operation="edit_file", path=str(target), old_string="missing", new_string="x", replace_all=True)
    )
    assert res["success"] is False
    assert target.read_text(encoding="utf-8") == "hello world"


def test_camel_case_replace_all_via_client(tmp_path):
    """replaceAll (camelCase) works end-to-end: alias flag + alias middleware."""
    from fastmcp import Client

    from filesystem_mcp import app

    target = _write(tmp_path, "aaa aaa")

    async def run():
        async with Client(app) as client:
            return await client.call_tool(
                "file_ops",
                {
                    "operation": "edit_file",
                    "path": str(target),
                    "oldString": "aaa",
                    "newString": "b",
                    "replaceAll": True,
                },
            )

    asyncio.run(run())
    assert target.read_text(encoding="utf-8") == "b b"
