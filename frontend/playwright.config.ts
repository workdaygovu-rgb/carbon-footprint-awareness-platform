import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E configuration. Starts both backend and frontend dev servers
 * and runs browser tests against the full stack in offline mode (no Gemini,
 * no Firestore) so tests are deterministic and credential-free.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: 1,
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      // Backend: FastAPI in offline mode (rules engine + in-memory store).
      command: "cd ../backend && uvicorn app.main:app --port 8000",
      port: 8000,
      reuseExistingServer: true,
      env: {
        USE_GEMINI: "false",
        USE_FIRESTORE: "false",
      },
    },
    {
      // Frontend: Vite dev server (proxies /api to the backend).
      command: "npm run dev",
      port: 5173,
      reuseExistingServer: true,
    },
  ],
});
