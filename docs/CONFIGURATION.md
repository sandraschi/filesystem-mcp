# Configuration

Filesystem MCP is configured through environment variables, the `.env` file
(copy `.env.example` at the repo root), and the webapp Settings page.

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio`, `http`, or `sse` (deprecated). |
| `MCP_HOST` | `127.0.0.1` | Bind address for HTTP/SSE mode. |
| `MCP_PORT` | `10742` | HTTP port. Fleet-registered; do not change without updating the registry. |
| `MCP_PATH` | `/mcp` | MCP endpoint path in HTTP mode. |
| `MCP_BRIDGE_URLS` | (empty) | Comma-separated remote MCP URLs to register as providers. |
| `DOCKER_ENABLED` | (auto) | Set `false` to skip Docker tool registration. |
| `FILESYSTEM_PORT` | `10742` | Used by the Tauri wrapper when spawning the embedded backend. |
| `FILESYSTEM_HOST` | `127.0.0.1` | Used by the Tauri wrapper. |
| `FILESYSTEM_LOG_LEVEL` | `info` | Log level for the frozen backend. |

## Webapp Backend (bridge)

The webapp's FastAPI bridge (`webapp/backend/bridge/main.py`) serves
`/api/llm/chat`, `/health`, and mounts the MCP app at `/mcp`. Its CORS policy
follows the fleet standard (tauri origins, Tailscale *.ts.net, LAN subnets,
CGNAT). LLM provider config lives in browser localStorage (`llm_config`,
`llm_provider`, `llm_model`) via the Settings page.

## Logging

structlog JSON output to `logs/filesystem_mcp.log` (repo-relative, with a
fallback to `~/.filesystem-mcp/`) plus stderr. HTTP daemon logs additionally
stream through the Tauri app to `backend-spawn.log` in the app log directory.

## Related Docs

- [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) — transport and design
- [MONITORING_STACK_DEPLOYMENT.md](MONITORING_STACK_DEPLOYMENT.md) — observability stack
- [CONTAINERIZATION_GUIDELINES.md](CONTAINERIZATION_GUIDELINES.md) — Docker deployment
