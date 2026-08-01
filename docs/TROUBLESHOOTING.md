# Troubleshooting

## Backend won't start / port 10742 in use

```powershell
Get-NetTCPConnection -LocalPort 10742 -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
webapp\start.ps1
```

Check `logs/filesystem_mcp.log` for import errors. The server kills orphaned
stdio processes on startup but never touches the HTTP daemon on 10742.

## Webapp shows "Backend offline"

1. Is `uvicorn filesystem_mcp.server:app --port 10742` running? `webapp\start.ps1` starts it.
2. Test `GET http://127.0.0.1:10742/api/health` — must return 200.
3. In the Tauri app use the **Restart Backend** button in the top bar.
4. Check CORS: the frontend connects cross-origin to 10742; the MCP HTTP app
   carries fleet-standard CORS middleware (tauri origins + LAN + Tailscale).

## Tool call fails with "No operation specified"

A portmanteau call omitted `operation`. The error lists valid values.

## edit_file made zero replacements

The `old_string` did not match exactly. Enable `ignore_whitespace=True`
(indentation drift), `is_regex=True`, or re-read the file to copy exact content.

## Docker tools return docker_error

Daemon unreachable: start Docker Desktop / `Start-Service docker`, wait, retry.
Compose errors name the exact command to inspect (`docker compose config`).

## Chat returns "LLM Error"

Provider down or model missing: open Settings, verify the provider badge is
green, refresh the model list, save. The bridge proxy is `POST /api/llm/chat`.

## Concurrency concerns

Run `test_concurrency_safety(operation="write", num_clients=8)` to verify the
lock layer; `get_lock_status()` shows current locks. Locks are in-memory and
clear on restart.

## Frozen backend (Tauri) crashes on launch

Build the sidecar standalone and run it: `dist/filesystem-mcp-backend.exe` with
`FILESYSTEM_PORT=11999` — check the crash log. The spec file `filesystem-mcp-backend.spec`
uses `noarchive=True` (mandatory) and a dist-info preserve list; heavy deps are
skipped via the SKIP list.

## Git / remotes

Remote is `https://github.com/sandraschi/filesystem-mcp` (origin). Branch: `main`.

## Related Docs

- [TROUBLESHOOTING_FASTMCP_2.12.md](TROUBLESHOOTING_FASTMCP_2.12.md) — FastMCP-specific issues
- [CLAUDE_DESKTOP_DEBUGGING.md](CLAUDE_DESKTOP_DEBUGGING.md) — IDE client issues
- [DEBUGGING_LESSONS_LEARNED.md](DEBUGGING_LESSONS_LEARNED.md) — incident log
- [MCP_PRODUCTION_CHECKLIST.md](MCP_PRODUCTION_CHECKLIST.md) — release audit
