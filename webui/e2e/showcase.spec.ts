import { expect, test, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { join } from "node:path";

const showcaseDirectory = process.env.KTOOLBOX_SHOWCASE_DIR;

test.skip(!showcaseDirectory, "Set KTOOLBOX_SHOWCASE_DIR to generate documentation screenshots.");

async function signIn(page: Page) {
  await page.goto("/");
  await page.getByLabel("Username").fill("playwright");
  await page.getByLabel("Password", { exact: true }).fill("fixture-password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Overview", exact: true })).toBeVisible();

  const languageTrigger = page.locator('[data-slot="dropdown-trigger"]').first();
  await languageTrigger.click();
  await page.getByRole("menuitemradio", { name: "简体中文", exact: true }).click();
  await expect(page.getByRole("heading", { name: "概览", exact: true })).toBeVisible();
}

async function capture(page: Page, name: string, fullPage = true) {
  if (!showcaseDirectory) return;
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
  await expect(page.locator('[data-slot="skeleton"]')).toHaveCount(0, { timeout: 15_000 });
  await page.waitForTimeout(400);
  await page.screenshot({
    animations: "disabled",
    fullPage,
    path: join(showcaseDirectory, name),
  });
}

test("generate documentation showcase screenshots", async ({ page }) => {
  if (!showcaseDirectory) return;
  await mkdir(showcaseDirectory, { recursive: true });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.setViewportSize({ width: 1440, height: 900 });
  await signIn(page);

  await page.goto("/tasks");
  await page.getByRole("button", { name: "创建任务", exact: true }).click();
  let taskDialog = page.getByRole("dialog", { name: "创建任务", exact: true });
  await taskDialog.getByRole("tab", { name: "下载作品", exact: true }).click();
  await taskDialog
    .getByRole("textbox", { name: "Pawchive 作品 URL" })
    .fill("https://pawchive.pw/fanbox/user/476249/post/12301669");
  await taskDialog.getByRole("textbox", { name: "输出目录" }).fill("showcase-post");
  await taskDialog.getByRole("button", { name: "创建任务", exact: true }).click();
  await expect(page.getByRole("heading", { name: "任务详情", exact: true })).toBeVisible();
  await expect(page.getByText("已完成", { exact: true }).first()).toBeVisible({ timeout: 15_000 });
  const completedTaskId = page.url().split("/").at(-1);
  await page.evaluate(async (taskId) => {
    const session = await fetch("/api/v1/session").then((response) => response.json());
    const task = await fetch(`/api/v1/tasks/${taskId}`).then((response) => response.json());
    const response = await fetch(`/api/v1/tasks/${taskId}`, {
      body: JSON.stringify({
        spec: task.spec,
        presentation: {
          creator_name: "ミュー",
          target_key: "download/fanbox/476249/12301669/",
          title: "らくがき",
        },
      }),
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": session.csrf_token,
      },
      method: "PATCH",
    });
    if (!response.ok) throw new Error(`Unable to attach showcase metadata: ${response.status}`);
  }, completedTaskId);

  await page.goto("/tasks");
  await page.getByRole("button", { name: "创建任务", exact: true }).click();
  taskDialog = page.getByRole("dialog", { name: "创建任务", exact: true });
  await taskDialog.getByRole("textbox", { name: "输出目录" }).fill("live-layout-fixture");
  await taskDialog.getByRole("button", { name: "创建任务", exact: true }).click();
  await expect(page.getByRole("heading", { name: "任务详情", exact: true })).toBeVisible();
  await expect(page.getByText("运行中", { exact: true })).toBeVisible();
  await expect(page.getByRole("region", { name: "活动下载" })).toContainText(
    "Oeg5AiNkge3N7kDPHqve3zFR.jpeg",
    { timeout: 10_000 },
  );
  const taskDetailsUrl = page.url();

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "概览", exact: true })).toBeVisible();
  await capture(page, "40-overview-showcase-desktop-light.png");

  await page.goto("/creators");
  await expect(page.getByRole("heading", { name: "作者", exact: true })).toBeVisible();
  await expect(page.getByText("ミュー", { exact: true }).first()).toBeVisible();
  await capture(page, "41-creators-showcase-desktop-light.png");

  await page.goto("/auto-sync");
  await expect(page.getByRole("heading", { name: "自动同步", exact: true })).toBeVisible();
  await expect(page.getByText("每日更新检查", { exact: true }).first()).toBeVisible();
  await capture(page, "42-auto-sync-showcase-desktop-light.png");

  await page.goto("/tasks");
  await expect(page.getByRole("heading", { name: "任务", exact: true })).toBeVisible();
  await expect(page.getByText("ミュー", { exact: true }).first()).toBeVisible();
  await capture(page, "43-task-queue-showcase-desktop-light.png");

  await page.goto(taskDetailsUrl);
  await page.getByRole("button", { name: "切换为深色主题", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.mouse.move(720, 180);
  await page.waitForTimeout(600);
  await capture(page, "44-task-live-showcase-desktop-dark.png");

  await page.setViewportSize({ width: 390, height: 844 });
  await capture(page, "45-task-live-showcase-mobile-dark.png", false);
});
