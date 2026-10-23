import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The Python server serves dist/ and the API on the same address, so the pages use relative paths.
// `npm run dev` sends /api to a running inspector (python -m larkfield_inspector --no-browser).
export default defineConfig({
  base: "./",
  plugins: [react()],
  build: { outDir: "dist", emptyOutDir: true, sourcemap: false },
  server: { proxy: { "/api": "http://127.0.0.1:8318" } },
});
