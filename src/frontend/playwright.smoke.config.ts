import { defineConfig, devices } from '@playwright/test';

// UI smoke test against live services (#213). Run via `just smoke` / scripts/ui_smoke.py,
// which starts the backend and the UIs; this config deliberately has no webServer.
const out = process.env.SMOKE_OUT ?? '../../tmp/debug/smoke';

export default defineConfig({
  testDir: './smoke',
  timeout: 240_000,
  expect: { timeout: 30_000 },
  workers: 1,
  retries: 0,
  reporter: [['list']],
  outputDir: `${out}/artifacts`,
  use: {
    ...devices['Desktop Chrome'],
    viewport: { width: 1600, height: 900 },
    trace: 'retain-on-failure',
  },
});
