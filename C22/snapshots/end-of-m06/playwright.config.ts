// One end-to-end flow in a real browser, against the production build and the mock API.
//   npx playwright install chromium   (once: downloads the browser)
//   npm run test:e2e
// Ports: E2E_API_PORT (8100) and E2E_WEB_PORT (4173), if those are busy on your computer.
import { defineConfig, devices } from '@playwright/test';

const apiPort = Number(process.env.E2E_API_PORT ?? 8100);
const webPort = Number(process.env.E2E_WEB_PORT ?? 4173);
const web = `http://localhost:${webPort}`;

export default defineConfig({
  testDir: 'e2e',
  timeout: 60_000,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: { baseURL: web, trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'phone', use: { ...devices['Pixel 7'] } },
  ],
  webServer: [
    {
      command: `node mock-api/server.mjs --size small --port ${apiPort}`,
      url: `http://127.0.0.1:${apiPort}/health`,
      env: { CORS_ORIGINS: web, MOCK_LOG: '0' },
      reuseExistingServer: false,
    },
    {
      command: `npx vite build && npx vite preview --port ${webPort} --strictPort`,
      url: web,
      env: { VITE_API_URL: `http://127.0.0.1:${apiPort}` },
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
