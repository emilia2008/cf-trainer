import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // During development, forward /api calls to the FastAPI backend.
    proxy: { "/api": process.env.VITE_PROXY_TARGET ?? "http://localhost:8000" },
  },
  build: {
    rollupOptions: {
      output: {
        // Libraries change far less often than app code: separate files cache better.
        manualChunks(id) {
          if (!id.includes("node_modules")) return undefined;
          if (/node_modules[\\/](react|react-dom|scheduler)[\\/]/.test(id)) return "react";
          return "vendor"; // recharts and its dependencies (d3, redux, ...)
        },
      },
    },
  },
});
