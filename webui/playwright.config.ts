import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://127.0.0.1:8791",
    colorScheme: "light",
    locale: "en-US",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "poetry run uvicorn tests.webui_e2e_server:app --host 127.0.0.1 --port 8791",
    cwd: "..",
    reuseExistingServer: false,
    timeout: 120_000,
    url: "http://127.0.0.1:8791/api/v1/health",
  },
});
