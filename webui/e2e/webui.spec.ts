import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { join } from "node:path";

const browserErrors = new WeakMap<Page, string[]>();
const legacyChineseTerms = new RegExp([
  "\u6295\u7a3f",
  "\u5e16\u5b50",
  "\u5c4f\u853d\u5668",
  "\u4e00\u89c8\u4e0b\u8f7d\u8fd0\u884c\u72b6\u6001",
  "\u5168\u90e8\u542f\u7528\u4f5c\u8005",
].join("|"));

test.beforeEach(({ page }) => {
  const errors: string[] = [];
  browserErrors.set(page, errors);
  page.on("pageerror", (error) => errors.push(`page: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  page.on("requestfailed", (request) => {
    const failure = request.failure()?.errorText ?? "unknown failure";
    if (!failure.includes("ERR_ABORTED")) errors.push(`request: ${request.method()} ${request.url()} (${failure})`);
  });
  page.on("response", (response) => {
    if (response.status() >= 500) errors.push(`response: ${response.status()} ${response.url()}`);
  });
});

test.afterEach(({ page }) => {
  expect(browserErrors.get(page)).toEqual([]);
});


async function signIn(page: Page) {
  await page.goto("/");
  await page.getByLabel("Username").fill("playwright");
  await page.getByLabel("Password", { exact: true }).fill("fixture-password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Overview", exact: true })).toBeVisible();
  const errors = browserErrors.get(page) ?? [];
  expect(errors.filter((error) => !error.includes("status of 401 (Unauthorized)"))).toEqual([]);
  errors.length = 0;
}

async function waitForToastAnnouncements(page: Page) {
  await expect(page.locator("[data-slot='toast']")).toHaveCount(0, { timeout: 10_000 });
  await expect(page.locator("[data-live-announcer] [role='img']")).toHaveCount(0, { timeout: 10_000 });
}

async function selectLanguage(page: Page, nativeName: string) {
  const trigger = page.locator('[data-slot="dropdown-trigger"]').first();
  await trigger.click();
  await page.getByRole("menuitemradio", { name: nativeName, exact: true }).click();
}


test("authenticated shell is accessible in desktop and mobile themes", async ({ page }) => {
  await signIn(page);
  const securityNotice = page.getByRole("button", { name: "Trusted networks only" });
  await securityNotice.click();
  const securityDialog = page.getByRole("dialog", { name: "Trusted networks only" });
  await expect(securityDialog).toContainText(
    "This session uses HTTP. Credentials and task data are not encrypted in transit.",
  );
  await expect(securityDialog).toContainText(
    "Use HTTPS or bind the WebUI to 127.0.0.1 when the network is not fully trusted.",
  );
  await page.keyboard.press("Escape");
  await expect(securityDialog).toBeHidden();
  const desktopScan = await new AxeBuilder({ page }).analyze();
  expect(desktopScan.violations).toEqual([]);

  await page.getByRole("button", { name: "Use dark theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: "Use emerald accent" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme-color", "emerald");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Trusted networks only" }).click();
  await expect(page.getByRole("dialog", { name: "Trusted networks only" })).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(page.getByRole("link", { name: "Tasks", exact: true })).toBeVisible();
  const menuButton = page.getByRole("button", { name: "Open navigation" });
  const menuSize = await menuButton.evaluate((element) => {
    const style = getComputedStyle(element);
    return { width: style.width, height: style.height };
  });
  const workbarBox = await page.locator(".app-workbar-inner").boundingBox();
  expect(menuSize).toEqual({ width: "44px", height: "44px" });
  expect(workbarBox?.height).toBe(64);
  expect(await page.locator(".app-main").evaluate((element) => getComputedStyle(element).paddingLeft)).toBe("12px");

  await page.getByRole("button", { name: "Change appearance" }).click();
  const appearance = page.getByRole("dialog").filter({ has: page.getByRole("heading", { name: "Theme" }) });
  await expect(appearance.getByRole("group", { name: "Accent color" })).toBeVisible();
  await expect(appearance.getByRole("group", { name: "Color scheme" })).toBeVisible();
  await expect(page.locator(".compact-theme-popover")).toHaveCSS("width", "240px");
  for (const label of ["Follow system theme", "Use light theme", "Use dark theme"]) {
    const modeButton = appearance.getByRole("button", { name: label, exact: true });
    await expect(modeButton).toBeVisible();
    await expect(modeButton).toHaveText("");
    await expect(modeButton).toHaveCSS("width", "44px");
    await expect(modeButton).toHaveCSS("height", "44px");
  }
  await appearance.getByRole("button", { name: "Use rose accent" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme-color", "rose");
  await appearance.getByRole("button", { name: "Follow system theme", exact: true }).click();
  await expect.poll(() => page.evaluate(() => localStorage.getItem("ktoolbox-theme"))).toBe("system");
  await page.keyboard.press("Escape");
  await page.waitForTimeout(600);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
  const mobileScan = await new AxeBuilder({ page }).analyze();
  expect(mobileScan.violations).toEqual([]);
});


test("dashboard links, roster sorting, and platform suggestions work with real HeroUI controls", async ({ page }) => {
  await signIn(page);

  await page.getByRole("link", { name: /Active tasks/ }).click();
  await expect(page).toHaveURL(/\/tasks\?status=active$/);
  await expect(page.getByRole("heading", { name: "Tasks", exact: true })).toBeVisible();

  await page.getByRole("link", { name: "Creators", exact: true }).click();
  const table = page.locator(".app-table-frame");
  await expect(table.getByText("Alpha Atelier", { exact: true })).toBeVisible();
  await expect(table.getByText("第 10 工作室", { exact: true })).toBeVisible();

  const creatorIdHeader = page.getByRole("columnheader", { name: /Creator ID/ });
  await creatorIdHeader.click();
  await creatorIdHeader.click();
  const creatorRows = table.getByRole("row").filter({ has: page.getByRole("button", { name: /^Edit / }) });
  await expect(creatorRows.first()).toContainText("studio-10");

  await page.getByRole("button", { name: "Add creator" }).click();
  const dialog = page.getByRole("dialog", { name: "Add creator" });
  await dialog.getByRole("button", { name: /Parse creator URL/ }).click();
  await page.getByRole("option", { name: "Enter platform and creator ID" }).click();
  const platform = dialog.getByRole("combobox", { name: "Platform" });
  await platform.click();
  for (const option of ["Patreon", "Pixiv", "Fanbox"]) {
    const item = page.getByRole("option", { name: option });
    await expect(item).toBeVisible();
    await expect(item.locator(".select-option-icon svg")).toHaveAttribute("aria-hidden", "true");
  }
  await platform.fill("custom-platform");
  await expect(platform).toHaveValue("custom-platform");
  await page.keyboard.press("Escape");
  await dialog.getByRole("button", { name: "Cancel" }).click();
});


test("Chinese product terminology stays consistent across workflows", async ({ page }) => {
  await signIn(page);
  await selectLanguage(page, "简体中文");
  await expect(page.getByRole("heading", { name: "概览", exact: true })).toBeVisible();
  await expect(page.locator("body")).not.toContainText(legacyChineseTerms);

  await page.getByRole("link", { name: "任务", exact: true }).click();
  await page.getByRole("button", { name: "创建任务" }).click();
  await expect(page.getByRole("switch", { name: "同步所有已启用作者" })).toBeVisible();
  await page.getByRole("dialog", { name: "创建任务" }).getByRole("button", { name: "取消" }).click();

  await page.getByRole("link", { name: "作品", exact: true }).click();
  await expect(page.getByRole("heading", { name: "作品", exact: true })).toBeVisible();
  await expect(page.getByRole("combobox", { name: "平台" })).toBeVisible();

  await page.getByRole("link", { name: "忽略规则", exact: true }).click();
  await expect(page.getByRole("heading", { name: "忽略规则", exact: true })).toBeVisible();
  await expect(page.locator("body")).not.toContainText(legacyChineseTerms);
});


test("backend error objects render as readable toast messages", async ({ page }) => {
  await signIn(page);
  await page.route("**/api/v1/session/logout", async (route) => {
    await route.fulfill({
      status: 422,
      contentType: "application/json",
      body: JSON.stringify({
        detail: [
          { loc: ["body", "creator_id"], msg: "Field required", input: { creator_id: null } },
          { loc: ["query", "offset"], msg: "Must be a multiple of 50", input: 1 },
        ],
      }),
    });
  });

  await page.getByRole("button", { name: "Sign out" }).click();
  const toast = page.getByText("creator id: Field required; offset: Must be a multiple of 50", { exact: true });
  await expect(toast).toBeVisible();
  const toastRoot = toast.locator("xpath=ancestor::*[@data-slot='toast']");
  await page.waitForTimeout(600);
  await expect(toastRoot).toBeInViewport({ ratio: 1 });
  await expect(toastRoot).not.toContainText('"loc"');
  await expect(toastRoot).not.toContainText("[object Object]");
  const errors = browserErrors.get(page) ?? [];
  expect(errors.filter((error) => !error.includes("status of 422 (Unprocessable Entity)"))).toEqual([]);
  errors.length = 0;
});

test("MCP connection page issues one-time tokens and exposes safe client configurations", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "MCP", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1, name: "MCP", exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { level: 1, name: "MCP", exact: true })).toBeVisible();
  await expect(page.getByText("Streamable HTTP", { exact: true })).toBeVisible();
  await expect(page.getByText("http://127.0.0.1:8792/mcp", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: /Configuration.*2/ }).click();
  await expect(page.locator("code").filter({ hasText: "config_schema" })).toBeVisible();

  await page.getByRole("tab", { name: "Codex", exact: true }).click();
  await expect(page.getByText('bearer_token_env_var = "KTOOLBOX_MCP_TOKEN"', { exact: false })).toBeVisible();
  await page.getByRole("tab", { name: "VS Code", exact: true }).click();
  await expect(page.getByText('"password": true', { exact: false })).toBeVisible();

  await page.getByRole("button", { name: "New access token", exact: true }).click();
  const createDialog = page.getByRole("dialog", { name: "Create access token", exact: true });
  await createDialog.getByLabel("Token name").fill("Playwright MCP");
  await createDialog.getByLabel("Confirm account password").fill("fixture-password");
  await createDialog.getByRole("button").filter({ hasText: "30 days" }).click();
  await page.getByRole("option", { name: "Never expires", exact: true }).click();
  await expect(createDialog.getByText("This token remains valid until you revoke it manually.", { exact: false })).toBeVisible();
  await createDialog.getByRole("button", { name: "Create access token", exact: true }).click();

  const secretDialog = page.getByRole("dialog", { name: "Save this token now", exact: true });
  const secret = secretDialog.locator("code");
  await expect(secret).toContainText("ktmcp_");
  const secretValue = await secret.textContent();
  expect(secretValue).toMatch(/^ktmcp_/);
  await secretDialog.getByRole("button", { name: "Confirm", exact: true }).click();
  await expect(page.getByText(secretValue ?? "", { exact: true })).toHaveCount(0);

  const tokenRow = page.getByRole("row").filter({ hasText: "Playwright MCP" });
  await tokenRow.getByRole("button", { name: "Revoke", exact: true }).click();
  const revokeDialog = page.getByRole("dialog", { name: "Revoke this access token?", exact: true });
  await expect(revokeDialog).toContainText("Playwright MCP");
  await revokeDialog.getByRole("button", { name: "Revoke", exact: true }).click();
  await expect(tokenRow.getByText("Revoked", { exact: true })).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
  await expect(page.getByRole("button", { name: "New access token", exact: true })).toBeVisible();
  await waitForToastAnnouncements(page);
  const accessibility = await new AxeBuilder({ page }).analyze();
  expect(accessibility.violations).toEqual([]);
});


test("HeroUI tables and forms preserve their visual hierarchy", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Tasks", exact: true }).click();
  await page.getByRole("button", { name: "Create task" }).click();
  const formSurface = page.locator(".app-form-modal-surface");
  const formScroll = page.locator(".app-form-modal-body");
  const formActions = page.locator(".app-form-modal-actions");
  await expect(formSurface).toBeVisible();
  await expect(formActions).toBeVisible();
  await expect(formSurface.locator(".field-label-icon")).not.toHaveCount(0);
  await expect(formSurface.locator('[data-slot="switch-icon"]')).toHaveCount(0);
  await expect(page.locator(".task-editor-tabs").getByRole("tab")).toHaveCount(2);
  await expect(page.locator(".task-editor-tabs").locator('[data-slot="scroll-shadow"]')).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Scroll tabs right" })).toHaveCount(0);

  const switchContent = formSurface.locator('[data-slot="switch-content"]').filter({ hasText: "All enabled creators" });
  const switchControl = switchContent.locator('[data-slot="switch-control"]');
  const switchLabel = switchContent.locator('[data-slot="label"]');
  await expect(switchControl).toHaveCount(1);
  const [controlBox, labelBox] = await Promise.all([switchControl.boundingBox(), switchLabel.boundingBox()]);
  expect(controlBox).not.toBeNull();
  expect(labelBox).not.toBeNull();
  expect(Math.abs((controlBox?.y ?? 0) - (labelBox?.y ?? 0))).toBeLessThan(2);
  expect(controlBox?.x ?? 0).toBeLessThan(labelBox?.x ?? 0);

  const startDateCheckbox = formSurface.getByRole("checkbox", { name: "No start date" });
  const startDateRoot = startDateCheckbox.locator('xpath=ancestor::*[@data-slot="checkbox"]');
  await expect(startDateCheckbox).toBeChecked();
  await expect(startDateRoot.locator('[data-slot="checkbox-indicator"]')).toHaveCount(1);
  await startDateCheckbox.press("Space");
  await expect(startDateCheckbox).not.toBeChecked();
  await expect(startDateRoot.locator('[data-slot="checkbox-indicator"]')).toHaveCount(0);
  await page.getByRole("dialog", { name: "Create task" }).getByRole("button", { name: "Create task" }).click();
  await expect(page.getByRole("alert")).toContainText("Choose a start date");
  await startDateCheckbox.press("Space");
  await expect(page.getByRole("alert")).toHaveCount(0);

  const requiredKeywords = formSurface.getByRole("textbox", { name: "Required title keywords" });
  await requiredKeywords.click();
  await requiredKeywords.pressSequentially("painting,painting，draft");
  await requiredKeywords.press("Enter");
  await expect(formSurface.getByRole("button", { name: "Remove painting" })).toHaveCount(1);
  await expect(formSurface.getByRole("button", { name: "Remove draft" })).toHaveCount(1);
  await formSurface.getByRole("button", { name: "Remove draft" }).click();
  await expect(formSurface.getByRole("button", { name: "Remove draft" })).toHaveCount(0);

  await page.getByRole("tab", { name: "Download post" }).click();
  await formSurface.getByRole("button", { name: /Parse post URL/ }).click();
  await page.getByRole("option", { name: "Enter platform and IDs", exact: true }).click();
  const postPath = formSurface.getByRole("group", { name: "Pawchive post path" });
  const revisionExample = formSurface.getByText(
    "https://pawchive.pw/fanbox/user/16456081/post/5715578/revision/8933804",
    { exact: true },
  );
  await revisionExample.scrollIntoViewIfNeeded();
  await expect(revisionExample).toBeVisible();
  await expect(revisionExample).toHaveCSS("font-family", /monospace/);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(revisionExample).toBeVisible();
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
  await page.setViewportSize({ width: 1440, height: 900 });
  const platformField = postPath.getByRole("combobox", { name: "Platform" });
  const creatorIdField = postPath.getByRole("textbox", { name: "Creator ID" });
  const postIdField = postPath.getByRole("textbox", { name: "Post ID" });
  await expect(platformField).toHaveValue("fanbox");
  await platformField.focus();
  await page.keyboard.press("Tab");
  await expect(creatorIdField).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(postIdField).toBeFocused();
  await page.getByRole("tab", { name: "Sync creators" }).click();

  const [scrollBox, actionBox] = await Promise.all([formScroll.boundingBox(), formActions.boundingBox()]);
  expect(scrollBox).not.toBeNull();
  expect(actionBox).not.toBeNull();
  expect(Math.abs((scrollBox?.y ?? 0) + (scrollBox?.height ?? 0) - (actionBox?.y ?? 0))).toBeLessThan(1);
  expect(await formSurface.locator(".app-form-modal-actions").count()).toBe(1);
  expect(await page.locator('[data-slot="modal-footer"]').count()).toBe(1);

  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
  await page.waitForTimeout(600);
  const modalScan = await new AxeBuilder({ page }).analyze();
  expect(modalScan.violations).toEqual([]);

  await page.setViewportSize({ width: 320, height: 700 });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
  await expect(formSurface.getByText("All enabled creators", { exact: true })).toBeVisible();
  await expect(formSurface.getByRole("group", { name: "Publication date range" })).toBeVisible();
  await expect(formSurface.locator(".optional-date-range-separator")).toHaveCount(0);
  expect(await formActions.evaluate((element) => element.scrollWidth - element.clientWidth)).toBe(0);

  await page.setViewportSize({ width: 1440, height: 900 });
  await formSurface.getByRole("textbox", { name: /Output directory/ }).fill("visual-hierarchy-downloads");
  await page.getByRole("dialog", { name: "Create task" }).getByRole("button", { name: "Create task" }).click();
  await expect(page.getByRole("heading", { name: "Task details" })).toBeVisible();
  await page.getByRole("button", { name: "Back" }).click();

  const tableRoot = page.locator(".table-root--secondary");
  const tableFrame = page.locator(".app-table-frame");
  await expect(tableRoot).toHaveCount(1);
  await expect(tableFrame).toHaveCount(1);
  await expect(tableFrame.locator(".table-column-icon")).toHaveCount(7);
  const tableStyles = await tableRoot.evaluate((element) => {
    const style = getComputedStyle(element);
    return {
      background: style.backgroundColor,
      padding: [style.paddingTop, style.paddingRight, style.paddingBottom, style.paddingLeft],
    };
  });
  expect(tableStyles.background).toBe("rgba(0, 0, 0, 0)");
  expect(tableStyles.padding).toEqual(["0px", "0px", "0px", "0px"]);
  await expect(tableFrame).toHaveCSS("border-top-width", "1px");
  expect(await tableFrame.evaluate((element) => element.scrollWidth - element.clientWidth)).toBe(0);

  const creatorSummary = tableFrame.getByText(/among \d+ creators/).first();
  await expect(creatorSummary).toBeVisible();
  await expect(tableFrame.getByText(/Demo Studio/).first()).toBeVisible();
  const desktopTaskRow = creatorSummary.locator("xpath=ancestor::*[@role='row'][1]");
  const desktopActions = desktopTaskRow.locator(".task-action-grid button");
  await expect(desktopActions).toHaveCount(4);
  await expect(desktopTaskRow.locator(".task-status-chip, [data-slot='chip']").filter({ hasText: "Running" }).locator("svg")).toHaveCount(1);
  for (const label of ["Stop", "Edit", "Delete"]) {
    await expect(desktopTaskRow.getByRole("button", { name: label })).toBeVisible();
  }
  await expect(desktopTaskRow.getByRole("button", { name: "Move up" })).toHaveCount(0);
  await expect(desktopTaskRow.getByRole("button", { name: "Move down" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Actions" })).toHaveCount(0);
  await desktopTaskRow.getByRole("rowheader").click();
  await expect(page.getByRole("heading", { name: "Task details" })).toBeVisible();
  await page.getByRole("button", { name: "Back" }).click();

  const selectedTask = page.getByRole("checkbox", { name: /Select Demo Studio/ }).first();
  await page.locator('[data-slot="checkbox"]').filter({ has: selectedTask }).click();
  await expect(page.getByRole("region", { name: "Batch actions" })).toBeVisible();
  const batchAuditDirectory = process.env.KTOOLBOX_BATCH_AUDIT_DIR;
  if (batchAuditDirectory) {
    await mkdir(batchAuditDirectory, { recursive: true });
    await page.screenshot({ fullPage: true, path: join(batchAuditDirectory, "tasks-desktop-light.png") });
  }

  await page.setViewportSize({ width: 390, height: 844 });
  const mobileCard = page.locator(".task-mobile-card:visible").filter({
    hasText: /among \d+ creators/,
  });
  await expect(mobileCard).toBeVisible();
  const mobileActions = mobileCard.locator(".task-action-grid button");
  await expect(mobileActions).toHaveCount(4);
  const mobileActionBox = await mobileCard.locator(".task-action-grid").boundingBox();
  expect(mobileActionBox?.height ?? 0).toBeGreaterThanOrEqual(44);
  expect(mobileActionBox?.height ?? 0).toBeLessThan(72);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
  if (batchAuditDirectory) {
    await page.screenshot({ fullPage: true, path: join(batchAuditDirectory, "tasks-mobile-light.png") });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.getByRole("button", { name: "Use dark theme" }).click();
    await page.waitForTimeout(200);
    await page.screenshot({ fullPage: true, path: join(batchAuditDirectory, "tasks-desktop-dark.png") });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ fullPage: true, path: join(batchAuditDirectory, "tasks-mobile-dark.png") });
  }
  await page.getByRole("button", { name: "Clear selection" }).click();

  await page.setViewportSize({ width: 768, height: 1024 });
  await expect(page.locator(".app-table-frame:visible")).toHaveCount(0);
  await expect(mobileCard).toBeVisible();
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
});


test("remote path picker browses the server filesystem from nested forms", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Tasks", exact: true }).click();
  await page.getByRole("button", { name: "Create task" }).click();
  const taskDialog = page.getByRole("dialog", { name: "Create task" });
  const browseButton = taskDialog.getByRole("button", { name: "Browse the remote computer for Output directory" });
  await browseButton.click();

  const picker = page.getByRole("dialog", { name: "Output directory" });
  await expect(picker).toBeVisible();
  await expect(picker.getByText("Project files")).toBeVisible();
  await expect(picker.getByRole("switch", { name: "Show hidden items" })).toBeVisible();
  await expect(picker.getByRole("textbox", { name: "Remote path" })).toHaveValue(/[/\\]downloads$/);
  await picker.getByRole("button", { name: "Parent directory" }).click();
  await expect(picker.getByRole("option", { name: "downloads" })).toBeVisible();
  await picker.getByRole("option", { name: "downloads" }).click();
  await expect(picker.getByRole("textbox", { name: "Remote path" })).toHaveValue(/[/\\]downloads$/);
  await picker.getByRole("button", { name: "Select directory" }).click();
  await expect(taskDialog.getByRole("textbox", { name: "Output directory" })).toHaveValue(/[/\\]downloads$/);
  await expect(browseButton).toBeFocused();

  await browseButton.click();
  await expect(picker).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(picker).not.toBeVisible();
  await expect(taskDialog).toBeVisible();
  await expect(browseButton).toBeFocused();

  await page.setViewportSize({ width: 390, height: 844 });
  await browseButton.click();
  await picker.getByRole("button", { name: "New folder" }).click();
  const createFolderDialog = page.getByRole("dialog", { name: "New folder" });
  await expect(createFolderDialog.getByText(/Create an empty folder/)).toBeVisible();
  await createFolderDialog.getByRole("textbox", { name: "Folder name" }).fill("e2e-created");
  await createFolderDialog.getByRole("button", { name: "Create folder" }).click();
  await expect(picker.getByRole("textbox", { name: "Remote path" })).toHaveValue(/[/\\]e2e-created$/);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
  expect(await picker.evaluate((element) => element.scrollWidth - element.clientWidth)).toBe(0);
  const pickerScan = await new AxeBuilder({ page }).include(".remote-path-picker-container").analyze();
  expect(pickerScan.violations).toEqual([]);
  await picker.getByRole("button", { name: "Parent directory" }).click();
  await picker.getByRole("button", { name: "Delete folder e2e-created" }).click();
  const deleteFolderDialog = page.getByRole("dialog", { name: "Delete this empty folder?" });
  await expect(deleteFolderDialog.getByText(/Files and nested folders are never deleted/)).toBeVisible();
  await deleteFolderDialog.getByRole("button", { name: "Delete folder" }).click();
  await expect(picker.getByRole("option", { name: "e2e-created" })).toHaveCount(0);
  await expect(picker.getByText(/Deleted empty folder/)).toBeVisible();
  await picker.getByRole("button", { name: "Cancel" }).click();
  await taskDialog.getByRole("button", { name: "Cancel" }).click();

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.getByRole("link", { name: "Configuration" }).click();
  await page.getByRole("button", { name: /Configuration section/ }).click();
  await page.getByRole("option", { name: "File downloads" }).click();
  const bucketBrowse = page.getByRole("button", { name: "Browse the remote computer for Storage bucket path" });
  await bucketBrowse.click();
  const hostPicker = page.getByRole("dialog", { name: "Storage bucket path" });
  await expect(hostPicker.getByText("Remote computer")).toBeVisible();
  const suggestedFolderDialog = page.getByRole("dialog", { name: "New folder" });
  if (await suggestedFolderDialog.isVisible()) {
    await suggestedFolderDialog.getByRole("button", { name: "Cancel" }).click();
  }
  await hostPicker.getByRole("button", { name: /Quick location/ }).click();
  const homeOption = page.getByRole("option", { name: "Home" });
  await expect(homeOption).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(homeOption).not.toBeVisible();
  await page.keyboard.press("Escape");
  await expect(hostPicker).not.toBeVisible();
});


test("remote path picker localizes every visible control", async ({ page }) => {
  await signIn(page);
  await selectLanguage(page, "简体中文");
  await page.getByRole("link", { name: "任务", exact: true }).click();
  await page.getByRole("button", { name: "创建任务" }).click();
  const taskDialog = page.getByRole("dialog", { name: "创建任务" });
  await taskDialog.getByRole("button", { name: "在远程计算机中浏览输出目录" }).click();
  const picker = page.getByRole("dialog", { name: "输出目录" });

  await expect(picker.getByRole("button", { name: /项目目录.*快捷位置/ })).toBeVisible();
  await expect(picker.getByRole("switch", { name: "显示隐藏项目" })).toBeVisible();
  await expect(picker.getByRole("button", { name: "新建目录" })).toBeVisible();
  await expect(picker.getByRole("button", { name: "选择目录" })).toBeVisible();
  await expect(picker.getByText("Project", { exact: true })).toHaveCount(0);
});


const localeCases = [
  { code: "zh-CN", nativeName: "简体中文", pages: [["/", "概览"], ["/tasks", "任务"], ["/creators", "作者"], ["/posts", "作品"], ["/blockers", "忽略规则"], ["/configuration", "配置"], ["/system", "系统"]], create: "创建任务" },
  { code: "zh-Hant", nativeName: "繁體中文", pages: [["/", "概覽"], ["/tasks", "工作"], ["/creators", "作者"], ["/posts", "作品"], ["/blockers", "忽略規則"], ["/configuration", "設定"], ["/system", "系統"]], create: "建立工作" },
  { code: "en", nativeName: "English", pages: [["/", "Overview"], ["/tasks", "Tasks"], ["/creators", "Creators"], ["/posts", "Posts"], ["/blockers", "Blockers"], ["/configuration", "Configuration"], ["/system", "System"]], create: "Create task" },
  { code: "ja", nativeName: "日本語", pages: [["/", "概要"], ["/tasks", "タスク"], ["/creators", "クリエイター"], ["/posts", "作品"], ["/blockers", "除外ルール"], ["/configuration", "設定"], ["/system", "システム"]], create: "タスクを作成" },
  { code: "ko", nativeName: "한국어", pages: [["/", "개요"], ["/tasks", "작업"], ["/creators", "크리에이터"], ["/posts", "작품"], ["/blockers", "제외 규칙"], ["/configuration", "설정"], ["/system", "시스템"]], create: "작업 만들기" },
  { code: "fr", nativeName: "Français", pages: [["/", "Aperçu"], ["/tasks", "Tâches"], ["/creators", "Créateurs"], ["/posts", "Œuvres"], ["/blockers", "Règles d’exclusion"], ["/configuration", "Configuration"], ["/system", "Système"]], create: "Créer une tâche" },
  { code: "ru", nativeName: "Русский", pages: [["/", "Обзор"], ["/tasks", "Задачи"], ["/creators", "Авторы"], ["/posts", "Работы"], ["/blockers", "Правила исключения"], ["/configuration", "Настройки"], ["/system", "Система"]], create: "Создать задачу" },
] as const;

for (const locale of localeCases) {
  test(`${locale.nativeName} localizes every primary WebUI route`, async ({ page }) => {
    await signIn(page);
    if (locale.code !== "en") await selectLanguage(page, locale.nativeName);
    await expect(page.locator("html")).toHaveAttribute("lang", locale.code);

    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("lang", locale.code);
    await expect(page.getByRole("heading", { name: locale.pages[0][1], exact: true })).toBeVisible();

    for (const [path, heading] of locale.pages) {
      if (path === "/configuration") {
        const responsePromise = page.waitForResponse((response) => response.url().includes("/config/schema?locale="));
        await page.goto(path);
        const response = await responsePromise;
        expect(new URL(response.url()).searchParams.get("locale")).toBe(locale.code);
        expect((await response.json()).locale).toBe(locale.code);
      } else {
        await page.goto(path);
      }
      await expect(page.getByRole("heading", { name: heading, exact: true })).toBeVisible();
      await expect(page.locator("body")).not.toContainText(/(?:nav|tasks|creators|posts|blockers|configuration|system)\.[A-Za-z]/);
    }

    await page.goto("/tasks");
    await page.getByRole("button", { name: locale.create, exact: true }).click();
    await expect(page.getByRole("dialog", { name: locale.create, exact: true })).toBeVisible();
    await page.keyboard.press("Escape");

    await page.setViewportSize({ width: 320, height: 700 });
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
    const scan = await new AxeBuilder({ page }).analyze();
    expect(scan.violations).toEqual([]);
  });
}

test("captures the complete mobile page density matrix", async ({ page }, testInfo) => {
  const auditDirectory = process.env.KTOOLBOX_UI_AUDIT_DIR ?? testInfo.outputPath("mobile-density-audit");
  const routes = [
    ["overview", "/", "Create sync task"],
    ["tasks", "/tasks", "Create task"],
    ["creators", "/creators", "Add creator"],
    ["posts", "/posts", "Search posts"],
    ["blockers", "/blockers", "Add blocker"],
    ["configuration", "/configuration", "Structured settings"],
    ["mcp", "/mcp", "New access token"],
    ["system", "/system", "Check Pawchive"],
  ] as const;

  await mkdir(auditDirectory, { recursive: true });
  await signIn(page);
  await page.getByRole("button", { name: "Use dark theme" }).click();
  await page.getByRole("button", { name: "Use rose accent" }).click();
  await page.setViewportSize({ width: 390, height: 844 });

  for (const [name, path, readyName] of routes) {
    await page.goto(path);
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.getByText(readyName, { exact: true }).first()).toBeVisible();
    await expect.poll(
      () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth),
    ).toBe(0);
    await page.screenshot({
      fullPage: true,
      path: join(auditDirectory, `${name}__390x844__dark-rose__default.png`),
    });
  }
});


test("captures the remote path picker visual matrix", async ({ page }, testInfo) => {
  const auditDirectory = process.env.KTOOLBOX_UI_AUDIT_DIR ?? testInfo.outputPath("ui-audit");
  await mkdir(auditDirectory, { recursive: true });
  async function capture(name: string, width: number, height: number) {
    await page.setViewportSize({ width, height });
    await page.waitForTimeout(500);
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
    await page.screenshot({ path: join(auditDirectory, `${name}__${width}x${height}.png`) });
  }

  await page.setViewportSize({ width: 1440, height: 900 });
  await signIn(page);
  await page.getByRole("link", { name: "Tasks", exact: true }).click();
  await page.getByRole("button", { name: "Create task" }).click();
  let parentDialog = page.getByRole("dialog", { name: "Create task" });
  await parentDialog.getByRole("button", { name: "Browse the remote computer for Output directory" }).click();
  let picker = page.getByRole("dialog", { name: "Output directory" });
  await expect(picker).toBeVisible();
  await capture("tasks__directory-picker__light", 1440, 900);
  await capture("tasks__directory-picker__light", 1024, 768);
  await capture("tasks__directory-picker__light", 768, 1024);
  await picker.getByRole("button", { name: "Cancel" }).click();
  await parentDialog.getByRole("button", { name: "Cancel" }).click();

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.getByRole("button", { name: "Use dark theme" }).click();
  await page.getByRole("button", { name: "Use emerald accent" }).click();
  await page.getByRole("button", { name: "Create task" }).click();
  parentDialog = page.getByRole("dialog", { name: "Create task" });
  await parentDialog.getByRole("button", { name: "Browse the remote computer for Output directory" }).click();
  picker = page.getByRole("dialog", { name: "Output directory" });
  await expect(picker).toBeVisible();
  await capture("tasks__directory-picker__dark-emerald", 390, 844);
  await picker.getByRole("button", { name: "New folder" }).click();
  await expect(page.getByRole("dialog", { name: "New folder" })).toBeVisible();
  await capture("tasks__directory-picker-create__dark-emerald", 390, 844);
  await page.getByRole("dialog", { name: "New folder" }).getByRole("button", { name: "Cancel" }).click();
  await capture("tasks__directory-picker__dark-emerald", 320, 700);
  const selectionBox = await picker.locator(".remote-path-selection").boundingBox();
  const footerBox = await picker.locator('[data-slot="modal-footer"]').boundingBox();
  expect(selectionBox).not.toBeNull();
  expect(footerBox).not.toBeNull();
  expect((selectionBox?.y ?? 0) + (selectionBox?.height ?? 0)).toBeLessThanOrEqual(footerBox?.y ?? 0);
  const [goButtonBox, refreshButtonBox] = await Promise.all([
    picker.getByRole("button", { name: "Go" }).boundingBox(),
    picker.getByRole("button", { name: "Refresh" }).boundingBox(),
  ]);
  expect(goButtonBox).not.toBeNull();
  expect(refreshButtonBox).not.toBeNull();
  const controlsOverlap = Boolean(goButtonBox && refreshButtonBox)
    && goButtonBox.x < refreshButtonBox.x + refreshButtonBox.width
    && goButtonBox.x + goButtonBox.width > refreshButtonBox.x
    && goButtonBox.y < refreshButtonBox.y + refreshButtonBox.height
    && goButtonBox.y + goButtonBox.height > refreshButtonBox.y;
  expect(controlsOverlap).toBe(false);
  await picker.getByRole("button", { name: "Cancel" }).click();
  await parentDialog.getByRole("button", { name: "Cancel" }).click();

  await page.setViewportSize({ width: 1024, height: 768 });
  await page.getByRole("button", { name: "Use light theme" }).click();
  await page.getByRole("link", { name: "Posts" }).click();
  await page.getByRole("textbox", { name: "Creator ID" }).fill("demo-studio");
  await page.getByRole("button", { name: "Search posts" }).click();
  await page.getByRole("button", { name: "Post details" }).first().click();
  parentDialog = page.getByRole("dialog", { name: "Fictional project study" });
  await parentDialog.getByRole("button", { name: "Browse the remote computer for Output directory" }).click();
  picker = page.getByRole("dialog", { name: "Output directory" });
  await expect(picker).toBeVisible();
  await capture("posts__directory-picker__light", 1024, 768);
  await picker.getByRole("button", { name: "Cancel" }).click();
  await parentDialog.getByText("Close", { exact: true }).click();

  await page.getByRole("link", { name: "Configuration" }).click();
  await page.getByRole("button", { name: /Configuration section/ }).click();
  await page.getByRole("option", { name: "Download jobs" }).click();
  await page.getByRole("button", { name: "Browse the remote computer for Content file" }).click();
  picker = page.getByRole("dialog", { name: "Content file" });
  await expect(picker.getByRole("textbox", { name: "File name" })).toHaveValue("content.txt");
  await capture("configuration__file-picker__light", 768, 1024);
  await picker.getByRole("button", { name: "Cancel" }).click();

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.getByRole("button", { name: "Use dark theme" }).click();
  await page.getByRole("button", { name: /Configuration section/ }).click();
  await page.getByRole("option", { name: "File downloads" }).click();
  await page.getByRole("button", { name: "Browse the remote computer for Storage bucket path" }).click();
  picker = page.getByRole("dialog", { name: "Storage bucket path" });
  await expect(picker.getByText("Remote computer")).toBeVisible();
  const suggestedFolderDialog = page.getByRole("dialog", { name: "New folder" });
  if (await suggestedFolderDialog.isVisible()) {
    await suggestedFolderDialog.getByRole("button", { name: "Cancel" }).click();
  }
  await expect(picker.locator('[data-slot="breadcrumbs-item"]')).toHaveCount(5);
  await capture("configuration__host-picker__dark-emerald", 1440, 900);
});


test("roster blockers and configuration keep controls aligned and visible", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Creators", exact: true }).click();
  await expect(page).toHaveURL(/\/creators$/);
  await expect(page.getByRole("columnheader", { name: "Creator name" })).toBeVisible();

  const creatorRow = page.getByRole("row").filter({ hasText: "Demo Studio" });
  expect(await page.getByRole("columnheader").allTextContents()).toEqual([
    "",
    "Creator name",
    "Creator ID",
    "Platform",
    "Note",
    "Included in full sync",
    "Actions",
  ]);
  await expect(page.locator(".app-table-frame .table-column-icon")).toHaveCount(6);
  await expect(creatorRow.locator(".platform-label-icon")).toBeVisible();
  await expect(creatorRow.getByRole("button", { name: "Edit fanbox:demo-studio" })).toBeVisible();
  await expect(creatorRow.getByRole("button", { name: "Remove fanbox:demo-studio" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Actions Demo Studio/ })).toHaveCount(0);
  const creatorSwitchCell = creatorRow.locator(".list-switch-cell");
  const creatorSwitchControl = creatorSwitchCell.locator('[data-slot="switch-control"]');
  const [creatorCellBox, creatorControlBox] = await Promise.all([
    creatorSwitchCell.boundingBox(),
    creatorSwitchControl.boundingBox(),
  ]);
  expect(creatorCellBox).not.toBeNull();
  expect(creatorControlBox).not.toBeNull();
  expect(Math.abs(
    (creatorCellBox?.x ?? 0) + (creatorCellBox?.width ?? 0) / 2
      - (creatorControlBox?.x ?? 0) - (creatorControlBox?.width ?? 0) / 2,
  )).toBeLessThan(1);
  await creatorRow.getByRole("switch", { name: "Enabled" }).press("Space");
  const disabledCreatorSwitch = creatorRow.getByRole("switch", { name: "Disabled" });
  await expect(disabledCreatorSwitch).toBeVisible();
  const offTrack = await creatorSwitchControl.evaluate((element) => getComputedStyle(element).backgroundColor);
  const fieldSurface = await page.locator("main input").first().evaluate((element) => getComputedStyle(element).backgroundColor);
  expect(offTrack).not.toBe(fieldSurface);
  const creatorSelection = page.getByRole("checkbox", { name: "Select Demo Studio" }).first();
  await page.locator('[data-slot="checkbox"]').filter({ has: creatorSelection }).click();
  const batchAuditDirectory = process.env.KTOOLBOX_BATCH_AUDIT_DIR;
  if (batchAuditDirectory) {
    await mkdir(batchAuditDirectory, { recursive: true });
    await page.screenshot({ fullPage: true, path: join(batchAuditDirectory, "creators-desktop-light.png") });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ fullPage: true, path: join(batchAuditDirectory, "creators-mobile-light.png") });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.getByRole("button", { name: "Use dark theme" }).click();
    await page.waitForTimeout(200);
    await page.screenshot({ fullPage: true, path: join(batchAuditDirectory, "creators-desktop-dark.png") });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ fullPage: true, path: join(batchAuditDirectory, "creators-mobile-dark.png") });
    await page.setViewportSize({ width: 1440, height: 900 });
  }
  await expect(page.getByRole("button", { name: "Enable 1" })).toHaveClass(/action-tone-enable/);
  await page.getByRole("button", { name: "Enable 1" }).click();
  await expect(creatorRow.getByRole("switch", { name: "Enabled" })).toBeVisible();
  await waitForToastAnnouncements(page);

  await page.getByRole("button", { name: "Add creator" }).click();
  const addCreatorDialog = page.getByRole("dialog", { name: "Add creator" });
  await expect(addCreatorDialog.getByRole("button", { name: /Parse creator URL/ })).toBeVisible();
  await expect(addCreatorDialog.getByRole("textbox", { name: "Pawchive creator URL" })).toBeVisible();
  await addCreatorDialog.getByRole("textbox", { name: "Pawchive creator URL" }).fill(
    "https://pawchive.pw/fanbox/user/example-creator",
  );
  const creatorUrlAuditDirectory = process.env.KTOOLBOX_CREATOR_URL_AUDIT_DIR;
  if (creatorUrlAuditDirectory) {
    await mkdir(creatorUrlAuditDirectory, { recursive: true });
    await page.waitForTimeout(300);
    await page.screenshot({ path: join(creatorUrlAuditDirectory, "creator-url-desktop-light.png") });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(300);
    await page.screenshot({ path: join(creatorUrlAuditDirectory, "creator-url-mobile-light.png") });
    await page.setViewportSize({ width: 1440, height: 900 });
  }
  await addCreatorDialog.getByRole("button", { name: /Parse creator URL/ }).click();
  await page.getByRole("option", { name: "Enter platform and creator ID" }).click();
  await expect(addCreatorDialog.getByRole("group", { name: "Pawchive creator path" })).toBeVisible();
  await expect(addCreatorDialog.getByRole("combobox", { name: "Platform" })).not.toHaveAttribute("readonly");
  await expect(addCreatorDialog.getByRole("textbox", { name: "Creator ID" })).not.toHaveAttribute("readonly");
  await expect(addCreatorDialog.getByRole("textbox", { name: "Note" })).toBeVisible();
  await addCreatorDialog.getByRole("button", { name: "Cancel" }).click();

  await creatorRow.getByRole("button", { name: "Edit fanbox:demo-studio" }).click();
  const editCreatorDialog = page.getByRole("dialog", { name: "Edit creator" });
  await expect(editCreatorDialog.getByRole("combobox", { name: "Platform" })).toHaveAttribute("readonly", "");
  await expect(editCreatorDialog.getByRole("textbox", { name: "Creator ID" })).toHaveAttribute("readonly", "");
  await editCreatorDialog.getByRole("button", { name: "Cancel" }).click();

  await page.getByRole("link", { name: "Blockers", exact: true }).click();
  await page.getByRole("button", { name: "Add blocker" }).click();
  const blockerEditor = page.getByRole("dialog", { name: "Add blocker" });
  await expect(blockerEditor.getByRole("textbox", { name: "Matcher type" })).toHaveValue("Field match");
  await expect(blockerEditor.getByRole("button", { name: /Matcher type/ })).toHaveCount(0);
  await page.getByRole("textbox", { name: /Rule ID/ }).fill("daily-sharing");
  await page.getByRole("textbox", { name: "Values" }).pressSequentially("fictional-daily,");
  await expect(page.getByRole("button", { name: "Remove fictional-daily" })).toBeVisible();
  await page.getByRole("dialog", { name: "Add blocker" }).getByRole("button", { name: "Save" }).click();

  const blockerCard = page.locator(".data-list-card").filter({
    has: page.getByRole("heading", { name: "daily-sharing" }),
  });
  await expect(blockerCard.getByRole("button", { name: "Edit" })).toBeVisible();
  await expect(blockerCard.getByRole("button", { name: "Remove blocker" })).toBeVisible();
  const blockerSwitchCell = blockerCard.locator(".list-switch-cell");
  const blockerSwitchControl = blockerSwitchCell.locator('[data-slot="switch-control"]');
  const [blockerCellBox, blockerControlBox] = await Promise.all([
    blockerSwitchCell.boundingBox(),
    blockerSwitchControl.boundingBox(),
  ]);
  expect(blockerCellBox).not.toBeNull();
  expect(blockerControlBox).not.toBeNull();
  expect(Math.abs(
    (blockerCellBox?.x ?? 0) + (blockerCellBox?.width ?? 0) / 2
      - (blockerControlBox?.x ?? 0) - (blockerControlBox?.width ?? 0) / 2,
  )).toBeLessThan(1);

  await blockerCard.getByRole("button", { name: "Remove blocker" }).click();
  await expect(page.getByRole("dialog", { name: "Remove this blocker?" })).toBeVisible();
  await page.getByRole("dialog", { name: "Remove this blocker?" }).getByRole("button", { name: "Cancel" }).click();

  await page.getByRole("link", { name: "Configuration", exact: true }).click();
  const saveBar = page.locator(".config-save-bar");
  await expect(saveBar).toBeVisible();
  expect(await saveBar.evaluate((element) => Boolean(element.closest(".form-surface")))).toBe(true);
  await page.setViewportSize({ width: 390, height: 844 });
  const tabsScroller = page.locator('[data-slot="scroll-shadow"]');
  await expect(tabsScroller).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Scroll tabs right" })).not.toBeVisible();
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
});


test("task form serializes one-sided dates and protects regular-expression commas", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Tasks", exact: true }).click();
  await page.getByRole("button", { name: "Create task" }).click();
  const taskDialog = page.getByRole("dialog", { name: "Create task" });
  const noStartDate = taskDialog.getByRole("checkbox", { name: "No start date" });
  await noStartDate.press("Space");
  await expect(noStartDate).not.toBeChecked();
  await taskDialog.getByRole("group", { name: "Publication date range" }).getByRole("button").click();
  const startCalendar = page.getByRole("application", { name: /Publication date range/ });
  await expect(startCalendar.getByRole("heading")).toContainText("July 2026");
  await startCalendar.getByRole("button", { name: "Friday, July 10, 2026" }).click();
  await expect(noStartDate).not.toBeChecked();
  await expect(taskDialog.getByRole("checkbox", { name: "No end date" })).toBeChecked();
  await expect(startCalendar).not.toBeVisible();

  const keywords = taskDialog.getByRole("textbox", { name: "Required title keywords" });
  await keywords.click();
  await keywords.pressSequentially("painting,painting，draft");
  await keywords.press("Enter");
  await taskDialog.getByRole("button", { name: "Remove draft" }).click();
  await taskDialog.getByRole("textbox", { name: "Output directory" }).fill("dated-sync-output");

  const requestPromise = page.waitForRequest((request) => request.method() === "POST" && request.url().endsWith("/api/v1/tasks"));
  await taskDialog.getByRole("button", { name: "Create task" }).click();
  const createRequest = await requestPromise;
  expect(createRequest.postDataJSON()).toMatchObject({
    spec: {
      kind: "sync",
      start_time: "2026-07-10T00:00:00",
      end_time: null,
      keywords: ["painting"],
      output: "dated-sync-output",
    },
  });
  await expect(page.getByRole("heading", { name: "Task details" })).toBeVisible();

  await page.getByRole("link", { name: "Blockers", exact: true }).click();
  await page.getByRole("button", { name: "Add blocker" }).click();
  const blockerDialog = page.getByRole("dialog", { name: "Add blocker" });
  await blockerDialog.getByRole("button", { name: /Contains Operator/ }).click();
  await page.getByRole("option", { name: "Regular expression" }).click();
  const regexValue = blockerDialog.getByRole("textbox", { name: "Values" });
  await regexValue.pressSequentially("^foo,bar$");
  await expect(regexValue).toHaveValue("^foo,bar$");
  await regexValue.press("Enter");
  await expect(blockerDialog.getByRole("button", { name: "Remove ^foo,bar$" })).toBeVisible();
  await expect(blockerDialog).toContainText("Commas are preserved in regular expressions");
});


test("task lifecycle remains operable through pause resume and stop", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Tasks", exact: true }).click();
  await page.getByRole("button", { name: "Create task" }).click();
  await page.getByRole("dialog", { name: "Create task" }).getByRole("button", { name: "Create task" }).click();
  await expect(page.getByRole("heading", { name: "Task details" })).toBeVisible();
  await expect(page.getByText("Running", { exact: true })).toBeVisible();
  await expect(page.getByTitle(/KiB\/s|MiB\/s/)).toBeVisible();

  await page.getByRole("button", { name: "Pause" }).click();
  await expect(page.getByText("Paused", { exact: true })).toBeVisible();
  await expect(page.getByText("0 B/s", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Resume" }).click();
  await expect(page.getByText("Running", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Stop" }).click();
  await expect(page.getByText("Stopped", { exact: true })).toBeVisible();
});


test("failed tasks explain the stage, reason, and recovery action", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Tasks", exact: true }).click();
  await page.getByRole("button", { name: "Create task" }).click();
  const dialog = page.getByRole("dialog", { name: "Create task" });
  await dialog.getByRole("textbox", { name: "Output directory" }).fill("failure-fixture");
  await dialog.getByRole("button", { name: "Create task" }).click();

  await expect(page.getByText("Failed", { exact: true })).toBeVisible({ timeout: 10_000 });
  const panel = page.getByRole("heading", { name: "Why this task failed" })
    .locator('xpath=ancestor::*[@aria-labelledby="task-failure-title"]');
  await expect(panel).toContainText("Creator failures: 1; file failures: 0.");
  await expect(panel).not.toContainText("Synchronization finished");
  await expect(panel).toContainText("Pawchive returned data in an unsupported format.");
  await expect(page.getByText("items.8.tags", { exact: false })).toBeVisible();
  await expect(page.getByText(/Update KToolBox/)).toBeVisible();
  await expect(page.getByText("Creator finished", { exact: true })).toBeVisible();
  await expect(page.locator("body")).not.toContainText('"code": "response_incompatible"');

  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(
    () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth),
  ).toBe(0);
  await expect(page.getByRole("heading", { name: "Why this task failed" })).toBeVisible();
  await waitForToastAnnouncements(page);
  const scan = await new AxeBuilder({ page }).analyze();
  expect(scan.violations).toEqual([]);
});


test("task details keep a long retry queue inside its own scroll region", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Tasks", exact: true }).click();
  await page.getByRole("button", { name: "Create task" }).click();
  const dialog = page.getByRole("dialog", { name: "Create task" });
  await dialog.getByRole("textbox", { name: "Output directory" }).fill("retry-fixture");
  await dialog.getByRole("button", { name: "Create task" }).click();

  const retryRegion = page.getByRole("region", { name: "Waiting to retry" });
  await expect(retryRegion).toBeVisible({ timeout: 10_000 });
  await expect(retryRegion.getByText("fictional-retry-file-01.zip")).toBeVisible();
  await expect(retryRegion.getByText("Retries completed: 0").first()).toBeVisible();
  await expect(retryRegion.getByText("HTTP 429").first()).toBeVisible();
  await expect.poll(() => retryRegion.evaluate((element) => element.scrollHeight > element.clientHeight)).toBe(true);
  await retryRegion.evaluate((element) => element.scrollTo({ top: element.scrollHeight }));
  await expect(retryRegion.getByText("fictional-retry-file-18.zip")).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await retryRegion.scrollIntoViewIfNeeded();
  await expect.poll(
    () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth),
  ).toBe(0);
  await waitForToastAnnouncements(page);
  const scan = await new AxeBuilder({ page }).analyze();
  expect(scan.violations).toEqual([]);
});
