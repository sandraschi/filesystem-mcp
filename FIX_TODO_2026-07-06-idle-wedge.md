# FIX TODO — fileops idle wedge / silent death (2026-07-06)

Status: DIAGNOSED. Steps 1-2 applied 2026-07-06 ~14:06 local. uv sync and
restart still pending — until then the running server is STILL on the buggy
stack and will keep wedging.

## Symptom

filesystem-mcp (Claude Desktop server name `fileops`) dies or wedges a few
minutes into every session. Pattern since 2026-07-04:

- Session starts clean, tool calls all succeed (sub-50ms).
- After a few minutes (idle or mid-session): either Claude Desktop logs
  "Server transport closed unexpectedly ... process exiting early"
  (process killed), or all subsequent calls hang until the client's
  4-minute timeout (event loop wedged).
- No traceback, no stderr, no lifespan shutdown log line.
- Only fileops affected; all other fleet servers in the same session fine.

Occurrences: Jul 4 20:48Z, Jul 4 21:28Z, Jul 5 16:48Z, Jul 6 11:08Z, plus
three live wedges during diagnosis on Jul 6 (~11:29Z, ~11:40Z, ~11:53Z —
the last ate a file write; check repo root for orphan .tmp.<hex> sidecar).

## Root cause (high confidence)

FastMCP **3.4.2 with the `[tasks]` extra** (pydocket 0.23.0 + redis 7.4.0
client), introduced by the dependency sync on **2026-07-03 ~23:45Z**
(pyproject.toml + uv.lock mtimes). Failures began the next session.

Mechanism: the tasks/Docket subsystem plus the 3.4.2 ping loop wedges the
stdio event loop after a few minutes. When the loop stops answering Claude
Desktop's pings, the client kills the process (the "crash" variant);
otherwise it presents as the classic fleet hang (schema loads, calls
time out).

Evidence:
- Server code is clean: no threads, no timers, no create_task, no blocking
  subprocess anywhere in src/. concurrency.py routes all blocking I/O
  through asyncio.to_thread.
- host_ops get_log_info (first observed hang trigger) is a static stub —
  the server was already wedged when it was called.
- get_lock_status returned an EMPTY lock table minutes before a wedge —
  the old "stale asyncio lock state" theory does not hold.
- Nothing in src/ uses task=True / Docket — the extra is dead weight.
- Upstream: FastMCP issue #2788 (stdio hang on Windows, traceback into
  docket/fakeredis; HTTP unaffected). 3.4.3+ notes: "ping loop now exits
  cleanly when a stream closes", "Docket is now reentrant", Windows
  console fixes.

## Fix steps

- [x] 1. pyproject.toml: `fastmcp[tasks]>=3.4.2,<4` -> `fastmcp>=3.4.3,<4`
        (tasks extra dropped; nothing uses it). Done 2026-07-06 14:06.
- [x] 2. run_server.py: added missing `import uvicorn` (latent NameError in
        the HTTP sidecar entry; unrelated to the wedge). Done 14:06.
- [ ] 3. `Set-Location D:\Dev\repos\filesystem-mcp; uv sync`
- [ ] 4. Verify: `uv pip list | Select-String "fastmcp|pydocket|redis"`
        (expect fastmcp >= 3.4.3; pydocket and redis GONE)
- [ ] 5. Restart fileops in Claude Desktop (toggle connector or restart app)
- [ ] 6. Soak test: 2-3 fileops calls, >= 10 min idle, call get_lock_status.
        Pass = instant return. Repeat once. Previously dead within ~3-9 min.
- [ ] 7. If it still wedges on 3.4.3+ without tasks: pin fastmcp==3.3.1,
        uv sync, re-soak; then file upstream issue (cleanest timeline:
        Jul 6 11:00-11:08Z window in
        C:\Users\sandr\AppData\Roaming\Claude\logs\mcp-server-fileops.log).
- [ ] 8. CHANGELOG.md + CHANGELOG_LATEST.md, bump 2.2.1, `just release`
        once soak is green.

## Fleet follow-ups (separate tasks)

- [ ] Audit fleet lockfiles for fastmcp 3.4.2 and unused [tasks] extras.
      Candidates first: winops, memops, gitops (same historical hang lore).
      `Get-ChildItem D:\Dev\repos -Recurse -Filter uv.lock -Depth 2 | Select-String 'version = "3.4.2"' -List`
- [ ] Update hang lore in mcp-central-docs (TRAPS_AND_PITFALLS.md Trap-6
      area): "stale asyncio lock state" superseded — lock table verified
      empty during a live wedge. New first checks: FastMCP version, tasks
      extra, ping-loop wedge. Restart is recovery, not diagnosis.
- [ ] Identify which client launches filesystem_mcp with SYSTEM Python
      (C:\Users\sandr\AppData\Local\Programs\Python\Python313\python.exe,
      cwd C:\Users\sandr, seen 2026-07-06 11:13Z, stdio, pings only — not
      the wedge cause, but a config smell; system Python lacks venv deps).
      Check C:\Users\sandr\.gemini\antigravity, LM Studio MCP config,
      Cursor/Windsurf configs; repoint to repo venv python.
- [ ] Optional hardening: asyncio.wait_for wrapper around portmanteau
      dispatch so a stuck op errors out instead of killing the server
      (defense in depth, not the root fix).

## Key paths

- Repo: D:\Dev\repos\filesystem-mcp
- Client log: C:\Users\sandr\AppData\Roaming\Claude\logs\mcp-server-fileops.log
- Server log: D:\Dev\repos\filesystem-mcp\logs\filesystem_mcp.log
  (shared by ALL instances incl. the foreign system-Python one; stray 0x97
  byte ~line 208250 — grep with latin-1)
- Claude config: `fileops` entry in
  C:\Users\sandr\AppData\Roaming\Claude\claude_desktop_config.json

Tags: [filesystem-mcp, fastmcp, bug, fix, critical]
