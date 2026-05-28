# Installing filesystem-mcp

File system, Git, and Docker operations for Claude Desktop and Claude Code.

---

## Prerequisites

Install these if you don't have them already. Windows commands use
[winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/)
(built into Windows 10 1809+ / Windows 11):

| Tool | Required for | Windows | macOS |
|------|-------------|---------|-------|
| **Claude Desktop** | all options | [claude.ai/download](https://claude.ai/download) | same |
| **uv** | Options C and D | `winget install astral-sh.uv` | `brew install uv` |
| **git** | clone repo (Options C/D) | `winget install Git.Git` | `brew install git` |
| **Node.js** | Option B, or web frontend | `winget install OpenJS.NodeJS` | `brew install node` |
| **Docker Desktop** | Docker/compose tools only | [docker.com/get-started](https://www.docker.com/get-started/) | same |

> After a winget install, close and reopen your terminal so the new tool is on PATH.

Docker Desktop is **only needed** if you want to use the Docker container management tools
(`container_ops`, `compose_*`). File system and Git tools work without it.

---

## Option A — Drag and Drop (Recommended)

No Python, uv, or git required. Claude Desktop manages the runtime.

1. Go to [Releases](https://github.com/sandraschi/filesystem-mcp/releases/latest)
2. Download `filesystem-mcp-{version}.mcpb`
3. Open Claude Desktop
4. Drag the `.mcpb` file onto the Claude Desktop window and accept the install prompt

Done.

---

## Option B — mcpb CLI

Requires Node.js (see Prerequisites above).

```powershell
npx @anthropic-ai/mcpb install https://github.com/sandraschi/filesystem-mcp
```

> `uvx mcpb` will NOT work — mcpb is an npm package, not on PyPI.

---

## Option C — Manual Configuration

Requires uv and git (see Prerequisites above).

```powershell
git clone https://github.com/sandraschi/filesystem-mcp
cd filesystem-mcp
uv sync
```

Add to `claude_desktop_config.json`:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "filesystem-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\path\\to\\filesystem-mcp",
        "run",
        "filesystem-mcp"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

Replace `C:\\path\\to\\filesystem-mcp` with your actual clone path. Restart Claude Desktop.

---

## Option D — Developer Mode

For contributing or running with live reload. Requires all tools in Prerequisites.

```powershell
git clone https://github.com/sandraschi/filesystem-mcp
cd filesystem-mcp
uv sync

# Start in stdio mode (MCP clients)
uv run filesystem-mcp

# Start in HTTP mode (web dashboard at http://localhost:10742)
$env:MCP_TRANSPORT = "http"
uv run filesystem-mcp
```

For the optional web frontend:

```powershell
cd webapp
npm install
npm run dev
# Opens http://localhost:10742
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for full dev setup including linting and tests.

---

## Verify Installation

After installing, open Claude Desktop and type:

> "List the files in my home directory"

You should see a directory listing from `file_ops`. If you get "tool not found",
restart Claude Desktop and check that the server appears in Settings → MCP Servers.

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` \| `http` \| `sse` |
| `MCP_HOST` | `127.0.0.1` | Bind address for HTTP/SSE |
| `MCP_PORT` | `10742` | MCP HTTP port |
| `FASTMCP_LOG_LEVEL` | `WARNING` | Log verbosity: `DEBUG` \| `INFO` \| `WARNING` |
| `PYTHONUNBUFFERED` | — | Set to `1` in Claude Desktop config |

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for the full variable reference.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Server not in Claude Desktop | Run `uv run filesystem-mcp` directly in terminal to see error; check config path |
| `uv` not found | `winget install astral-sh.uv` then reopen terminal |
| `git` not found | `winget install Git.Git` then reopen terminal |
| Docker tools return "daemon not running" | Start Docker Desktop |
| Port 10742 already in use | Set `MCP_PORT` to a free port in the `env` block |
| `uv sync` fails | Ensure Python 3.12+ is available: `uv python install 3.12` |
| `npx mcpb` fails | Ensure Node.js is installed: `winget install OpenJS.NodeJS` |

For more: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) · [open an issue](https://github.com/sandraschi/filesystem-mcp/issues)
