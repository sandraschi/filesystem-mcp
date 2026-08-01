# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.1] - 2026-08-01

### Added
- `server_shutdown` tool (DESTRUCTIVE, confirm=True guard) for graceful self-termination
- REST endpoints: `GET /api/status`, `GET /api/capabilities`, `GET /api/skills`, `GET /api/llm/discover`
- CORS middleware on the MCP HTTP app (tauri origins + Tailscale + LAN regex) — fixes
  cross-origin "Failed to fetch" in the Tauri WebView and LAN access
- `/api/v1/diagnostics` now reports the real registered tool list (was hardcoded 0)
- Dashboard rewrite: hero section, live backend/LLM KPIs with data-testids, working
  quick actions (was hardcoded fake stats with dead buttons)
- Chat upgrade: localStorage history (100-msg cap), 4 personalities, example prompts,
  export/clear, skill-first system prompt, bridge-proxy LLM calls with tool forwarding,
  `?context=` workflow presets from the Apps page
- Settings: auto-detection of Ollama/LM Studio with status badges, `llm-provider-select`
  / `llm-model-select` testids, GPU opportunity banner, `llm_provider`/`llm_model` keys
- Session-context injection: `.claude-plugin` hooks, `.cursorrules` section,
  `.windsurfrules`, `.github/copilot-instructions.md`, `.opencode/skills/`
- `## Return Format` + `## Examples` docstring sections on all 24 tools (Args: vanished)
- MCPB prompts: `system.md` 3000+ words, `user.md` 4000+ words (was 25/339 runt)
- Canonical docs: `docs/CONFIGURATION.md`, `docs/DEVELOPMENT.md`, `docs/TOOLS.md`, `docs/TROUBLESHOOTING.md`
- Playwright e2e audit (`webapp/e2e/fleet-audit.spec.ts`) + `webapp/playwright.config.ts`
- `webapp` `typecheck` script so CI's TS gate actually executes
- `renovate.json` (fleet dep auto-bump); `serve`/`fmt`/`certify` just recipes
- Coverage config in pytest.ini (`--cov-fail-under=50`)

### Changed
- `transport.py` uses `uvicorn.Server` on `mcp.http_app()` instead of `run_http_async()`
  (which dropped CORSMiddleware)
- LLM chat now proxies through the bridge `POST /api/llm/chat` (tools forwarded)
- Dev tooling moved to `[dependency-groups] dev` (ruff/pytest/pre-commit/pyright) so
  fleet CI's `uv run ruff` resolves
- `.gitignore`: `reports/`, `mcpb/`, `*.mcpb`, `*.bak-*`, `webapp/dist/`, `gen/`
- `llms.txt` rewritten (llms-full.txt link, no mojibake); README stack section + port fix
- Removed stale manifests (`manifest.json` fake Node entry, `mcpb.json`,
  `mcpb_manifest.json` 74-tool ghost list) — pack script regenerates
- Untracked `mcpb/` legacy duplicate (prompts now canonical in `assets/prompts/`)
- Biome config migrated to v2; repo-root `biome.json` config reconciled

### Fixed
- GitHub Actions was disabled on the repo (`actions/permissions.enabled=false`) —
  enabled; CI now runs on the reusable `sandraschi/fleet-ci` hybrid workflow
- **Webapp MCP connection was broken**: the frontend spoke legacy SSE while FastMCP 3.4
  only serves Streamable HTTP — rewrote `mcp-client.ts` to the streamable protocol
  (initialize → notifications/initialized → tools/list with Mcp-Session-Id)
- CORS: `expose_headers` now includes `mcp-session-id` — without it the browser could
  not read the session header cross-origin (webapp → 127.0.0.1:10742), so every MCP
  call after initialize failed with "Missing session ID"
