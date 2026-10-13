# Filesystem MCP — User Guide

## Introduction

Filesystem MCP is a FastMCP 3.4+ server that turns your file system, Docker
containers, and computer's health metrics into MCP tools any AI assistant can use.
Instead of describing what you want done, you can let the assistant directly read,
write, edit, search, compare, move, and analyze files; create and manage
directories; list, start, stop, and inspect Docker containers, images, networks,
and volumes; orchestrate Docker Compose stacks; and pull live CPU, memory, disk,
process, and network statistics.

This guide teaches you how to use the server from three angles: as a user of the
bundled webapp, as a user of an AI client (Claude Desktop, Cursor, Windsurf,
opencode) that connects over MCP, and as a developer who wants to script or extend
it. Every section is a tutorial: do this, then that, and you will see these
results. The examples use Windows paths (D:/Dev/repos/...) because that is the
primary fleet environment, but everything works on macOS and Linux too — just
adjust the paths.

## 1. Quick Start

### 1.1 Installation

The server is distributed as a Python package managed with uv. Clone the
repository and bootstrap:

```
git clone https://github.com/sandraschi/filesystem-mcp
cd filesystem-mcp
just bootstrap
```

`just bootstrap` installs the Python dependencies (including dev tools and
pre-commit hooks) and the webapp's Node dependencies. If you do not use `just`,
run `uv sync --extra dev` followed by `npm ci` inside `webapp/`.

### 1.2 Running in stdio mode (Claude Desktop / Cursor / opencode)

The simplest way to connect an AI client is stdio mode:

```
just mcp
```

or directly `uv run python -m filesystem_mcp`. The server prints JSON-RPC
messages on stdout and logs to `logs/filesystem_mcp.log` plus stderr.

For Claude Desktop, add this to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "filesystem-mcp": {
      "command": "uv",
      "args": ["--directory", "D:/Dev/repos/filesystem-mcp", "run", "filesystem-mcp"]
    }
  }
}
```

For Cursor, add the same command under Settings > MCP. For opencode, add it to
`opencode.json`'s `mcp` section. The server supports several simultaneous
clients because every file write is protected by a per-path lock.

### 1.3 Running in HTTP mode (webapp)

The React webapp talks to the server over HTTP. Start everything with the fleet
launcher:

```
webapp\start.ps1
```

This clears the registered ports (10742 backend, 10743 frontend) of zombie
processes, waits for the backend health check, starts the Vite dev server, and
opens your browser at http://127.0.0.1:10743. The backend serves:

- `GET /api/health` and `GET /health` — liveness probes
- `GET /api/status` — server name, version, uptime, registered tool count
- `GET /api/capabilities` — the full tool list and feature flags
- `GET /api/skills` — skill registry (empty until skills are added)
- `GET /api/llm/discover` — probes for Ollama (11434) and LM Studio (1234)
- `POST /api/llm/chat` — LLM proxy (Ollama, LM Studio, OpenAI, Anthropic)
- `GET /api/v1/diagnostics` — system CPU/memory/disk plus tool inventory
- `/mcp` — the streamable MCP endpoint for MCP-over-HTTP clients

### 1.4 Desktop app (Tauri)

The repo ships a Tauri 2 native wrapper. Build the installer with
`just build-native`, then run the CUA smoke test with `just cua-nsis-test`
(install, launch, verify, uninstall). The installer embeds the frozen Python
backend, so users on a naked PC need nothing installed: one shortcut, one app.
On first launch it registers itself for Cursor/Claude Desktop via an optional
NSIS dialog.

## 2. The Webapp

The webapp has ten pages, reachable from the left sidebar:

- **Dashboard** — hero with backend status, KPI cards (server version, registered
  tools, uptime, local LLM detection), quick actions, and capability summary.
- **Chat** — skill-first chat against your local LLM with four personalities
  (Research Assistant, Expert Reviewer, Quick Summarizer, Custom), example
  prompts, conversation export to .txt, and clear. History persists in
  localStorage (100 messages cap).
- **Apps** — pre-filled chat workflows (Code Review, Log Analyzer, System Doctor,
  Large File Hunt, Disk Space Audit).
- **File Browser** — browse directories on the machine.
- **Tools** — the tool catalog mapped to pages.
- **Git Ops** — git operations page.
- **Docker** — container and compose console.
- **Logs** — server log overview.
- **Settings** — appearance (dark/light/system), LLM provider configuration with
  auto-detection of Ollama and LM Studio, model selection, API keys.
- **Help** — reference and troubleshooting.

The top bar shows the live backend connection dot (green/red) with exponential
backoff retries, and a theme toggle. Ctrl+scroll zooms the UI (persisted), and in
the Tauri app the backend-status event refreshes instantly.

## 3. File Operations Tutorial

The `file_ops` tool is the workhorse. It takes an `operation` parameter and a set
of optional parameters. Let's walk through the operations in order of use.

### 3.1 Reading a file

Ask your assistant to read a file, or call the tool directly:

```
file_ops(operation="read_file", path="D:/Dev/repos/myproject/config.json")
```

The response contains the content, size, line count, encoding, metadata, and a
recommendation when a file is large enough that a windowed read would be smarter.
For a 2 GB log, use `read_file_lines` with an offset and limit instead:

```
file_ops(operation="read_file_lines", path="D:/logs/big.log", offset=0, limit=200)
```

### 3.2 Writing a file

```
file_ops(operation="write_file", path="D:/Dev/repos/myproject/notes.md",
         content="# My Notes\nCreated by MCP.")
