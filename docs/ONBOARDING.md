# Onboarding — filesystem-mcp

Get joy in under 5 minutes: file operations, system monitoring, and an LLM chat
that actually answers.

## What this is for

filesystem-mcp is a local-first MCP server: 24 tools for file IO, directory
work, content search, Docker, and host monitoring, plus a web dashboard
(backend :10742, frontend :10743) with Chat, Tools, Skills, and Inbox pages.

## What you need

- **Nothing to install to get value.** Clone the repo and start it; file tools,
  search, and monitoring work immediately.
- **Docker (optional):** only the `container_ops` / `infra_ops` / `compose_*`
  tools need a Docker daemon. Without it they return a clear `docker_error`.
- **Ollama (optional, free):** for the Chat page. Install from
  https://ollama.com, pull one model (`ollama pull llama3.2:3b`), and the
  dashboard detects it automatically. LM Studio works too.
- **Money / accounts:** none for local use. Cloud providers (OpenAI, Anthropic)
  need your own API key, entered in Settings; keys stay in your browser and go
  to the provider only through the backend proxy.

## Start it

```powershell
.\start.ps1            # backend + frontend + browser
.\start.ps1 -BackendOnly   # API only (for agents / Claude Desktop stdio)
```

## Sanity check (60 seconds)

1. Open the dashboard (`http://127.0.0.1:10743`) — backend dot must be green.
2. Chat page: pick the detected provider, send "reply with exactly: HI".
   If you see HI, the backend chat proxy works end to end.
3. Inbox page: every tool call above left a receipt there. Empty Inbox with a
   green backend dot means nothing has run yet — not a bug.

## Pitfalls

- **Port squatters:** if `:10742` is held by a stale process, the backend exits
  on bind. `start.ps1` clears stale listeners first; services (Session 0) must
  be restarted via `services.msc`, never taskkill.
- **Chat 404/502:** 404 = backend predates the `/api/llm/chat` route (pull
  latest); 502 with an Ollama message = Ollama itself is broken (repair Ollama,
  the proxy just forwards its answer).
- **Docker tools failing:** Docker daemon not running. Start Docker Desktop;
  everything else keeps working.
- **API keys:** Settings stores them in `localStorage` (browser-only). No
  keystore migration yet — do not commit exported configs containing keys.

## Where to look next

- `docs/CONFIGURATION.md` — env vars and ports.
- `docs/TOOLS.md` — full tool catalog.
- `docs/TROUBLESHOOTING.md` — when something breaks.
