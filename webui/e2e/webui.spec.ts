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


test("authenticated shell is accessible in desktop and mobile themes", async ({ page }) => {
  await signIn(page);
  const desktopScan = await new AxeBuilder({ page }).analyze();
  expect(desktopScan.violations).toEqual([]);

  await page.getByRole("button", { name: "Use dark theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: "Use emerald accent" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme-color", "emerald");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(page.getByRole("link", { name: "Tasks", exact: true })).toBeVisible();
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
  await page.getByRole("button", { name: "Switch language" }).click();
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
  const postPath = formSurface.getByRole("group", { name: "Pawchive post path" });
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

  await expect(tableFrame.getByText("2 creators", { exact: true })).toBeVisible();
  await expect(tableFrame.getByText(/demo-studio/)).toBeVisible();
  const desktopActions = page.locator(".task-action-grid:visible button");
  await expect(desktopActions).toHaveCount(7);
  for (const label of ["Task details", "Stop", "Edit", "Move up", "Move down", "Delete"]) {
    await expect(page.getByRole("button", { name: label })).toBeVisible();
  }
  await expect(page.getByRole("button", { name: "Actions" })).toHaveCount(0);

  await page.setViewportSize({ width: 390, height: 844 });
  const mobileCard = page.locator(".task-mobile-card:visible");
  await expect(mobileCard).toBeVisible();
  const mobileActions = mobileCard.locator(".task-action-grid button");
  await expect(mobileActions).toHaveCount(7);
  const mobileActionBox = await mobileCard.locator(".task-action-grid").boundingBox();
  expect(mobileActionBox?.height ?? 0).toBeGreaterThan(80);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);

  await page.setViewportSize({ width: 768, height: 1024 });
  await expect(page.locator(".app-table-frame:visible")).toHaveCount(0);
  await expect(page.locator(".task-mobile-card:visible")).toBeVisible();
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
  await picker.getByRole("textbox", { name: "Folder name" }).fill("e2e-created");
  await picker.getByRole("button", { name: "Add" }).click();
  await expect(picker.getByRole("textbox", { name: "Remote path" })).toHaveValue(/[/\\]e2e-created$/);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
  expect(await picker.evaluate((element) => element.scrollWidth - element.clientWidth)).toBe(0);
  const pickerScan = await new AxeBuilder({ page }).include(".remote-path-picker-container").analyze();
  expect(pickerScan.violations).toEqual([]);
  await picker.getByRole("button", { name: "Select directory" }).click();
  await taskDialog.getByRole("button", { name: "Cancel" }).click();

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.getByRole("link", { name: "Configuration" }).click();
  await page.getByRole("button", { name: /Configuration section/ }).click();
  await page.getByRole("option", { name: "File downloads" }).click();
  const bucketBrowse = page.getByRole("button", { name: "Browse the remote computer for Storage bucket path" });
  await bucketBrowse.click();
  const hostPicker = page.getByRole("dialog", { name: "Storage bucket path" });
  await expect(hostPicker.getByText("Remote computer")).toBeVisible();
  await hostPicker.getByRole("button", { name: /Quick location/ }).click();
  const homeOption = page.getByRole("option", { name: "Home" });
  await expect(homeOption).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(homeOption).not.toBeVisible();
  await page.keyboard.press("Escape");
  await expect(hostPicker).not.toBeVisible();
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
  await capture("tasks__directory-picker__dark-emerald", 320, 700);
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
  await capture("configuration__host-picker__dark-emerald", 1440, 900);
});


test("roster blockers and configuration keep controls aligned and visible", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Creators", exact: true }).click();
  await expect(page).toHaveURL(/\/creators$/);
  await expect(page.getByRole("columnheader", { name: "Creator name" })).toBeVisible();

  const creatorRow = page.getByRole("row").filter({ hasText: "Demo Studio" });
  expect(await page.getByRole("columnheader").allTextContents()).toEqual([
    "Creator name",
    "Creator ID",
    "Platform",
    "Note",
    "Status",
    "Actions",
  ]);
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
  await disabledCreatorSwitch.press("Space");
  await expect(creatorRow.getByRole("switch", { name: "Enabled" })).toBeVisible();

  await page.getByRole("button", { name: "Add creator" }).click();
  const addCreatorDialog = page.getByRole("dialog", { name: "Add creator" });
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

  const blockerCard = page.getByRole("heading", { name: "daily-sharing" }).locator("xpath=ancestor::section");
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