```

Writes are atomic: the server writes to a temp file in the same directory and
renames it over the target. A `.backup` of any previous content is created unless
you pass `no_backup=True`. Missing parent directories are created by default.

### 3.3 Editing a file

```
file_ops(operation="edit_file", path="D:/Dev/repos/myproject/app.py",
         old_string="host = 'localhost'", new_string="host = '0.0.0.0'")
```

The edit is exact-match. If the assistant's reproduction of the original text has
drifted (extra spaces, line-wrapping), enable `ignore_whitespace=True`. To replace
every occurrence, pass `allow_multiple=True`. To use a regex, pass `is_regex=True`
and `new_string` may contain backreferences. Every edit writes a `.backup`, and
you can revert the most recent edit on a path:

```
file_ops(operation="undo_edit", path="D:/Dev/repos/myproject/app.py")
```

### 3.4 Moving, copying, deleting

```
file_ops(operation="move_file", path="D:/tmp/a.txt", destination_path="D:/docs/a.txt")
file_ops(operation="copy_file", path="D:/docs/a.txt", destination_path="D:/backup/a.txt")
file_ops(operation="delete_file", path="D:/tmp/old.bin")
```

`move_file` and `copy_file` refuse to overwrite existing destinations unless you
pass `overwrite=True`. Deleting is permanent — there is no trash can, so ask the
user before deleting and prefer `move_file` to an archive folder for anything
ambiguous.

### 3.5 Inspecting files

```
file_ops(operation="file_exists", path="D:/data/input.csv")
file_ops(operation="get_file_info", path="D:/data/input.csv", include_content=False)
file_ops(operation="head_file", path="D:/data/input.csv", lines=5)
file_ops(operation="tail_file", path="D:/data/input.csv", lines=5)
```

`get_file_info` returns size, modification time, type, and (optionally) content.
`head_file`/`tail_file` are great for peeking at CSVs and logs without loading
them.

### 3.6 Batch reads

```
file_ops(operation="read_multiple_files",
         file_paths=["D:/dev/a.py", "D:/dev/b.py", "D:/dev/c.py"],
         include_content=True, max_file_size_mb=5)
```

Files larger than the per-file cap are reported as truncated instead of blowing
up the context.

## 4. Directory Operations Tutorial

`dir_ops` manages folders.

```
dir_ops(operation="list_directory", path="D:/Dev/repos", recursive=False)
```

Add `recursive=True` to descend (bounded by `max_files=1000`), and
`include_hidden=True` to see dotfiles. To understand a tree visually:

```
dir_ops(operation="directory_tree", path="D:/Dev/repos/arxiv-mcp/src", max_depth=3)
```

`calculate_directory_size` answers "what is eating my disk":

```
dir_ops(operation="calculate_directory_size", path="D:/data", human_readable=True)
```

`find_empty_directories` is handy for cleanup campaigns, and `create_directory`
with `create_parents=True` builds nested folders in one call.

## 5. Search and Analysis Tutorial

`search_ops` is the query engine.

### 5.1 Grep

```
search_ops(operation="grep_file", path="D:/Dev/repos", search_pattern="assfix",
           recursive=True, context_lines=2)
