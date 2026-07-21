import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const browserErrors = new WeakMap<Page, string[]>();

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
  await expect(page.getByRole("heading", { name: "Download operations at a glance" })).toBeVisible();
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
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(page.getByRole("link", { name: "Tasks" })).toBeVisible();
  await page.waitForTimeout(600);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
  const mobileScan = await new AxeBuilder({ page }).analyze();
  expect(mobileScan.violations).toEqual([]);
});


test("HeroUI tables and forms preserve their visual hierarchy", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Tasks" }).click();
  await page.getByRole("button", { name: "Create task" }).click();
  const formSurface = page.locator(".app-form-modal-surface");
  const formScroll = page.locator(".app-form-modal-scroll");
  const formActions = page.locator(".app-form-modal-actions");
  await expect(formSurface).toBeVisible();
  await expect(formActions).toBeVisible();
  await expect(formSurface.locator(".field-label-icon")).not.toHaveCount(0);
  await expect(formSurface.locator('[data-slot="switch-icon"]')).toHaveCount(0);

  const switchContent = formSurface.locator('[data-slot="switch-content"]').filter({ hasText: "All enabled creators" });
  const switchControl = switchContent.locator('[data-slot="switch-control"]');
  const switchLabel = switchContent.locator('[data-slot="label"]');
  await expect(switchControl).toHaveCount(1);
  const [controlBox, labelBox] = await Promise.all([switchControl.boundingBox(), switchLabel.boundingBox()]);
  expect(controlBox).not.toBeNull();
  expect(labelBox).not.toBeNull();
  expect(Math.abs((controlBox?.y ?? 0) - (labelBox?.y ?? 0))).toBeLessThan(2);
  expect(controlBox?.x ?? 0).toBeLessThan(labelBox?.x ?? 0);

  const startDateCheckbox = formSurface.getByRole("checkbox", { name: "Apply start date" });
  const startDateRoot = startDateCheckbox.locator('xpath=ancestor::*[@data-slot="checkbox"]');
  await expect(startDateCheckbox).not.toBeChecked();
  await expect(startDateRoot.locator('[data-slot="checkbox-indicator"]')).toHaveCount(0);
  await startDateCheckbox.press("Space");
  await expect(startDateCheckbox).toBeChecked();
  await expect(startDateRoot.locator('[data-slot="checkbox-indicator"]')).toHaveCount(1);
  await startDateCheckbox.press("Space");

  const [scrollBox, actionBox] = await Promise.all([formScroll.boundingBox(), formActions.boundingBox()]);
  expect(scrollBox).not.toBeNull();
  expect(actionBox).not.toBeNull();
  expect(Math.abs((scrollBox?.y ?? 0) + (scrollBox?.height ?? 0) - (actionBox?.y ?? 0))).toBeLessThan(1);
  expect(await formSurface.locator(".app-form-modal-actions").count()).toBe(1);
  expect(await page.locator('[data-slot="modal-footer"]').count()).toBe(0);

  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
  await page.waitForTimeout(600);
  const modalScan = await new AxeBuilder({ page }).analyze();
  expect(modalScan.violations).toEqual([]);

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.getByLabel("Output directory").fill("visual-hierarchy-downloads");
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

  await expect(tableFrame.getByText("1 creator", { exact: true })).toBeVisible();
  await expect(tableFrame.getByText("Demo Studio", { exact: true })).toBeVisible();
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
});


test("roster blockers and configuration keep controls aligned and visible", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Creators" }).click();

  const creatorRow = page.getByRole("row").filter({ hasText: "Demo Studio" });
  await expect(creatorRow.getByRole("button", { name: "Edit Demo Studio" })).toBeVisible();
  await expect(creatorRow.getByRole("button", { name: "Remove Demo Studio" })).toBeVisible();
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

  await page.getByRole("link", { name: "Blockers" }).click();
  await page.getByRole("button", { name: "Add blocker" }).click();
  await page.getByRole("textbox", { name: /Rule ID/ }).fill("daily-sharing");
  await page.getByRole("textbox", { name: "Values" }).fill("fictional-daily");
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

  await page.getByRole("link", { name: "Configuration" }).click();
  const saveBar = page.locator(".config-save-bar");
  await expect(saveBar).toBeVisible();
  expect(await saveBar.evaluate((element) => Boolean(element.closest(".form-surface")))).toBe(true);
  await page.setViewportSize({ width: 390, height: 844 });
  const tabsScroller = page.locator('[data-slot="scroll-shadow"]');
  expect(await tabsScroller.evaluate((element) => element.scrollWidth - element.clientWidth)).toBe(0);
  await expect(page.getByRole("button", { name: "Scroll tabs right" })).not.toBeVisible();
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);
});


test("task lifecycle remains operable through pause resume and stop", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Tasks" }).click();
  await page.getByRole("button", { name: "Create task" }).click();
  await page.getByRole("dialog", { name: "Create task" }).getByRole("button", { name: "Create task" }).click();
  await expect(page.getByRole("heading", { name: "Task details" })).toBeVisible();
  await expect(page.getByText("Running", { exact: true })).toBeVisible();
  await expect(page.getByTitle(/KiB\/s|MiB\/s/)).toBeVisible();

  await page.getByRole("button", { name: "Pause" }).click();
  await expect(page.getByText("Paused", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Resume" }).click();
  await expect(page.getByText("Running", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Stop" }).click();
  await expect(page.getByText("Stopped", { exact: true })).toBeVisible();
});
