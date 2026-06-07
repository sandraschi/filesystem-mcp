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

> **Windows:** After any winget install, **close and reopen PowerShell** so PATH updates apply.  
> **macOS:** use `brew install uv git node` equivalents.

Docker Desktop is **only needed** for the Docker container management tools (`container_ops`,
`compose_*`). File system and Git tools work without it.

---

## Option A — Drag and Drop (Recommended)

No Python, uv, or git required. Claude Desktop manages the runtime.

1. Go to [Releases](https://github.com/sandraschi/filesystem-mcp/releases/latest)
2. Download `filesystem-mcp-*.mcpb`
3. Open Claude Desktop
4. Drag the `.mcpb` file onto the Claude Desktop window and accept the install prompt

**Pass criteria:** server appears in the MCP list with no terminal steps.

---

## Option B — mcpb CLI

`mcpb` is **not** on PyPI — `uvx mcpb` will fail. Requires Node.js:

```powershell
winget install OpenJS.NodeJS --accept-source-agreements --accept-package-agreements
# Close and reopen terminal, then:
npx @anthropic-ai/mcpb install https://github.com/sandraschi/filesystem-mcp
```

Restart Claude Desktop after install completes.

---

## Option C — Manual Configuration

```powershell
winget install astral-sh.uv --accept-source-agreements --accept-package-agreements
winget install Git.Git --accept-source-agreements --accept-package-agreements
# Close and reopen terminal

git clone https://github.com/sandraschi/filesystem-mcp
cd filesystem-mcp
uv sync --all-extras
```

Edit Claude Desktop config:

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
        "filesystem-mcp",
        "--stdio"
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

For contributing or running from source. Requires all tools in Prerequisites.

```powershell
winget install Casey.Just --accept-source-agreements --accept-package-agreements
git clone https://github.com/sandraschi/filesystem-mcp
cd filesystem-mcp
uv sync --all-extras
uv run filesystem-mcp --stdio
```

For the optional web frontend (http://localhost:10742):

```powershell
$env:MCP_TRANSPORT = "http"
uv run filesystem-mcp
cd webapp && npm install && npm run dev
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for linting, testing, and build steps.

---

## Verify Installation

In Claude Desktop, try:

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

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for the full reference.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Server not in Claude Desktop | Run `uv run filesystem-mcp --stdio` directly to see error; check config path |
| `uv` not found | `winget install astral-sh.uv`; reopen terminal |
| `git` not found | `winget install Git.Git`; reopen terminal |
| Docker tools return "daemon not running" | Start Docker Desktop |
| Port 10742 already in use | Set `MCP_PORT` to a free port in the `env` block |
| `uv sync` fails | Ensure Python 3.12+: `uv python install 3.12` |
| `uvx mcpb` fails | Expected — use Option A or `npx @anthropic-ai/mcpb` |

Full diagnostics: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) · [open an issue](https://github.com/sandraschi/filesystem-mcp/issues)

---

*Feature overview: [README.md](README.md)*
