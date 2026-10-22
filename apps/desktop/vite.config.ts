import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The Vite dev server proxies /api to the local FastAPI backend.
// In production the Electron main process serves the built assets
// and either spawns the backend or expects it on 127.0.0.1:8787.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    // Allow the Arena preview host (a *.e2b.app subdomain)
    // plus local hosts.  The dev server only proxies to the
    // local backend, so this stays safe.
    allowedHosts: [".e2b.app", "localhost", "127.0.0.1"],
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8787",
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
    css: false,
  },
});
