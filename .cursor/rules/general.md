# Filesystem MCP - General Rules

## Rule #1: Check Central Documentation First

**BEFORE making any changes, ALWAYS check:**
- **Central Docs:** `D:\Dev\repos\mcp-central-docs\`
- **Standards:** `mcp-central-docs/STANDARDS.md`
- **FastMCP Guide:** `mcp-central-docs/FASTMCP_2.13_MIGRATION.md`

## Rule #2: Shell Context for Multi-Workspace

When switching to work on this repo in a multi-workspace setup:
1. Start a fresh shell (don't reuse terminals from other repos)
2. Always `cd D:\Dev\repos\filesystem-mcp` as the first command
3. Verify `Get-Location` shows correct directory before running other commands

## Rule #3: PowerShell Only (Windows)

**NEVER use Linux syntax:**
- ❌ `&&`, `||`, `ls`, `cat`, `grep`, `rm -rf`
- ✅ Use PowerShell: `Get-ChildItem`, `Get-Content`, `Select-String`, `Remove-Item -Recurse -Force`

## Rule #4: FastMCP Standards

- **NEVER** use `description=` parameter in `@mcp.tool()`
- **ALWAYS** use comprehensive docstrings (50+ lines minimum)
- **ALWAYS** include: Args, Returns, Examples, Notes sections

