import { expect, test } from "@playwright/test";

test("legacy work-root attachments parse and preview correctly (#389)", async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await page.getByLabel("Username").fill("playwright");
  await page.getByLabel("Password", { exact: true }).fill("fixture-password");
  const migrationLoaded = page.waitForResponse((response) =>
    response.url().endsWith("/api/v1/naming/legacy-migration")
    && response.request().method() === "GET",
  );
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Overview", exact: true })).toBeVisible();
  if ((await (await migrationLoaded).json() as { pending: boolean }).pending) {
    await page.getByRole("dialog", { name: "Migrate legacy naming settings" })
      .getByRole("button", { name: "Ignore", exact: true }).click();
  }

  await page.getByRole("link", { name: "Naming format", exact: true }).click();
  await page.getByRole("tab", { name: "Legacy download conversion", exact: true }).click();
  await page.getByRole("tab", { name: "Paste configuration", exact: true }).click();
  await page.getByRole("textbox", { name: "Legacy .env naming settings" })
    .fill("KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./\n");
  const parsed = page.waitForResponse((response) => response.url().endsWith("/api/v1/naming/source/parse"));
  await page.getByRole("button", { name: "Parse configuration", exact: true }).click();
  const parsedResponse = await parsed;
  expect(parsedResponse.ok()).toBe(true);
  await expect(page.getByText("Legacy format parsed", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Scan old locations", exact: true })).toBeEnabled();

  await page.getByRole("tab", { name: "Directory structure", exact: true }).click();
  const attachments = page.getByRole("textbox", { name: "Attachments directory", exact: true });
  const originalDirectory = await attachments.inputValue();
  await attachments.fill("./");
  await page.getByRole("button", { name: "Save directory structure", exact: true }).click();
  const prompt = page.getByRole("dialog", { name: "Review existing downloads" });
  await prompt.getByRole("button", { name: "Ignore", exact: true }).click();
  await expect(prompt).toBeHidden();
  await page.getByRole("tab", { name: "Legacy download conversion", exact: true }).click();
  const tree = page.getByRole("tree", { name: "Directory tree preview" });
  const attachment = tree.getByRole("treeitem", { name: "1.png", exact: true });
  const cover = tree.getByRole("treeitem", { name: /cover\.jpg$/ });
  await expect(tree.getByRole("treeitem", { name: /^\.\/?$/ })).toHaveCount(0);
  await expect(attachment).toBeAttached();
  expect(await attachment.evaluate((element) => getComputedStyle(element).paddingInlineStart))
    .toBe(await cover.evaluate((element) => getComputedStyle(element).paddingInlineStart));
  await expect(page.locator("[data-slot='toast']")).toHaveCount(0, { timeout: 10_000 });

  for (const [width, height] of [[1440, 900], [1024, 768], [320, 700]]) {
    await page.setViewportSize({ width, height });
    await tree.scrollIntoViewIfNeeded();
    await expect(attachment).toBeVisible();
    await expect.poll(() => page.evaluate(() =>
      document.documentElement.scrollWidth - document.documentElement.clientWidth,
    )).toBe(0);
    await page.screenshot({ path: testInfo.outputPath(`root-attachments-${width}.png`) });
  }

  // Restore the shared offline fixture for the other browser tests.
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.getByRole("tab", { name: "Directory structure", exact: true }).click();
  await attachments.fill(originalDirectory);
  await page.getByRole("button", { name: "Save directory structure", exact: true }).click();
  await prompt.getByRole("button", { name: "Ignore", exact: true }).click();
  await expect(prompt).toBeHidden();
  expect(errors).toEqual([]);
});
