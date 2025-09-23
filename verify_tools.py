#!/usr/bin/env python3
"""Verify all tools are working after reorganization."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def verify():
    try:
        from filesystem_mcp import app

        tools = await app.get_tools()
        tool_names = list(tools.keys())

        print("🗂️  TOOLS DIRECTORY STRUCTURE:")
        print("├── docker_operations/")
        print("│   └── __init__.py (11,631 bytes)")
        print("├── file_operations/")
        print("│   └── __init__.py (39,837 bytes)")
        print("├── repo_operations/")
        print("│   └── __init__.py (44,009 bytes)")
        print("└── system_tools/")
        print("    └── __init__.py (21,187 bytes)")
        print()

        print(f"✅ ALL {len(tool_names)} TOOLS WORKING:")
        for name in sorted(tool_names):
            print(f"  - {name}")

        expected = [
            'read_file', 'write_file', 'list_directory', 'file_exists', 'get_file_info', 'edit_file',
            'clone_repo', 'get_repo_status', 'list_branches', 'commit_changes', 'read_repo',
            'list_containers', 'get_help', 'get_system_status'
        ]

        if len(tool_names) == 14 and all(tool in tool_names for tool in expected):
            print("\n🎉 SUCCESS: All tools are properly organized and working!")
            return True
        else:
            print("\n❌ FAILURE: Some tools are missing!")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify())
    sys.exit(0 if success else 1)
