import os
import sys
import asyncio
from pathlib import Path

# Add the src directory to sys.path to import the portmanteau_file module
sys.path.append(str(Path("D:/Dev/repos/filesystem-mcp/src")))

from filesystem_mcp.tools.portmanteau_file import _edit_file, _undo_edit


async def run_tests():
    test_file = Path("D:/Dev/repos/filesystem-mcp/test_edit.txt")

    # Setup initial file
    content = """
    Line 1: Item A
    Line 2: Item B
    Line 3: Item A
    Indented    Line 4
    """
    test_file.write_text(content.strip())
    print(f"Created test file: {test_file}")

    try:
        # Test 1: Multiple replacements (allow_multiple=True)
        print("\nTest 1: Replacing all 'Item A' with 'Item X'")
        res = await _edit_file(
            file_path=str(test_file),
            old_string="Item A",
            new_string="Item X",
            allow_multiple=True,
        )
        print(
            f"Result: {res['success']}, replaced: {res['result']['total_occurrences_replaced']}"
        )
        print(f"Content:\n{test_file.read_text()}")

        # Test 2: Regex replacement
        print("\nTest 2: Regex replacing 'Item [B]' with 'Item Beta'")
        res = await _edit_file(
            file_path=str(test_file),
            old_string="Item B",
            new_string="Item Beta",
            is_regex=True,
        )
        print(f"Result: {res['success']}")
        print(f"Content:\n{test_file.read_text()}")

        # Test 3: Indentation agnostic matching
        print("\nTest 3: Indentation agnostic matching 'Indented Line 4'")
        res = await _edit_file(
            file_path=str(test_file),
            old_string="Indented Line 4",
            new_string="Modified Line 4",
            ignore_whitespace=True,
        )
        print(f"Result: {res['success']}")
        print(f"Content:\n{test_file.read_text()}")

        # Test 4: Batch replacements
        print("\nTest 4: Batch replacements")
        res = await _edit_file(
            file_path=str(test_file),
            old_string=None,
            new_string=None,
            replacements=[
                {"old_string": "Item X", "new_string": "Final A"},
                {"old_string": "Item Beta", "new_string": "Final B"},
            ],
        )
        print(
            f"Result: {res['success']}, total replaced: {res['result']['total_occurrences_replaced']}"
        )
        print(f"Content:\n{test_file.read_text()}")

        # Test 5: Undo most recent edit
        print("\nTest 5: Reverting last edit (Batch) via undo_edit")
        res = await _undo_edit(file_path=str(test_file))
        print(
            f"Result: {res['success']}, restored from: {res['result']['restored_from']}"
        )
        print(f"Content:\n{test_file.read_text()}")

    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
        for bak in Path("D:/Dev/repos/filesystem-mcp").glob("test_edit_*.bak"):
            bak.unlink()
        print("\nCleanup complete.")


if __name__ == "__main__":
    asyncio.run(run_tests())
