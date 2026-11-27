import { expect, test, type Page } from "@playwright/test";

import type { AutomaticSyncPlanList, LegacyNamingMigration, NamingLegacyContext } from "../src/types";

const browserErrors = new WeakMap<Page, string[]>();
const emptyPlans: AutomaticSyncPlanList = { plans: [], revision: "empty-project", next_runs: {} };
const noLegacyMigration: LegacyNamingMigration = {
  pending: false,
  project_revision: "empty-project",
  sources: [],
  fields: [],
  ignored_environment_keys: [],
};
const noLegacyContext: NamingLegacyContext = { roots: [], conversion_pending: false };
const emptyResponses: Record<string, unknown> = {
  "/tasks": [],
  "/creators": [],
  "/auto-sync/plans": emptyPlans,
  "/auto-sync/runs": [],
  "/auto-sync/updates": [],
  "/naming/conversions": [],
  "/naming/layout-versions": [],
  "/naming/legacy-migration": noLegacyMigration,
  "/naming/legacy-context": noLegacyContext,
  "/startup-notices": [],
  "/mcp/tokens": [],
};

test.use({ viewport: { width: 1440, height: 1000 } });
test.describe.configure({ timeout: 45_000 });

test.beforeEach(async ({ context, page }) => {
  const errors: string[] = [];
  browserErrors.set(page, errors);
  page.on("crash", () => errors.push("renderer crashed"));
  page.on("pageerror", (error) => errors.push(`page: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  page.on("response", (response) => {
    if (response.status() >= 500) errors.push(`response: ${response.status()} ${response.url()}`);
  });

  // Keep the real application, authentication, and SSE connection, but exercise
  // empty data states independently of records created by other browser tests.
  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname.replace(/^\/api\/v1/u, "");
    if (route.request().method() === "GET" && Object.hasOwn(emptyResponses, path)) {
      await route.fulfill({ json: emptyResponses[path] });
      return;
    }
    await route.continue();
  });

  const response = await context.request.post("/api/v1/session/login", {
    data: { username: "playwright", password: "fixture-password" },
  });
  expect(response.ok()).toBe(true);
});

test.afterEach(({ page }) => {
  expect(browserErrors.get(page)).toEqual([]);
});

async function remainResponsive(page: Page) {
  // Issue #395 failed 2–6 seconds after rendering. Immediate visibility checks
  // miss that failure, so keep the production page idle beyond that window.
  await page.waitForTimeout(8_000);
  expect(browserErrors.get(page)).toEqual([]);
  await page.getByRole("link", { name: "Overview", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Overview", level: 1 })).toBeVisible();
}

test("direct navigation to an empty task queue keeps the renderer responsive", async ({ page }) => {
  await page.goto("/tasks");
  await expect(page.getByRole("heading", { name: "Tasks", level: 1 })).toBeVisible();
  await expect(page.getByText("The task queue is empty", { exact: true })).toBeVisible();
  await remainResponsive(page);
});

const dataPages = [
  { path: "/tasks", name: "Tasks", emptyText: "The task queue is empty" },
  { path: "/auto-sync", name: "Automatic sync", emptyText: "No automatic sync plans" },
  { path: "/creators", name: "Creators", emptyText: "No creators are saved" },
  { path: "/posts", name: "Posts", emptyText: "Ready to search Pawchive" },
  { path: "/naming", name: "Naming format", emptyText: null },
  { path: "/mcp", name: "MCP", emptyText: "No MCP access tokens" },
] as const;

for (const dataPage of dataPages) {
  test(`sidebar navigation to ${dataPage.name} remains responsive with empty data`, async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Overview", level: 1 })).toBeVisible();
    await page.getByRole("link", { name: dataPage.name, exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`${dataPage.path}$`, "u"));
    await expect(page.getByRole("heading", { name: dataPage.name, level: 1 })).toBeVisible();
    if (dataPage.emptyText) {
      await expect(page.getByText(dataPage.emptyText, { exact: true })).toBeVisible();
    } else {
      await expect(page.getByRole("tab", { name: "Directory structure", exact: true })).toBeVisible();
    }
    await remainResponsive(page);
  });
}