```

Binary files are detected and skipped, so results are clean text matches. Use
`case_sensitive=False` for case-insensitive search. `count_pattern` returns just
the count.

### 5.2 Finding large files

```
search_ops(operation="find_large_files", path="D:/", min_size_mb=500)
```

Returns paths and sizes above the threshold — the starting point of any disk
triage.

### 5.3 Finding duplicates

```
search_ops(operation="find_duplicate_files", path="D:/photos", hash_algorithm="sha256")
```

Content-hash based, so identical files with different names are found. Use
`min_size` to skip tiny files and `max_duplicates` to bound the output.

### 5.4 Comparing files

```
search_ops(operation="compare_files", path="D:/dev/a.txt", path2="D:/dev/b.txt")
```

Returns a unified diff — perfect for reviewing what changed between two versions
of a file without a git history.

### 5.5 Extracting log lines

```
search_ops(operation="extract_log_lines", path="D:/logs/app.log",
           start_time="2026-08-01T00:00:00", end_time="2026-08-01T23:59:59",
           log_levels=["ERROR", "CRITICAL"], max_lines=200)
```

Time-bounded, level-filtered log extraction. Combine with `grep_file` around the
first match for stack traces.

## 6. Docker Tutorial

### 6.1 Containers

```
container_ops(operation="list_containers", show_stats=True)
container_ops(operation="get_container", container_id="web")
container_ops(operation="container_logs", container_id="web", tail=100)
container_ops(operation="container_stats", container_id="web")
```

Creating a container:

```
container_ops(operation="create_container", image="nginx:alpine", name="web-proxy",
              ports={"8080/tcp": 80}, detach=True)
```

Running commands inside a container:

```
container_ops(operation="container_exec", container="db",
              command="psql -U postgres -c 'SELECT 1'")