- `server.py` now uses the module-level `http_app()` (was calling the FastMCP instance
  method, which never included the appended routes — `/api/v1/diagnostics` and friends
  404'd under real uvicorn)
- `run_server.py` was calling `uvicorn.run` without importing uvicorn (F821) — fixed
- `console.log` removed from production JS
- Dead `href="#"` links on Tools page; "(Mock)" apps replaced with real chat presets
- Low-contrast/`text-xs` UI text bumped where unjustified

## [Unreleased] — 2026-07-06

### Fixed
- `_kill_orphaned_stdio()` startup guard: on launch, kills any stale filesystem_mcp stdio
  processes from previous CD sessions while preserving the HTTP daemon (port 10742).
  Prevents Claude Desktop hangs from orphaned stdio processes accumulating across reconnects.

### Changed
- README.md: synced tool count and transport architecture description.
- MCD project page: synced FastMCP version and added reliability note.

### Added
- Tauri 2.0 native wrapper with `bundle.resources` + `std::process::Command`
- PyInstaller frozen backend embedded in NSIS installer
- CUA-NSIS smoke test (`scripts/cua-smoke.py`, `scripts/cua-nsis-config.json`)
- `just cua-nsis-test` recipe
- Tauri CORS: `tauri://localhost` origins for WebView API access
- `GET /api/v1/diagnostics` endpoint for CUA verification

## [2.2.0] - 2026-06-11

### Fixed — head_file / tail_file on large or mixed-encoding files

Tailing real Windows logs (e.g. 10MB Claude Desktop MCP logs containing
mixed UTF-8/cp1252 bytes) failed hard: both operations did a strict
`read_text()` of the **entire file**, so a single bad byte anywhere — at
position 503845 in a 10-line tail request — aborted the read, and every
tail cost O(file size) in time and memory.

- `tail_file`: rewritten as a backwards block read from EOF (8KB blocks,
  stop after `lines + 1` newlines), decoding only the tail bytes with
  `errors="replace"`. O(tail size) regardless of file size.
- `head_file`: now streams line-by-line with `errors="replace"` and stops
  after N lines instead of slurping the file.
- `total_lines` in the response is now `None` when not counted (counting
  would require reading the whole file, defeating head/tail). `head_file`
  still reports it when the file was fully consumed.

Verified against the failing 10.4MB `mcp-server-memops1.log` on Goliath
(utf-8 default now succeeds; previously required latin-1 workaround).

### Changed
- **FastMCP 3.2+ Upgrade**: Updated FastMCP dependency from 2.14.4+ to 3.2.0 for universal connect pattern support
- **Concurrency Safety**: Implemented atomic file operations with proper locking for multi-client access
- **Documentation**: Updated FastMCP version references throughout README and documentation

### Added
- **Universal Connect Pattern**: Support for multiple simultaneous clients via stdio and HTTP transports
- **Atomic File Operations**: New `file_ops_safe` tool with atomic write patterns preventing corruption
- **File Locking System**: Comprehensive locking mechanism for file and directory operations
- **Concurrency Testing**: Built-in testing tools for multi-client operation validation
- **FastMCP 3.2 Features**: Access to new 3.2 functionality including codemode, prefabs, app providers, and transforms

### Fixed
- **File Corruption Risk**: Eliminated race conditions in concurrent file operations
- **Multi-Client Access**: Safe simultaneous access to same files from multiple clients
- **Version References**: Updated all FastMCP 2.14.4+ references to 3.2+ in documentation and badges
- **Dependency Resolution**: Ensured compatibility with latest FastMCP 3.2.0 features

### Security
- **Atomic Writes**: All file write operations use temporary file patterns with verification
- **Lock Timeouts**: 30-second timeout prevents deadlocks in concurrent scenarios
- **Queue Management**: FIFO queue for waiting operations prevents resource starvation

## [2.1.0] - 2026-02-27

### Fixed
- **Windows path compatibility in edit_file**: `file_ops(edit_file)` now accepts both
  `old_string`/`new_string` (canonical) and `old_str`/`new_str` (alias) parameter names.
  This resolves a Pydantic validation error that occurred when Claude's built-in `str_replace`
  tool tried to call `file_ops` with the alias names, causing all str_replace operations on
  Windows paths (`D:\`, `C:\`) to fail with "unexpected keyword argument" errors.
  The alias resolution happens at dispatch time before any path handling, so both call
  styles now work identically.

## [2.0.0] - 2025-12-25

### Added
- **Major Tool Expansion**: Added 10+ advanced file operations tools (57+ total tools)
  - `find_large_files` - Large file detection for disk management
  - `find_duplicate_files` - Content-based duplicate file detection
  - `find_empty_directories` - Empty directory cleanup
  - `compare_files` - File diff comparison with unified format
  - `read_multiple_files` - Batch file reading operations
  - `move_file` - File/directory moving with overwrite control
  - `read_file_lines` - Precise line-based file reading
  - `search_files` - Advanced recursive file search with patterns
  - `directory_tree` - Visual directory tree representation
  - `calculate_directory_size` - Directory size calculation with statistics

- **MCPB Packaging**: Professional drag-and-drop installation for Claude Desktop
  - Complete MCPB manifest with user configuration
  - Extensive prompt templates for AI integration
  - Clean package structure without bundled dependencies
  - Professional build scripts and CI/CD integration

- **Enhanced Prompt Templates**: Comprehensive AI integration templates
  - `system.md` - System-level Claude Desktop instructions
  - `user.md` - User interaction guide with examples
  - `examples.json` - Structured tool usage examples
  - `quick-start.md` - 5-minute getting started guide
  - `configuration.md` - Detailed configuration options
  - `troubleshooting.md` - Comprehensive troubleshooting guide

### Changed
- **FastMCP Upgrade**: Migrated from FastMCP 2.12.0 to 2.14.1+
- **Packaging Migration**: Complete transition from DXT to MCPB format
- **Installation Method**: MCPB drag-and-drop now primary installation method
- **Dependencies**: MCPB packages no longer bundle dependencies (installed separately)
- **Documentation**: Updated installation instructions and feature descriptions

### Fixed
- Manifest validation errors in MCPB packaging
- Broken symlinks in development environment
- Package build process optimizations

### Security
- Updated author information and contact details
- Maintained secure path validation and permission checks
- Enhanced audit logging capabilities

## [1.0.0] - 2024-05-20

### Added
- Initial release of Filesystem MCP
- **File System Operations**:
  - Read, write, and manage files and directories
  - List directory contents with detailed metadata
  - Recursive directory scanning
  - File content analysis

- **Docker Container Management**:
  - Container lifecycle management (create, start, stop, remove)
  - Image management (list, pull, build, remove)
  - Network and volume management
  - Docker Compose support
  - Container execution and log streaming

- **Git Repository Management**:
  - Clone repositories with branch and depth control
  - Repository status and commit management
  - Repository structure inspection

- **Developer Experience**:
  - Comprehensive API documentation
  - Type hints throughout the codebase
  - Unit and integration tests
  - CI/CD pipeline with GitHub Actions
  - Pre-commit hooks for code quality

### Changed
- Project structure optimized for FastMCP 2.10 compatibility
- Improved error handling and validation
- Enhanced security with secure path handling

### Fixed
- Various bug fixes and stability improvements

### Security
- Implemented secure path validation
- Added input sanitization
- Improved error messages to prevent information leakage

## [0.1.0] - 2024-05-01
### Added
- Initial project setup
- Basic file system operations
- Git repository management foundation
