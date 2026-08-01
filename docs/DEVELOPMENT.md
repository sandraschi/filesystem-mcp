# Development

## Quick Start

```powershell
just bootstrap   # uv sync --extra dev + pre-commit install + npm ci
just serve       # HTTP daemon on 127.0.0.1:10742
just mcp         # stdio mode for IDE MCP clients
just test        # pytest
just lint        # ruff + biome
just certify     # ruff + format check + import check + pytest
```

## Repository Layout

```
src/filesystem_mcp/
├── __init__.py            # FastMCP app, tool imports, HTTP app + REST routes
├── server.py              # ASGI entry (uvicorn filesystem_mcp.server:app)
├── transport.py           # stdio/http/sse runner
├── concurrency.py         # per-path locks + atomic writes
└── tools/
    ├── portmanteau_file.py            # file_ops (13 ops)
    ├── portmanteau_directory.py       # dir_ops
    ├── portmanteau_search.py          # search_ops
    ├── portmanteau_container.py       # container_ops
    ├── portmanteau_infrastructure.py  # infra_ops (images/networks/volumes)
    ├── portmanteau_orchestration.py   # compose_* tools
    ├── portmanteau_monitoring.py      # monitor_get_* (8 tools)
    ├── portmanteau_host.py            # host_ops
    ├── portmanteau_file_safe.py       # locks + concurrency test
    ├── portmanteau_system.py          # server_shutdown
    ├── agentic_file_workflow.py       # sampling workflow
    └── utils.py                       # response helpers, path safety
webapp/                  # React + Vite + Tailwind + Zustand frontend
native/                  # Tauri 2 wrapper (Rust), NSIS installer
tests/                   # pytest suite (94 tests)
```

## Adding a Tool

1. Create (or extend) a module in `src/filesystem_mcp/tools/`.
2. Register the module in the `tool_modules` list inside `_import_tools()` in
   `src/filesystem_mcp/__init__.py` — **no import, no tool**.
3. Follow the docstring protocol: `## Return Format` + `## Examples` mandatory,
   parameters documented via `Annotated[..., Field(...)]`, no `Args:` blocks.
4. Return `{"success": bool, "action": str, "message": str, "result": {...}}`
   via `_success_response` / `_error_response` helpers.
5. Add a test in `tests/` and run `just certify`.

## Adding a REST Route

Add `@app.custom_route(...)` at module level, or extend the route list in
`http_app()` next to `/api/status` and `/api/capabilities`. Keep the fleet
response shape `{"success": bool, ...}`.

## Webapp

```powershell
cd webapp
npm run dev     # Vite dev server on 10743, proxies /api + /mcp to 10742
npm run build   # production build to webapp/dist (embedded in Tauri)
npx tsc --noEmit
npx biome check --write src/
npx playwright test   # e2e audit
```

## Native (Tauri)

```powershell
just build-native    # PyInstaller backend -> resources -> cargo tauri build (NSIS)
just cua-nsis-test   # install -> launch -> health -> screenshot -> uninstall
```

See `native/` for the wrapper; the backend is embedded via `bundle.resources`
(never `externalBin`) and spawned by `native/src/backend.rs`.

## Testing

- 94 pytest tests (unit + integration) with coverage gate (`--cov-fail-under=50`).
- Playwright e2e: `webapp/e2e/fleet-audit.spec.ts`.
- CUA-NSIS smoke: `scripts/cua-smoke.py`.

## Conventions

- Ruff (line-length 120) + Biome + pre-commit hooks.
- LF line endings via `.gitattributes`.
- Ports 10742/10743 from the fleet registry — never use 3000/5000/5173/8000/8080.

## Related Docs

- [AI_DEVELOPMENT_RULES.md](AI_DEVELOPMENT_RULES.md)
- [DEVELOPMENT_PAIN_POINTS.md](DEVELOPMENT_PAIN_POINTS.md)
- [TOOL_DOCSTRING_STANDARD.md](TOOL_DOCSTRING_STANDARD.md)
- [DEBUGGING_LESSONS_LEARNED.md](DEBUGGING_LESSONS_LEARNED.md)
