import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// `vite build --mode profile` builds the production code with React's profiling build, so that
// the React DevTools Profiler (and <Profiler>) can measure a production build.
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  resolve: mode === 'profile' ? { alias: { 'react-dom/client': 'react-dom/profiling' } } : {},
  server: { port: 5173, strictPort: true },
  preview: { port: 4173, strictPort: true },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
    setupFiles: ['src/test/setup.ts'],
  },
}));
