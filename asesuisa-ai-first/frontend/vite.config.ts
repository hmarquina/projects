import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Destino del proxy en desarrollo (`npm run dev`); debe coincidir con APP_PORT del backend.
const api = process.env.API_URL ?? "http://127.0.0.1:8765";
const prefixes = ["/auth", "/initiatives", "/pipeline-runs", "/releases", "/metrics", "/audit", "/health"];

export default defineConfig({
  plugins: [react()],
  server: { proxy: Object.fromEntries(prefixes.map((p) => [p, api])) },
  test: { environment: "jsdom", globals: true, setupFiles: ["./src/test/setup.ts"], css: false },
});
