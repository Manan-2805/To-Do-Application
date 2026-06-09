import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60000,
  expect: {
    timeout: 5000,
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 2,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://localhost:8080",
    actionTimeout: 0,
    trace: "on-first-retry",
    headless: !process.env.CI ? false : process.env.HEADLESS !== "false",
    launchOptions: {
      slowMo: !process.env.CI ? 500 : process.env.SLOWMO ? parseInt(process.env.SLOWMO, 10) : 0,
    },
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
});
