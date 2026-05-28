# filesystem-mcp — Claude Code Guide

## Overview
FastMCP 3.2.0+ compliant MCP server for comprehensive file system, Git, and Docker operations with concurrency safety

## Entry Points
- `uv run filesystem-mcp` → `filesystem_mcp.__main__:run`

## Standards
- FastMCP 3.2+ portmanteau tool pattern — tools use `operation` enum param
- Responses: structured dicts with `success`, `message`, domain-specific fields
- Dual transport: stdio (Claude Desktop) + HTTP (`MCP_TRANSPORT=http`)
- See [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs) for fleet-wide coding standards

## Key Files
- `README.md` — full documentation
- `pyproject.toml` — build config and entry points
- `AGENTS.md` — OpenAI Codex agent context (if present)
