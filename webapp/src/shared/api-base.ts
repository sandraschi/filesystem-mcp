/**
 * Backend origin for REST calls.
 * Browser tabs: "" (relative, same-origin; the Vite dev proxy forwards
 * /api and /mcp to the backend, and any LAN/Tailscale hostname keeps working).
 * Tauri WebView only: absolute 127.0.0.1, because the built dist has no proxy.
 * Must match BackendPort in fleet-start.config.ps1.
 */
const BACKEND_PORT = 10742;

export function isTauri(): boolean {
  if (typeof window === "undefined") return false;
  return "__TAURI__" in window || "__TAURI_INTERNALS__" in window;
}

export const API_BASE: string = isTauri() ? `http://127.0.0.1:${BACKEND_PORT}` : "";
