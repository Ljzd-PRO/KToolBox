import { expect, test, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { join } from "node:path";

const browserErrors = new WeakMap<Page, string[]>();
const realtimeAuditDirectory = process.env.KTOOLBOX_REALTIME_AUDIT_DIR;

test.beforeEach(({ page }) => {
  const errors: string[] = [];
  browserErrors.set(page, errors);
  page.on("pageerror", (error) => errors.push(`page: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  page.on("response", (response) => {
    if (response.status() >= 500) errors.push(`response: ${response.status()} ${response.url()}`);
  });
});

test.afterEach(({ page }) => {
  expect(browserErrors.get(page)).toEqual([]);
});

async function signIn(page: Page, allowedErrorFragments: string[] = []) {
  await page.goto("/");
  await page.getByLabel("Username").fill("playwright");
  await page.getByLabel("Password", { exact: true }).fill("fixture-password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Overview", exact: true })).toBeVisible();
  const errors = browserErrors.get(page) ?? [];
  expect(
    errors.filter(
      (error) =>
        !error.includes("status of 401 (Unauthorized)") &&
        !allowedErrorFragments.some((fragment) => error.includes(fragment)),
    ),
  ).toEqual([]);
  errors.length = 0;
}

async function csrf(page: Page): Promise<string> {
  const response = await page.request.get("/api/v1/session");
  expect(response.ok()).toBe(true);
  return String((await response.json()).csrf_token);
}

function headers(token: string) {
  return { "X-CSRF-Token": token };
}

test("local resources synchronize between two tabs without manual refresh", async ({ page }) => {
  await signIn(page);
  const runId = Date.now().toString(36);
  const observer = await page.context().newPage();
  browserErrors.set(observer, []);
  observer.on("pageerror", (error) => browserErrors.get(observer)?.push(`page: ${error.message}`));
  observer.on("console", (message) => {
    if (message.type() === "error") browserErrors.get(observer)?.push(`console: ${message.text()}`);
  });
  const csrfToken = await csrf(page);

  await observer.goto("/creators");
  await expect(observer.getByRole("rowheader", { name: "Demo Studio" })).toBeVisible();
  const creatorId = `realtime-${runId}`;
  const creator = {
    service: "fanbox",
    creator_id: creatorId,
    alias: null,
    enabled: true,
  };
  const creatorResponse = await page.request.post("/api/v1/creators", {
    data: creator,
    headers: headers(csrfToken),
  });
  expect(creatorResponse.status()).toBe(201);
  await expect(observer.getByText(creatorId, { exact: true }).first()).toBeVisible({
    timeout: 1000,
  });

  await observer.goto("/blockers");
  const blockerResponse = await page.request.get("/api/v1/blockers");
  const blockerPayload = await blockerResponse.json();
  const blockerId = `realtime-${runId}-rule`;
  blockerPayload.blockers.push({
    id: blockerId,
    type: "field-match",
    enabled: true,
    scope: { mode: "global", creators: [] },
    options: {
      rule: {
        kind: "group",
        mode: "any",
        negate: false,
        conditions: [{
          kind: "field",
          field: "title",
          operator: "contains",
          values: ["fictional"],
          expected: true,
          case_sensitive: false,
          negate: false,
        }],
      },
    },
  });
  const savedBlockers = await page.request.put("/api/v1/blockers", {
    data: blockerPayload.blockers,
    headers: headers(csrfToken),
  });
  expect(savedBlockers.ok()).toBe(true);
  await expect(observer.getByRole("heading", { name: blockerId })).toBeVisible({
    timeout: 1000,
  });

  let dotenvReads = 0;
  observer.on("response", (response) => {
    if (
      response.request().method() === "GET" &&
      response.url().endsWith("/api/v1/config/dotenv/dotenv")
    ) {
      dotenvReads += 1;
    }
  });
  await observer.goto("/configuration");
  await expect.poll(() => dotenvReads).toBeGreaterThan(0);
  const readsBeforePatch = dotenvReads;
  const dotenv = await page.request.get("/api/v1/config/dotenv/dotenv");
  const patched = await page.request.patch("/api/v1/config/dotenv/dotenv", {
    data: { values: { KTOOLBOX_JOB__COUNT: "5" } },
    headers: {
      ...headers(csrfToken),
      "If-Match": dotenv.headers()["etag"],
    },
  });
  expect(patched.ok()).toBe(true);
  await expect.poll(() => dotenvReads, { timeout: 1000 }).toBeGreaterThan(readsBeforePatch);

  await observer.goto("/mcp");
  const tokenName = `realtime-${runId}-token`;
  const tokenResponse = await page.request.post("/api/v1/mcp/tokens", {
    data: {
      name: tokenName,
      password: "fixture-password",
      permission: "read",
      expires_in_days: 7,
    },
    headers: headers(csrfToken),
  });
  expect(tokenResponse.status()).toBe(201);
  await expect(observer.getByText(tokenName, { exact: true }).first()).toBeVisible({
    timeout: 1000,
  });

  await observer.goto("/tasks");
  const taskResponse = await page.request.post("/api/v1/tasks", {
    data: {
      spec: {
        kind: "download",
        post: null,
        service: "fanbox",
        creator_id: creatorId,
        post_id: `work-${runId}`,
        revision_id: null,
        output: "realtime-task",
        dump_post_data: true,
      },
    },
    headers: headers(csrfToken),
  });
  expect(taskResponse.status()).toBe(201);
  await expect(observer.getByText(new RegExp(`work-${runId}`)).first()).toBeVisible({
    timeout: 1000,
  });

  await observer.getByRole("button", { name: "Create task" }).click();
  const taskDialog = observer.getByRole("dialog", { name: "Create task" });
  await taskDialog
    .getByRole("button", { name: "Browse the remote computer for Output directory" })
    .click();
  const picker = observer.getByRole("dialog", { name: "Output directory" });
  await expect(picker).toBeVisible();
  const currentPath = await picker.getByRole("textbox", { name: "Remote path" }).inputValue();
  const folderName = `realtime-${runId}-folder`;
  const directoryResponse = await page.request.post("/api/v1/filesystem/directories", {
    data: { scope: "project", parent: currentPath, name: folderName },
    headers: headers(csrfToken),
  });
  expect(directoryResponse.status()).toBe(201);
  await expect(picker.getByRole("option", { name: folderName })).toBeVisible({ timeout: 1000 });

  const createdDirectory = await directoryResponse.json();
  await page.request.delete("/api/v1/filesystem/directories", {
    data: { scope: "project", path: createdDirectory.path },
    headers: headers(csrfToken),
  });
  await expect(picker.getByRole("option", { name: folderName })).toHaveCount(0, { timeout: 1000 });

  expect(browserErrors.get(observer)).toEqual([]);
  await observer.close();
});

test("SSE failure falls back to local polling and recovers without remote queries", async ({
  page,
}) => {
  let localTaskReads = 0;
  let remoteReads = 0;
  page.on("request", (request) => {
    const url = request.url();
    if (request.method() === "GET" && url.endsWith("/api/v1/tasks")) localTaskReads += 1;
    if (url.includes("/api/v1/pawchive/") || url.endsWith("/api/v1/site-version")) {
      remoteReads += 1;
    }
  });
  await page.route("**/api/v1/events*", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "intentional realtime test outage" }),
    }),
  );

  await signIn(page, ["503", "Failed to load resource"]);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => localStorage.setItem("ktoolbox-theme", "dark"));
  await page.reload();
  const taskReadsBeforeFallback = localTaskReads;
  const remoteReadsBeforeFallback = remoteReads;
  const degradedControl = page.getByRole("button", {
    name: "Fallback refresh. Reconnect",
  });
  await expect(degradedControl).toBeVisible({ timeout: 7000 });

  await expect.poll(() => localTaskReads, { timeout: 12_000 }).toBeGreaterThan(
    taskReadsBeforeFallback,
  );
  expect(remoteReads).toBe(remoteReadsBeforeFallback);

  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "System", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Navigation" })).toBeHidden();
  await page.waitForTimeout(450);
  await expect(page.getByRole("heading", { name: "Live updates" })).toBeVisible();
  await expect(page.getByText("10-second fallback refresh", { exact: true })).toBeVisible();
  await expect
    .poll(() =>
      page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      ),
    )
    .toBe(0);
  if (realtimeAuditDirectory) {
    await mkdir(realtimeAuditDirectory, { recursive: true });
    await page.screenshot({
      fullPage: true,
      path: join(realtimeAuditDirectory, "system__390x844__dark__fallback.png"),
    });
  }

  const outageErrors = browserErrors.get(page) ?? [];
  expect(
    outageErrors.every(
      (error) =>
        error.includes("503") ||
        error.includes("Failed to load resource") ||
        error.includes("ERR_FAILED"),
    ),
  ).toBe(true);
  outageErrors.length = 0;

  await page.unroute("**/api/v1/events*");
  await degradedControl.click();
  await expect(degradedControl).toBeHidden({ timeout: 5000 });
  await expect(page.getByText("Server-sent events", { exact: true }).first()).toBeVisible();
});

test("captures the responsive live-update status matrix", async ({ page }) => {
  test.skip(
    !realtimeAuditDirectory,
    "Set KTOOLBOX_REALTIME_AUDIT_DIR to capture the live-update visual matrix.",
  );
  if (!realtimeAuditDirectory) return;
  await mkdir(realtimeAuditDirectory, { recursive: true });
  await signIn(page);

  const viewports = [
    { id: "1440x900", width: 1440, height: 900 },
    { id: "1024x768", width: 1024, height: 768 },
    { id: "390x844", width: 390, height: 844 },
  ] as const;
  const themes = ["light", "dark"] as const;

  for (const viewport of viewports) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    for (const theme of themes) {
      await page.evaluate(
        (nextTheme) => localStorage.setItem("ktoolbox-theme", nextTheme),
        theme,
      );
      await page.goto("/system");
      await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
      await expect(page.getByRole("heading", { name: "Live updates" })).toBeVisible();
      await expect(page.getByText("Server-sent events", { exact: true }).first()).toBeVisible();
      await expect
        .poll(() =>
          page.evaluate(
            () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
          ),
        )
        .toBe(0);
      await page.screenshot({
        fullPage: true,
        path: join(
          realtimeAuditDirectory,
          `system__${viewport.id}__${theme}__connected.png`,
        ),
      });
    }
  }
});
