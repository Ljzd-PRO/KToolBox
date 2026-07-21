import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";


async function signIn(page: Page) {
  await page.goto("/");
  await page.getByLabel("Username").fill("playwright");
  await page.getByLabel("Password", { exact: true }).fill("fixture-password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Download operations at a glance" })).toBeVisible();
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


test("task lifecycle remains operable through pause resume and stop", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Tasks" }).click();
  await page.getByRole("button", { name: "Create task" }).click();
  await page.getByRole("button", { name: "Create task", exact: true }).last().click();
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