```

`stdin_data` lets you pipe input directly, avoiding a docker cp + exec dance.
Lifecycle ops are `start_container`, `stop_container` (with a stop timeout),
`restart_container`, and `remove_container` (use `force=True` for running
containers you really want gone).

### 6.2 Images, networks, volumes

```
infra_ops(operation="list_images", all_images=True)
infra_ops(operation="pull_image", image="postgres", tag="17-alpine")
infra_ops(operation="build_image", path="D:/dev/myapp", tag="myapp:latest")
infra_ops(operation="remove_image", image="myapp:old")
infra_ops(operation="create_network", name="app-net")
infra_ops(operation="create_volume", name="data-vol")
infra_ops(operation="list_volumes")
```

`prune_images` and `prune_volumes` reclaim space; they are destructive, so run
them only when the user agrees.

## 7. Docker Compose Tutorial

The compose tools wrap `docker compose` and take a `path` to the compose file
directory:

```
compose_config(path="D:/dev/services", validate=True)   # validate first
compose_up(path="D:/dev/services", detach=True)
compose_ps(path="D:/dev/services", all_services=True)
compose_logs(path="D:/dev/services", tail=100)
compose_restart(path="D:/dev/services", services=["web"])
compose_down(path="D:/dev/services")
```

`compose_up` supports `scale` (`{"worker": 3}`) and `build=True`. Be careful with
`compose_down(volumes_prune=True)` — it deletes anonymous volumes declared in the
compose file, which is data loss.

## 8. System Monitoring Tutorial

Eight read-only tools report machine health:

```
monitor_get_resource_usage()          # quick CPU/mem/disk %
monitor_get_system_status()           # full snapshot
monitor_get_process_info(max_processes=10, sort_by="memory_percent")
monitor_get_disk_usage()              # per-partition
monitor_get_cpu_info()                # per-core usage
monitor_get_memory_info()             # virtual + swap
monitor_get_performance_metrics()     # counters
monitor_get_network_info()            # interfaces + I/O
```

Use these before heavy operations to confirm headroom, and during incidents to
correlate symptoms with CPU/memory/disk spikes.

## 9. Host Context Tutorial

`host_ops` answers "who am I, where am I, what is this machine?":

```
host_ops(operation="get_system_info")
host_ops(operation="get_environment_info")
host_ops(operation="get_hardware_info")
host_ops(operation="get_user_info")
host_ops(operation="get_help", category="filesystem")
```

`get_help` is a multilevel help system that can return targeted documentation per
category and detail level — a good first call when learning the surface.

## 10. Agentic File Workflows

`agentic_file_workflow` delegates the reasoning to your host's LLM via MCP
sampling. Give it a natural-language goal and a hint about which tool groups to
use:

```
agentic_file_workflow(workflow_prompt="Find all TODO comments in src/ and
                       summarize them by module", available_tools=["search_ops"])
```

The server gathers file system context (listings, file heads) server-side and
sends it to the host LLM with the prompt. The response includes the execution
trail (`steps_executed`, `results`, `notes`), a summary, and recommendations. If
your host does not support sampling, the tool returns `NO_CONTEXT` with recovery
options — fall back to composing `file_ops`/`search_ops` calls yourself.

## 11. Concurrency and Safety

The headline feature is safe concurrent access. If Claude Desktop and Cursor both
edit the same file, each write is serialized by a per-path lock and applied
atomically. You can verify the layer with the built-in stress test:

```
test_concurrency_safety(operation="write", num_clients=8)
```

It reports how many of the concurrent clients succeeded — all should. To see
which paths currently hold locks:

```
get_lock_status()
```

Every write creates a `.backup`; every edit can be undone with `undo_edit`. If
something ever looks wrong, the undo path is the recovery.

## 12. Shutting the Server Down

The HTTP daemon can terminate itself gracefully:

```
server_shutdown(confirm=True)
```

Without `confirm=True` the tool returns a clarification response. The process
exits about a second later so in-flight responses can flush. Stdio instances exit
when the parent client closes the stream.

## 13. Configuration Reference

Environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `MCP_TRANSPORT` | `stdio` | `stdio`, `http`, or `sse` |
| `MCP_HOST` | `127.0.0.1` | HTTP bind address |
| `MCP_PORT` | `10742` | HTTP port (fleet registered) |
| `MCP_PATH` | `/mcp` | MCP endpoint path |
| `MCP_BRIDGE_URLS` | (empty) | Comma-separated remote MCP URLs to bridge |
| `DOCKER_ENABLED` | (auto) | Set `false` to skip Docker tool registration |

The Tauri app spawns the frozen backend with `FILESYSTEM_PORT`,
`FILESYSTEM_HOST`, and `FILESYSTEM_MCP_TAURI=1`.

Logs: structlog JSON to `logs/filesystem_mcp.log` and stderr. On startup the
server cleans up orphaned stdio processes from stale IDE sessions but never kills
the HTTP daemon holding port 10742.

## 14. Troubleshooting

**The webapp shows "Backend offline".** Start the backend: `webapp\start.ps1`.
Check `logs/filesystem_mcp.log` for startup errors. Confirm nothing else holds
port 10742 (`Get-NetTCPConnection -LocalPort 10742`).

**The assistant says "No operation specified".** A portmanteau call was missing
the `operation` parameter. The error lists the valid values — pass one.

**An edit changed nothing.** The `old_string` did not match exactly. Enable
`ignore_whitespace=True` or switch to regex mode, then retry.

**Docker tools fail with `docker_error`.** The daemon is unreachable. Start Docker
Desktop (or `Start-Service docker`), wait for it, and retry. The recovery options
in the error tell you the exact command to run.

**Chat says "LLM Error".** The provider is not running or the model is missing.
Open Settings, confirm Ollama or LM Studio is detected, and refresh the model
list. Then save.

**A grep returns nothing.** The pattern may be in a binary file or the case
differs. Add `case_sensitive=False`, and check the file type with `get_file_info`.

**Concurrent clients conflict.** Run `test_concurrency_safety` to verify the lock
layer, then `get_lock_status` to inspect current locks. If a lock is stuck,
restart the server — locks are in-memory and do not survive restarts.

## 15. FAQ

**Do I need Docker to use the server?** No. File, directory, search, monitoring,
and host tools work without Docker. Docker tools fail with a clear `docker_error`
when the daemon is missing.

**Can multiple AI clients connect at once?** Yes. The concurrency layer exists
exactly for that. All clients share the same filesystem, so coordination is
"last write wins" with atomicity guarantees.

**Are writes really atomic?** Yes. Temp file + `os.replace()` in the same
directory means a crash at any point leaves either the old file or the new file,
never a torn write.

**Where are the backups?** Next to the file, named `<file>.backup`
(`no_backup=True` disables them per call). `undo_edit` restores the latest one.

**Does the server touch the internet?** No, except Docker Hub when you pull
images. File operations are local-only.

**How do I update?** `git pull` inside the repo, then `uv sync --extra dev` and
`npm ci` in `webapp/` if dependencies changed. Restart the backend.

**Where do I get support?** Open an issue on
https://github.com/sandraschi/filesystem-mcp or check `docs/` in the repository
(TECHNICAL_ARCHITECTURE.md, TROUBLESHOOTING_FASTMCP_2.12.md, and the deployment
guides).

## 16. Deep Dive: Every file_ops Parameter

This section documents the exact parameters accepted by `file_ops` so you can
build precise calls without trial and error.

- `operation` (required) — one of the thirteen documented operations.
- `path` — the target file path. Use forward slashes on Windows
  (D:/data/input.csv) to avoid escape-character bugs.
- `content` — text for `write_file` (and `edit_file`'s replacement in some
  callers); omitted for reads.
- `encoding` — default `utf-8`. Pass `utf-16` or `latin-1` for legacy files.
- `old_string` / `new_string` — the find/replace pair for `edit_file`.
- `old_str` / `new_str` — accepted aliases matching Claude's built-in
  str_replace tool, so both conventions work.
- `file_paths` — list for `read_multiple_files`.
- `destination_path` — target for `move_file` / `copy_file`.
- `overwrite` — default `false`; must be `true` to clobber an existing
  destination.
- `offset` / `limit` — window controls for `read_file_lines`.
- `lines` — count for `head_file` / `tail_file` (default 10).
- `check_type` — `"file"` or `"any"`, for `file_exists`.
- `follow_symlinks` — default `true`.
- `include_content` / `max_content_size` — metadata enrichment for
  `get_file_info` (default cap 1 MB).
- `create_parents` — default `true`; writes create missing directories.
- `no_backup` — default `false`; set `true` to skip `.backup` creation.
- `max_file_size_mb` — per-file cap for batch reads (default 10).
- `allow_multiple` — replace all occurrences in `edit_file`.
- `is_regex` — treat `old_string` as a Python regex.
- `ignore_whitespace` — normalize indentation before matching.
- `replacements` — list of `{old_string, new_string}` dicts for batch edits.

### 16.1 Parameter combinations that matter

- Reading the tail of a growing log: `tail_file(path, lines=50)`.
- Editing every occurrence of a version string:
  `edit_file(path, old_string="1.2.3", new_string="1.2.4", allow_multiple=True)`.
- Regex cleanup: `edit_file(path, old_string=r"\s+$", new_string="",
  is_regex=True, allow_multiple=True)` strips trailing whitespace.
- Reading a slice of a huge CSV: `read_file_lines(path, offset=100, limit=50)`.

## 17. Deep Dive: Docker Compose Patterns

### 17.1 Zero-downtime rebuild

1. `compose_config(path, validate=True)` — catch YAML errors first.
2. `compose_up(path, build=True)` — rebuild changed images.
3. `compose_ps(path)` — confirm the new containers are healthy.
4. `compose_logs(path, tail=50)` — verify clean startup.
5. On failure: `compose_logs` since the restart time, fix, and `compose_restart`.

### 17.2 Scaling workers

`compose_up(path, scale={"worker": 3})` starts three worker replicas. Verify
with `compose_ps` and watch load with `container_stats` on each replica. Scale
down with `compose_up(path, scale={"worker": 1})` (compose converges to the
requested replica count).

### 17.3 Diagnosing a crash-looping service

1. `compose_ps(path, all_services=True)` — find the service with state
   `Restarting`.
2. `compose_logs(path, services=["<name>"], tail=200)` — read the crash output.
3. `container_ops(operation="container_stats", container_id="<name>")` — check
   for OOM/CPU limits.
4. Present the cause and the fix; do not silently restart loops.

## 18. Deep Dive: Monitoring in Practice

### 18.1 A health snapshot you can paste anywhere

```
monitor_get_resource_usage()
```

returns CPU percent, memory (total/available/percent), disk usage, and boot time
in one call. It is the recommended first probe.

### 18.2 Process forensics

```
monitor_get_process_info(filter_pattern="python", max_processes=50,
                         sort_by="cpu_percent")
```

shows every Python process sorted by CPU. Add `sort_by="memory_percent"` to find
memory hogs. AccessDenied on system processes is normal; the filter keeps output
focused.

### 18.3 Capacity planning

`monitor_get_performance_metrics()` returns the raw counters; sample it twice a
few seconds apart and diff to get utilization rates. `monitor_get_disk_usage()`
per partition reveals which volume is about to fill.

## 19. Deployment Scenarios

### 19.1 Single user, one client (simplest)

`just mcp` in a terminal. The client spawns it on demand. No HTTP, no ports, no
webapp. Claude Desktop or Cursor just works.

### 19.2 Family of clients sharing the machine

Start the HTTP daemon once (`MCP_TRANSPORT=http uv run filesystem-mcp` or the
webapp launcher), then configure every client with the HTTP endpoint
`http://127.0.0.1:10742/mcp`. All clients share one daemon and its concurrency
layer — no per-client database contention, because there is no database. The
daemon also survives individual client restarts.

### 19.3 LAN or Tailscale access

Bind the daemon to 0.0.0.0 (`MCP_HOST=0.0.0.0`) and connect from another device
via `http://<tailscale-ip>:10742/mcp`. The CORS configuration allows *.ts.net
hosts, LAN subnets, and Tailscale CGNAT ranges by default, so the webapp works
from tablets and phones on the tailnet. Use MCP_PORT to move off 10742 if another
service owns it.

### 19.4 Air-gapped machine

The server itself needs no internet. It only reaches the network when you pull
Docker images. Install dependencies from a local wheelhouse if you must, then run
fully offline.

## 20. Security and Auditing Guide

- **Path scope**: operations act on the paths you give them; there is no hidden
  "admin mode" that expands scope.
- **Backups are your audit trail**: every write/edit leaves a `.backup` next to
  the file. `get_lock_status` shows active locks. `undo_edit` reverts the latest
  edit on a path.
- **Logs**: structlog JSON in `logs/filesystem_mcp.log` records server events
  with ISO timestamps; correlate with file mtimes when investigating.
- **Secrets**: never put API keys in prompts to tools. The LLM chat proxy
  (`/api/llm/chat`) forwards keys only to the provider you configure in Settings;
  keys live in browser localStorage on the client side.
- **Destructive flags**: `force=True`, `volumes_prune=True`, `prune_*`, and
  `server_shutdown(confirm=True)` are guarded and documented. Only pass them on
  explicit user request.
- **Docker risk**: `container_exec` runs commands inside containers with the
  container's user context — scope commands to the container, never pass host
  credentials.
- **Multi-user machines**: bind to 127.0.0.1 unless you explicitly want LAN
  access. The webapp has no authentication layer; keep it on your tailnet or
  localhost.

## 21. Extending the Server

### 21.1 Adding a tool

Tools live in `src/filesystem_mcp/tools/`. Register a new module in the
`tool_modules` list inside `src/filesystem_mcp/__init__.py` (`_import_tools`),
then define:

```python
from .utils import READ_ONLY, _get_app, _success_response

@_get_app().tool(annotations=READ_ONLY, version="2.3.0")
async def my_new_tool(param: str) -> dict:
    """Describe what the tool does.

    ## Return Format
    {"success": bool, "action": str, "message": str, "result": {...}}

    ## Examples
    my_new_tool(param="value")
    """
    return _success_response(action="my_new_tool", message="Done.", data={...})
```

Docstrings follow the fleet SOTA protocol: `## Return Format` and `## Examples`
are mandatory, parameters are documented via `Annotated[..., Field(...)]`, and
`Args:` blocks are avoided.

### 21.2 Adding a REST endpoint

Add `@app.custom_route(...)` in `src/filesystem_mcp/__init__.py`, or add routes in
the `http_app()` builder alongside `/api/status` and `/api/capabilities`.

### 21.3 Rebuilding the webapp

The webapp is a Vite + React + Tailwind + Zustand app in `webapp/`. `npm run dev`
serves it with a proxy to the backend; `npm run build` produces `webapp/dist`,
which the Tauri app embeds.

## 22. Glossary

- **Portmanteau tool** — one MCP tool exposing several operations through an
  `operation` enum parameter (e.g. `file_ops` with thirteen operations).
- **Atomic write** — writing to a temp file and renaming over the target so
  readers never see partial content.
- **Per-path lock** — an in-process asyncio lock per file path serializing
  concurrent writes.
- **Dual transport** — the server speaks stdio (IDE clients) and HTTP streamable
  (webapp, LAN, Tailscale).
- **Sampling** — the MCP mechanism by which a tool asks the host LLM to reason
  (used by `agentic_file_workflow`).
- **MCPB** — the packaged bundle format for Claude Desktop distribution
  (`just mcpb-pack`).
- **CUA smoke test** — pywinauto-based installer certification
  (`just cua-nsis-test`): install, launch, health, screenshot, diagnostics,
  uninstall.

## 23. Using the Chat Page Effectively

The Chat page combines your local LLM with the MCP tool surface. Configure the
provider first in Settings (Ollama or LM Studio recommended), then:

1. Pick a personality in the dropdown: Research Assistant (careful, structured
   answers), Expert Reviewer (critical, technical), Quick Summarizer (short), or
   Custom (your own system prompt).
2. Click an example prompt to fill the input — for example "List the largest
   files in my home directory" or "Show me the git status of the current repo".
3. Send. The chat sends your history plus the server's tool catalog to the LLM,
   and the LLM may emit tool calls that the page renders inline.
4. Export the conversation to a .txt file with the download button, or clear it
   with the eraser button.

The conversation is stored in your browser (localStorage, capped at 100
messages), so reloading the page restores it. The Apps page pre-fills the chat
with entire workflows: Code Review, Log Analyzer, System Doctor, Large File Hunt,
and Disk Space Audit — click one and review the pre-filled prompt before sending.

## 24. Error Catalog

Every error response carries `error_type`. Here is what each one means and what
to do:

- `validation` — a required parameter (usually `operation`) is missing or an
  enum value is invalid. The response lists valid values. Fix the call.
- `not_found` — the path or container/image/volume does not exist. Verify with
  `file_exists` / `list_containers` / `list_images` before retrying.
- `file_error` — I/O failure (permission denied, path locked, disk full). Check
  ACLs, close other editors holding the file, and confirm free space.
- `docker_error` — daemon down, image missing, port bind conflict, or compose
  failure. `recovery_options` name the exact inspection command (e.g.
  `docker ps -a`, `docker compose config`).
- `internal_error` — unexpected exception. The server logs the full traceback;
  retry once, then check `logs/filesystem_mcp.log` for the cause.
- `NO_CONTEXT` (agentic_file_workflow) — the host client does not expose MCP
  sampling. Compose the workflow from ordinary tool calls instead.
- `SAMPLING_ERROR` — the host sampling call failed. Shorten the workflow prompt
  and retry.

## 25. Migrating from Other Filesystem MCP Servers

If you previously used a different filesystem MCP implementation, here is the
mapping:

- `read_file`/`write_file`/`edit_file` — identical semantics, but writes are now
  atomic and create `.backup` files by default.
- `list_directory` — was often a dedicated tool; here it is
  `dir_ops(operation="list_directory")`.
- Search tools — `grep_file` replaces ad-hoc `rg`-wrapper tools; binary sniffing
  is built in.
- Docker tools — `container_ops`/`infra_ops`/compose tools replace per-command
  scripts; every call is bounded by a hard timeout.
- Agentic workflows — `agentic_file_workflow` replaces DIY multi-tool
  orchestration with server-side context gathering + host sampling.

## 26. Performance Notes

- Reads are streamed through line windows for large files; avoid
  `read_file` on files over ~1 MB.
- `find_duplicate_files` hashes content; on big trees prefer `min_size` to skip
  small files and `max_duplicates` to bound work.
- `directory_tree` with `max_depth` and `pattern` keeps output proportional to
  what you need.
- Docker calls carry a hard `timeout`; compose builds can take minutes, so pass
  an appropriate `timeout` and check `compose_logs` rather than polling blindly.
- `monitor_get_*` tools are cheap; feel free to call them between operations.

## 27. Version History Highlights

- **2.2.x** — Tauri native wrapper, CUA smoke certification, MCPB packaging,
  concurrency diagnostics (`get_lock_status`, `test_concurrency_safety`),
  graceful `server_shutdown`, expanded REST surface
  (`/api/status`, `/api/capabilities`, `/api/skills`, `/api/llm/discover`).
- **2.1.x** — HTTP daemon + streamable MCP endpoint, bridge proxy for LLM chat.
- **2.0.x** — full portmanteau consolidation, dual transport, atomic writes.

## 28. Step-by-Step First Session

Walk through this once and you will have seen most of the surface:

1. Start the server: `just mcp`.
2. Ask your assistant: "What is the system status?" — it calls
   `monitor_get_resource_usage`.
3. Ask: "List the files in D:/Dev/repos" — `dir_ops` listing.
4. Ask: "Show me the first 20 lines of
   D:/Dev/repos/filesystem-mcp/README.md" — `head_file`.
5. Ask: "Search for the word TODO in D:/Dev/repos/filesystem-mcp/src" —
   `grep_file` with context.
6. Ask: "What is the biggest directory under D:/Dev/repos?" —
   `calculate_directory_size` on candidates.
7. Ask: "List running Docker containers" — `container_ops` listing.
8. Ask: "Show the largest processes on this machine" —
   `monitor_get_process_info(sort_by="memory_percent")`.
9. Ask the assistant to create a scratch file and then delete it — you will see
   the `.backup` appear next to it, proving the safety layer.
10. Open the webapp (`webapp\start.ps1`) and visit Dashboard, Tools, Chat, and
    Settings to see the same server from the browser.

## 29. Recommended Tool Sequences by Intent

| Intent | Sequence |
|--------|----------|
| "Find the file that defines X" | `grep_file` → `read_file_lines` → `edit_file` |
| "Free up disk space" | `monitor_get_disk_usage` → `calculate_directory_size` → `find_large_files` |
| "Is the app healthy?" | `compose_ps` → `compose_logs` → `container_stats` |
| "What changed on my machine?" | `get_system_info(detailed=True)` → `monitor_get_process_info` → `get_log_info` |
| "Clean a messy downloads folder" | `find_large_files` → `get_file_info` per candidate → `move_file` to archive |
| "Refactor a symbol" | `grep_file` (inventory) → `read_file` each site → `edit_file` each → `grep_file` (verify) |
| "Verify concurrency safety" | `test_concurrency_safety` → `get_lock_status` |

## 31. Appendix: Webapp Settings Explained

- **Appearance** — Light, Dark, or System. Dark is the fleet default; the choice
  persists per browser.
- **LLM Provider** — dropdown with Ollama (Local), LM Studio (Local), OpenAI,
  Anthropic, and Gemini. Selecting a local provider auto-fills its standard base
  URL and refreshes the model list.
- **Provider status badges** — shown above the dropdown after auto-detection:
  green "Detected" or gray "Not found" per provider. If none is detected, an
  amber banner suggests installing Ollama; a GPU-aware banner appears when a
  discrete GPU is detected and no LLM is running.
- **Base URL** — overridable per provider; useful for remote Ollama instances on
  your LAN or tailnet.
- **API Key** — required for cloud providers, not for local ones; stored only in
  your browser's localStorage and sent to the provider (or the bridge proxy)
  when chatting.
- **Model Name** — auto-populated from the detected provider; a manual input
  appears when no models could be fetched, so you can still type an exact model
  id. "Refresh Models" re-queries the provider.

The chosen provider and model are also mirrored to the `llm_provider` and
`llm_model` localStorage keys used by fleet tooling.

## 32. Appendix: REST API Reference

| Method | Path | Purpose | Example response |
|--------|------|---------|------------------|
| GET | `/api/health` | liveness | `{"status":"healthy","server_name":"filesystem-mcp","version":"2.2.0"}` |
| GET | `/health` | alias of health | same |
| GET | `/api/status` | uptime + tool count | `{"status":"ok","server":"filesystem-mcp","version":"2.2.0","uptime_seconds":42,"tool_count":24}` |
| GET | `/api/capabilities` | tool list + features | `{"capabilities":{"tools":[...],"features":{...}}}` |
| GET | `/api/skills` | skill registry | `{"skills":[]}` |
| GET | `/api/llm/discover` | provider probe | `{"providers":[{"name":"ollama","detected":true},...]}` |
| POST | `/api/llm/chat` | LLM proxy | `{"content":"...","tool_calls":null}` |
| GET | `/api/v1/diagnostics` | system + tools | `{"backend":{...},"system":{...},"tools":{"total":24}}` |
| GET | `/mcp` | streamable MCP | MCP protocol |


## 30. Final Notes

Filesystem MCP is designed to be boring and safe: atomic writes, backups,
guarded destructive operations, structured errors, and a concurrency layer that
lets several AI clients share one machine without corrupting each other's work.
When in doubt, prefer the non-destructive path (read, list, calculate, compare)
and let the user authorize moves, deletes, prunes, and shutdowns. The webapp is
your window, the chat is your voice, and the MCP surface is what any client can
reach. Enjoy the filesystem.
