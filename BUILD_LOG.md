

## 2026-10-06 - NSIS build (0.1.0), first release build

Output: `native/target/release/bundle/nsis/Filesystem MCP_0.1.0_x64-setup.exe` (36.7 MB), also staged to `dist/`. Backend 34.4 MB, frozen-binary smoke test PASSED.
Built from a dirty working tree (other uncommitted WIP in `src/`); installer contains that code.

Phase 1 audit (TAURI_PRODUCTION_PITFALLS A-J) fixes:

| Gap | Fix |
|-----|-----|
| Spec `noarchive=False`, `upx=True` | `noarchive=True`, `upx=False` |
| Spec missing `_strptime/_datetime/cachetools/joserfc*/mcp.types/key_value` | Added to hiddenimports |
| `run_server.py` no eager stdlib/mcp imports | Added `_datetime`, `_strptime`, `mcp.types` |
| `backend.rs` bare-name resolve first (#19) | `resources/` first |
| `backend.rs` blind port-PID kill (sec 15) | Image-scoped `taskkill /IM`; attach to responsive holder via `/health` |
| `main.rs` backend not killed on `ExitRequested` | Added, plus `wait()` |
| 3 relative `/api/...` fetches (chat.tsx, settings.tsx) break in WebView | `API_BASE` (`webapp/src/shared/api-base.ts`): absolute in PROD, relative in dev |
| TS6133 in `mcp-client.ts` blocked the tsc gate | Removed dead `isProduction`, `_expectResult` |

Not fixed: operator port == dev port (10742), violates side-by-side rule (needs claim_ports.py). Not run: CUA NSIS smoke test (no `cua-nsis-test` recipe in justfile; scripts exist; dev backend PID holds 10742), installed-app verify (sec M).
