# filesystem-mcp — Agent Guide

## Overview
FastMCP 3.2+ server for file system, Docker, system monitoring, and host context operations.

## Tools
23 tools across 10 modules. Portmanteau tools use an `operation` enum parameter.

| Tool | Category | Mutates |
|------|----------|---------|
| `file_ops` | File read/write/edit/delete/move/copy | Yes |
| `dir_ops` | Directory list/create/remove | Some |
| `search_ops` | Grep, search, compare, find duplicates | No |
| `container_ops` | Docker container lifecycle | Yes |
| `infra_ops` | Docker images, networks, volumes | Yes |
| `compose_up/down/ps/logs/config/restart` | Docker Compose | Some |
| `monitor_get_*` (8 tools) | System metrics | No |
| `host_ops` | Host info and environment | No |
| `agentic_file_workflow` | LLM sampling-based file ops | Yes |
| `get_lock_status` | Concurrency lock diagnostics | No |

## Ports
- Backend: 10742
- Frontend: 10743

## Key Standards
- Concurrency-safe writes: per-path `asyncio.Lock` + atomic `os.replace()`
- Structured responses: `_success_response`, `_error_response`, `_clarification_response`
- Dual transport: stdio (Claude Desktop) + HTTP (webapp)

Install docs: follow mcp-central-docs/standards/AGENT_INSTALL_REFERENCE.md
