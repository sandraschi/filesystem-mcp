import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      external: ["@tauri-apps/api/event", "@tauri-apps/api/window"],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    allowedHosts: ['goliath'],
    port: 10743,
    strictPort: true,
    host: true,
    proxy: {
      "/mcp": {
        target: "http://localhost:10742",
        changeOrigin: true,
        ws: true,
      },
      "/api": {
        target: "http://localhost:10742",
        changeOrigin: true,
      },
    },
  },
});
