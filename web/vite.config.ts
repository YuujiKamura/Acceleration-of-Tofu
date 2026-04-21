import { defineConfig } from "vite";

// base "./" so the built assets resolve under any GitHub Pages subpath.
export default defineConfig({
  base: "./",
  server: {
    port: 5173,
    host: true,
  },
  build: {
    target: "es2022",
    outDir: "dist",
    assetsDir: "assets",
    sourcemap: true,
  },
});
