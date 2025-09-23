#!/usr/bin/env python3
"""Test script to verify tools organization works."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test():
    from filesystem_mcp import app

    tools = await app.get_tools()
    tool_names = list(tools.keys())

    print(f'✅ All {len(tool_names)} tools registered:')
    for name in sorted(tool_names):
        print(f'  - {name}')

    expected_tools = [
        'read_file', 'write_file', 'list_directory', 'file_exists', 'get_file_info', 'edit_file',
        'clone_repo', 'get_repo_status', 'list_branches', 'commit_changes', 'read_repo',
        'list_containers',
        'get_help', 'get_system_status'
    ]

    if len(tool_names) == len(expected_tools) and all(tool in tool_names for tool in expected_tools):
        print("🎉 SUCCESS: All expected tools are properly registered!")
        return True
    else:
        print("❌ FAILURE: Missing tools detected")
        return False

if __name__ == "__main__":
    success = asyncio.run(test())
    sys.exit(0 if success else 1)
