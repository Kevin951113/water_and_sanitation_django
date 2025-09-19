import { defineConfig } from "vite";

export default defineConfig({
  base: "/static/treasure/",        // Django will serve from STATIC_URL/treasure/
  build: {
    outDir: "../static/treasure",   // relative to this vite.config.js
    emptyOutDir: true,
    manifest: true
  }
});