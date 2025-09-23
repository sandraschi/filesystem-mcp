#!/usr/bin/env python3
"""Test script to verify MCP server functionality."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_server():
    """Test the MCP server initialization and tool registration."""
    try:
        from filesystem_mcp import app

        print("✅ Server initialized successfully")

        # Get registered tools
        tools = await app.get_tools()
        tool_names = list(tools.keys())

        print(f"✅ Registered tools ({len(tool_names)}): {tool_names}")

        # Check for expected tools
        expected_tools = [
            'read_file', 'write_file', 'list_directory', 'file_exists', 'get_file_info', 'edit_file',
            'clone_repo', 'get_repo_status', 'list_branches', 'commit_changes', 'read_repo',
            'list_containers',
            'get_help', 'get_system_status'
        ]

        missing_tools = [tool for tool in expected_tools if tool not in tool_names]
        extra_tools = [tool for tool in tool_names if tool not in expected_tools]

        if missing_tools:
            print(f"⚠️  Missing expected tools: {missing_tools}")
        else:
            print("✅ All expected tools are registered")

        if extra_tools:
            print(f"ℹ️  Additional tools found: {extra_tools}")

        print("🎉 MCP server test completed successfully!")

    except Exception as e:
        print(f"❌ Server test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(test_server())
    sys.exit(0 if success else 1)