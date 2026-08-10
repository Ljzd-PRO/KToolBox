import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

async function signIn(page: import("@playwright/test").Page) {
  await page.goto("/");
  await page.getByLabel("Username").fill("playwright");
  await page.getByLabel("Password", { exact: true }).fill("fixture-password");
  const migrationStatusLoaded = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/naming/legacy-migration") &&
      response.request().method() === "GET",
  );
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Overview", exact: true })).toBeVisible();
  const migrationStatus = (await (await migrationStatusLoaded).json()) as { pending: boolean };
  const migrationDialog = page.getByRole("dialog", { name: "Migrate legacy naming settings" });
  if (migrationStatus.pending) {
    await expect(migrationDialog).toBeVisible();
    await migrationDialog.getByRole("button", { name: "Ignore", exact: true }).click();
    await expect(migrationDialog).toBeHidden();
  }
}

test("automatic sync stays readable in a sidebar-constrained tablet layout", async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 768 });
  await signIn(page);
  await page.getByRole("link", { name: "Automatic sync", exact: true }).click();

  await expect(page.getByRole("heading", { level: 1, name: "Automatic sync", exact: true })).toBeVisible();
  await expect(page.getByRole("paragraph").filter({ hasText: "Daily studios" })).toBeVisible();
  await expect(page.getByRole("paragraph").filter({ hasText: "Weekly reference" })).toBeVisible();
  await expect(page.locator(".app-table-frame").first()).toBeHidden();
  await expect(page.getByRole("button", { name: "Run now" }).first()).toBeVisible();
  await expect(page.getByText("Period: Last 30 days", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: /Statistics period/ }).click();
  await page.getByRole("option", { name: "Last 14 days", exact: true }).click();
  await expect(page.getByText("Period: Last 14 days", { exact: true })).toBeVisible();
  await expect(page.getByRole("dialog", { name: "Statistics period" })).toBeHidden();
  await expect.poll(
    () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth),
  ).toBe(0);

  const scan = await new AxeBuilder({ page }).analyze();
  expect(scan.violations).toEqual([]);
});

test("automatic sync editor supports creator selection and both schedule modes", async ({ page }) => {
  await signIn(page);
  await page.getByRole("link", { name: "Automatic sync", exact: true }).click();
  await page.getByRole("button", { name: "New plan", exact: true }).click();

  const dialog = page.getByRole("dialog", { name: "New plan" });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("textbox", { name: "Plan ID" })).toHaveAttribute("readonly");
  await dialog.getByRole("textbox", { name: "Plan name" }).fill("Reference artists");
  await dialog.getByRole("checkbox", { name: "Demo Studio" }).check({ force: true });
  await expect(dialog.getByRole("checkbox", { name: "Demo Studio" })).toBeChecked();
  await expect(dialog.getByText("Selected creators: 1", { exact: true })).toBeVisible();

  await dialog.getByRole("tab", { name: "Advanced" }).click();
  const cron = dialog.getByRole("textbox", { name: "Cron expression" });
  await expect(cron).toHaveValue("0 3 * * *");
  await cron.fill("30 4 * * 1,3,5");
  await expect(dialog.getByText("Next three runs", { exact: true })).toBeVisible();

  await dialog.getByRole("button", { name: /Cron schedule/ }).click();
  await page.getByRole("option", { name: "Fixed interval", exact: true }).click();
  await expect(dialog.getByRole("textbox", { name: "Repeat every" })).toHaveValue("24");
  await expect(dialog.getByRole("button", { name: /Hours/ })).toBeVisible();
  await expect(dialog.getByRole("switch", { name: "No start date" })).not.toBeChecked();
  await expect(dialog.getByRole("switch", { name: "Download primary file (cover)" })).toBeChecked();

  await dialog.getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(dialog).toBeHidden();
});
