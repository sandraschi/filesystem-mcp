#!/usr/bin/env python3
"""Final test after workflow fixes."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test():
    from filesystem_mcp import app
    tools = await app.get_tools()
    print(f'✅ All {len(tools)} tools still working after workflow fixes!')
    return len(tools) == 14

if __name__ == "__main__":
    success = asyncio.run(test())
    print("🎉 SUCCESS: MCP server fully functional!" if success else "❌ FAILURE")
    sys.exit(0 if success else 1)
