import AxeBuilder from "@axe-core/playwright";
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

test("adds a temporary creator from a secondary task modal", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await signIn(page);
  await page.getByRole("link", { name: "Tasks", exact: true }).click();
  await page.getByRole("button", { name: "Create task", exact: true }).click();

  const taskDialog = page.getByRole("dialog", { name: "Create task" });
  await taskDialog.getByText("All enabled creators", { exact: true }).click();
  await taskDialog.getByRole("button", { name: "Add temporary creator" }).click();

  const creatorDialog = page.getByRole("dialog", { name: "Add temporary creator" });
  await expect(creatorDialog).toBeVisible();
  await creatorDialog
    .getByRole("textbox", { name: "Pawchive creator URL" })
    .fill("https://pawchive.pw/patreon/user/temporary-42");
  await creatorDialog.getByRole("textbox", { name: "Note" }).fill("Guest studio");
  await page.waitForTimeout(400);
  const accessibility = await new AxeBuilder({ page }).analyze();
  expect(accessibility.violations).toEqual([]);
  await page.screenshot({
    path: testInfo.outputPath("temporary-creator-secondary-desktop.png"),
  });
  await creatorDialog.getByRole("button", { name: "Add to task" }).click();

  await expect(creatorDialog).toBeHidden();
  await expect(taskDialog.getByText("Temporary", { exact: true })).toBeVisible();
  await expect(taskDialog.getByRole("checkbox", { name: /Guest studio/ })).toBeChecked();
  await page.waitForTimeout(250);
  await page.screenshot({
    path: testInfo.outputPath("temporary-creator-selected-desktop.png"),
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await taskDialog.getByRole("button", { name: "Add temporary creator" }).click();
  const mobileCreatorDialog = page.getByRole("dialog", { name: "Add temporary creator" });
  await expect(mobileCreatorDialog).toBeVisible();
  await expect.poll(
    () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth),
  ).toBe(0);
  await page.waitForTimeout(400);
  await page.screenshot({
    path: testInfo.outputPath("temporary-creator-secondary-mobile.png"),
  });
  await mobileCreatorDialog.getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(taskDialog).toBeVisible();
  await taskDialog.getByRole("checkbox", { name: /Guest studio/ }).scrollIntoViewIfNeeded();
  await page.waitForTimeout(250);
  await page.screenshot({
    path: testInfo.outputPath("temporary-creator-selected-mobile.png"),
  });

  const taskRequest = page.waitForRequest(
    (request) => request.url().endsWith("/api/v1/tasks") && request.method() === "POST",
  );
  await taskDialog.getByRole("button", { name: "Create task", exact: true }).click();
  const payload = (await taskRequest).postDataJSON() as {
    spec: { creators: Array<Record<string, unknown>> };
  };
  expect(payload.spec.creators).toEqual([
    {
      service: "patreon",
      creator_id: "temporary-42",
      alias: "Guest studio",
      enabled: true,
    },
  ]);
});
