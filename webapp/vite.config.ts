import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 10743,
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
