import { defineConfig } from 'vitest/config';

// Vite serves the page while you work (npm run dev) and builds the files for production (npm run build).
// Vitest runs the tests in src/ (npm test).
export default defineConfig({
  server: { port: 5173, strictPort: true },
  preview: { port: 4173, strictPort: true },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
});
