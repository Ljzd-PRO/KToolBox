import { expect, test, type Page } from "@playwright/test";

async function signIn(page: Page) {
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
    await migrationDialog.getByRole("button", { name: "Ignore", exact: true }).click();
    await expect(migrationDialog).toBeHidden();
  }
}

test("primary cover controls stay clear across task, schedule, and naming workflows", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await signIn(page);
  await page.getByRole("link", { name: "Tasks", exact: true }).click();
  await page.getByRole("button", { name: "Create task", exact: true }).click();

  const taskDialog = page.getByRole("dialog", { name: "Create task" });
  const syncCover = taskDialog.getByRole("switch", { name: "Download primary file (cover)" });
  await expect(syncCover).toBeChecked();
  await syncCover.scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  await page.screenshot({
    path: testInfo.outputPath("primary-cover-task-desktop.png"),
  });

  await taskDialog.getByRole("tab", { name: "Download post", exact: true }).click();
  const downloadCover = taskDialog.getByRole("switch", { name: "Download primary file (cover)" });
  await expect(downloadCover).toBeChecked();
  await page.setViewportSize({ width: 390, height: 844 });
  await downloadCover.scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  await expect.poll(
    () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth),
  ).toBe(0);
  await page.screenshot({
    path: testInfo.outputPath("primary-cover-task-mobile.png"),
  });
  await taskDialog.getByRole("button", { name: "Cancel", exact: true }).click();

  await page.setViewportSize({ width: 1024, height: 768 });
  await page.getByRole("link", { name: "Automatic sync", exact: true }).click();
  await page.getByRole("button", { name: "New plan", exact: true }).click();
  const planDialog = page.getByRole("dialog", { name: "New plan" });
  const scheduledCover = planDialog.getByRole("switch", { name: "Download primary file (cover)" });
  await expect(scheduledCover).toBeChecked();
  await scheduledCover.scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  await page.screenshot({
    path: testInfo.outputPath("primary-cover-automatic-sync.png"),
  });
  await planDialog.getByRole("button", { name: "Cancel", exact: true }).click();

  await page.getByRole("link", { name: "Naming format", exact: true }).click();
  await page.getByRole("tab", { name: "Naming templates", exact: true }).click();
  await expect(page.getByText("Primary file template (cover)", { exact: true })).toBeVisible();
});
