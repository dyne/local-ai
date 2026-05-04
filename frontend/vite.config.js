import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

const backendUrl = process.env.LOCAL_AI_BACKEND_URL || `http://127.0.0.1:${process.env.LOCAL_AI_BACKEND_PORT || "8000"}`;
const backendWsUrl = backendUrl.replace(/^http/, "ws");

export default defineConfig({
  plugins: [svelte()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api/app": backendUrl,
      "/session": backendUrl,
      "/events": backendUrl,
      "/audio": {
        target: backendWsUrl,
        ws: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.js"],
  },
});
