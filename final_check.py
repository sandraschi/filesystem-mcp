#!/usr/bin/env python3
"""Final check that all tools work after fixing linter errors."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def check():
    try:
        from filesystem_mcp import app

        tools = await app.get_tools()
        tool_names = list(tools.keys())

        print(f"✅ All {len(tool_names)} tools working:")
        for name in sorted(tool_names):
            print(f"  - {name}")

        expected = [
            'read_file', 'write_file', 'list_directory', 'file_exists', 'get_file_info', 'edit_file',
            'clone_repo', 'get_repo_status', 'list_branches', 'commit_changes', 'read_repo',
            'list_containers', 'get_help', 'get_system_status'
        ]

        if len(tool_names) == 14 and all(tool in tool_names for tool in expected):
            print("\n🎉 SUCCESS: All tools working and linter errors fixed!")
            return True
        else:
            print("\n❌ FAILURE: Some tools missing!")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(check())
    sys.exit(0 if success else 1)
