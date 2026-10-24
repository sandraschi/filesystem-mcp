"""P1 coverage: file_ops hash/append/touch, dir_ops copy_tree, search_ops dev ops."""

import json

import pytest

from filesystem_mcp.tools.portmanteau_directory import dir_ops
from filesystem_mcp.tools.portmanteau_file import file_ops
from filesystem_mcp.tools.portmanteau_search import search_ops


@pytest.mark.asyncio
async def test_touch_append_hash_roundtrip(tmp_path):
    p = tmp_path / "note.txt"
    r = await file_ops(operation="touch_file", path=str(p))
    assert r["success"] is True and r["result"]["created"] is True
    r = await file_ops(operation="append_file", path=str(p), content="hello")
    assert r["success"] is True
    r = await file_ops(operation="append_file", path=str(p), content="world")
    assert r["success"] is True
    assert p.read_text() == "hello\nworld"
    r = await file_ops(operation="get_file_hash", path=str(p), hash_algorithm="sha256")
    assert r["success"] is True and len(r["result"]["hash"]) == 64
    r = await file_ops(operation="touch_file", path=str(p))
    assert r["success"] is True and r["result"]["created"] is False


@pytest.mark.asyncio
async def test_copy_tree_shutil(tmp_path):
    src = tmp_path / "src"
    (src / "sub").mkdir(parents=True)
    (src / "a.txt").write_text("hi")
    (src / "sub" / "b.txt").write_text("yo")
    dst = tmp_path / "dst"
    dry = await dir_ops(operation="copy_tree", path=str(src), destination_path=str(dst), dry_run=True)
    assert dry["success"] is True and dry["result"]["file_count"] == 2
    assert not dst.exists()
    real = await dir_ops(operation="copy_tree", path=str(src), destination_path=str(dst))
    assert real["success"] is True and (dst / "a.txt").read_text() == "hi"
    err = await dir_ops(operation="copy_tree", path=str(src), destination_path=str(dst))
    assert err["success"] is False and err["error_type"] == "already_exists"
    ok = await dir_ops(operation="copy_tree", path=str(src), destination_path=str(dst), overwrite=True)
    assert ok["success"] is True
    guard = await dir_ops(operation="copy_tree", path=str(src), destination_path=str(src / "inner"))
    assert guard["success"] is False
    mirror_guard = await dir_ops(
        operation="copy_tree", path=str(src), destination_path=str(tmp_path / "d2"), mirror=True
    )
    assert mirror_guard["success"] is False


@pytest.mark.asyncio
async def test_find_todos_and_symbols(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text("# TODO: fix this\ndef my_handler():\n    pass\nclass MyService:\n    pass\n")
    todos = await search_ops(operation="find_todos", path=str(tmp_path), recursive=True)
    assert todos["success"] is True and todos["result"]["total_matches"] >= 1
    syms = await search_ops(
        operation="find_symbols", path=str(f), search_pattern="my_handler"
    )
    assert syms["success"] is True
    names = [s["name"] for s in syms["result"]["symbols"]]
    assert "my_handler" in names


@pytest.mark.asyncio
async def test_validate_json(tmp_path):
    good = tmp_path / "good.json"
    good.write_text(json.dumps({"a": 1}))
    bad = tmp_path / "bad.json"
    bad.write_text("{nope")
    r = await search_ops(operation="validate_json", path=str(good))
    assert r["success"] is True and r["result"]["valid"] is True
    r = await search_ops(operation="validate_json", path=str(bad))
    assert r["success"] is True and r["result"]["valid"] is False
