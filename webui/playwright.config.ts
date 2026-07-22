import { defineConfig } from "@playwright/test";

const e2ePort = process.env.KTOOLBOX_E2E_PORT ?? "8792";
const e2ePython = process.env.KTOOLBOX_E2E_PYTHON ?? "poetry run python";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: `http://127.0.0.1:${e2ePort}`,
    colorScheme: "light",
    locale: "en-US",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command: `${e2ePython} -m uvicorn tests.webui_e2e_server:app --host 127.0.0.1 --port ${e2ePort}`,
    cwd: "..",
    reuseExistingServer: false,
    timeout: 120_000,
    url: `http://127.0.0.1:${e2ePort}/api/v1/health`,
  },
});
