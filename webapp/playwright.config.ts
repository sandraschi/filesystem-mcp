import { defineConfig } from "@playwright/test";

const BACKEND_PORT = 10742;
const FRONTEND_PORT = 10743;

export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  retries: 1,
  use: {
    baseURL: `http://127.0.0.1:${FRONTEND_PORT}`,
    headless: true,
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: `uv run uvicorn filesystem_mcp.server:app --host 127.0.0.1 --port ${BACKEND_PORT} --log-level warning`,
      port: BACKEND_PORT,
      cwd: "../",
      timeout: 30000,
      reuseExistingServer: false,
    },
    {
      command: `npx vite --port ${FRONTEND_PORT} --host 127.0.0.1 --strictPort`,
      port: FRONTEND_PORT,
      cwd: ".",
      timeout: 30000,
      reuseExistingServer: false,
    },
  ],
});
