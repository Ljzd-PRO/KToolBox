import { expect, test, type Page } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";

const auditDirectory = process.env.KTOOLBOX_I18N_AUDIT_DIR;

const locales = [
  { code: "zh-CN", create: "创建任务", heading: "概览" },
  { code: "zh-Hant", create: "建立工作", heading: "概覽" },
  { code: "en", create: "Create task", heading: "Overview" },
  { code: "ja", create: "タスクを作成", heading: "概要" },
  { code: "ko", create: "작업 만들기", heading: "개요" },
  { code: "fr", create: "Créer une tâche", heading: "Aperçu" },
  { code: "ru", create: "Создать задачу", heading: "Обзор" },
] as const;

const routes = [
  ["overview", "/"],
  ["tasks", "/tasks"],
  ["creators", "/creators"],
  ["posts", "/posts"],
  ["blockers", "/blockers"],
  ["configuration", "/configuration"],
  ["system", "/system"],
] as const;

const viewports = [
  { id: "1440x900", width: 1440, height: 900 },
  { id: "390x844", width: 390, height: 844 },
] as const;

const themes = ["light", "dark"] as const;

test.skip(!auditDirectory, "Set KTOOLBOX_I18N_AUDIT_DIR to capture the visual review matrix.");

async function signIn(page: Page) {
  await page.goto("/");
  await page.getByLabel("Username").fill("playwright");
  await page.getByLabel("Password", { exact: true }).fill("fixture-password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Overview", exact: true })).toBeVisible();
}

async function applyPresentation(page: Page, locale: string, theme: "light" | "dark") {
  await page.evaluate(
    ([nextLocale, nextTheme]) => {
      localStorage.setItem("ktoolbox-language", nextLocale);
      localStorage.setItem("ktoolbox-theme", nextTheme);
      localStorage.setItem("ktoolbox-theme-color", "emerald");
    },
    [locale, theme],
  );
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("lang", locale);
  await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
}

async function capture(page: Page, name: string, fullPage = true) {
  if (!auditDirectory) throw new Error("KTOOLBOX_I18N_AUDIT_DIR is required");
  await page.waitForTimeout(250);
  await expect
    .poll(() => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth))
    .toBeLessThanOrEqual(0);
  await page.screenshot({ fullPage, path: join(auditDirectory, `${name}.png`) });
}

test("captures the seven-language responsive theme matrix", async ({ page }) => {
  test.setTimeout(12 * 60_000);
  if (!auditDirectory) return;
  await mkdir(auditDirectory, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 900 });
  await signIn(page);

  const manifest: Array<Record<string, string | number | boolean>> = [];
  for (const locale of locales) {
    for (const theme of themes) {
      await applyPresentation(page, locale.code, theme);
      for (const viewport of viewports) {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        for (const [pageName, route] of routes) {
          await page.goto(route);
          await expect(page.locator("main")).toBeVisible();
          const name = `${pageName}__page__${locale.code}__${viewport.id}__${theme}-emerald`;
          await capture(page, name);
          manifest.push({
            kind: "page",
            locale: locale.code,
            page: pageName,
            route,
            theme,
            viewport: viewport.id,
            fullPage: true,
            file: `${name}.png`,
          });
        }
      }
    }

    await page.setViewportSize({ width: 1024, height: 768 });
    await applyPresentation(page, locale.code, "light");
    await page.goto("/tasks");
    await page.getByRole("button", { name: locale.create, exact: true }).click();
    await expect(page.getByRole("dialog", { name: locale.create, exact: true })).toBeVisible();
    const taskName = `tasks__create-modal__${locale.code}__1024x768__light-emerald`;
    await capture(page, taskName, false);
    manifest.push({ kind: "overlay", locale: locale.code, page: "tasks", route: "/tasks", theme: "light", viewport: "1024x768", fullPage: false, file: `${taskName}.png` });
    await page.keyboard.press("Escape");

    const languageTrigger = page.locator("header").locator('[data-slot="dropdown-trigger"]');
    await expect(languageTrigger).toHaveCount(1);
    await languageTrigger.click();
    const languageName = `shell__language-menu__${locale.code}__1024x768__light-emerald`;
    await capture(page, languageName, false);
    manifest.push({ kind: "overlay", locale: locale.code, page: "shell", route: "/tasks", theme: "light", viewport: "1024x768", fullPage: false, file: `${languageName}.png` });
    await page.keyboard.press("Escape");

    await page.setViewportSize({ width: 390, height: 844 });
    await applyPresentation(page, locale.code, "dark");
    await page.goto("/tasks");
    await page.getByRole("button", { name: locale.create, exact: true }).click();
    const taskDialog = page.getByRole("dialog", { name: locale.create, exact: true });
    const browseButton = taskDialog.locator('button:has(svg.tabler-icon-folder-open)');
    await expect(browseButton).toHaveCount(1);
    await browseButton.click();
    await expect(page.locator(".remote-path-picker-container")).toBeVisible();
    const pickerName = `tasks__path-picker__${locale.code}__390x844__dark-emerald`;
    await capture(page, pickerName, false);
    manifest.push({ kind: "overlay", locale: locale.code, page: "tasks", route: "/tasks", theme: "dark", viewport: "390x844", fullPage: false, file: `${pickerName}.png` });
    await page.keyboard.press("Escape");
    await page.keyboard.press("Escape");
  }

  await writeFile(
    join(auditDirectory, "capture-manifest.json"),
    `${JSON.stringify({ generatedAt: new Date().toISOString(), captures: manifest }, null, 2)}\n`,
  );
});
