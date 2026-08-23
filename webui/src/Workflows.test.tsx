import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { queryClient } from "./lib/query";

const session = {
  authenticated: true,
  username: "owner",
  csrf_token: "csrf-token",
  created_at: "2026-07-21T00:00:00Z",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const projectSummary = {
  name: "Fixture",
  root: "/project",
  project_config: "/project/ktoolbox.toml",
  dotenv_files: [],
  version: "1.0.0",
  default_output: "downloads",
  resolved_default_output: "/project/downloads",
};

afterEach(() => {
  queryClient.clear();
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/");
  localStorage.clear();
});

describe("project workflows", () => {
  it("shows localized package details and safe official links", async () => {
    window.history.replaceState({}, "", "/about");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/about")) {
          return json({
            name: "KToolBox",
            version: "1.0.0",
            description: "Package summary",
            license: "BSD-3-Clause",
            authors: ["Ljzd-PRO"],
            python_version: "3.14.0",
            urls: {
              documentation: "https://ktoolbox.readthedocs.io/",
              repository: "https://github.com/Ljzd-PRO/KToolBox",
              issues: "https://github.com/Ljzd-PRO/KToolBox/issues",
            },
          });
        }
        throw new Error(`Unexpected request: ${path}`);
      }),
    );

    render(<BrowserRouter><App /></BrowserRouter>);

    expect(await screen.findByRole("heading", { name: "About", level: 1 })).toBeInTheDocument();
    expect(await screen.findByText("BSD-3-Clause")).toBeInTheDocument();
    expect(await screen.findByText("3.14.0")).toBeInTheDocument();
    expect(await screen.findByText("Ljzd-PRO")).toBeInTheDocument();
    const repository = screen.getByRole("link", { name: "Open Source repository" });
    expect(repository).toHaveAttribute("target", "_blank");
    expect(repository).toHaveAttribute("rel", "noopener noreferrer");
    expect(within(repository).getByText("https://github.com/Ljzd-PRO/KToolBox", { selector: "code" })).toBeInTheDocument();
  });

  it("explains structured task failures without exposing raw event JSON", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/tasks/task-failed");
    const failure = {
      code: "response_incompatible",
      stage: "work_list",
      message: "Response validation failed.",
      retryable: false,
      platform: "fanbox",
      creator_id: "demo-studio",
      file_name: null,
      http_status: null,
      operation: "list_creator_posts",
      fields: ["items.8.tags"],
    };
    const fileFailures = Array.from({ length: 6 }, (_, index) => ({
      code: "resource_not_found",
      stage: "file_request",
      message: "The upstream file is unavailable.",
      retryable: false,
      platform: "fanbox",
      creator_id: "demo-studio",
      file_name: `cover-${index + 1}.jpg`,
      http_status: 404,
      operation: null,
      fields: [],
    }));
    const task = {
      id: "task-failed",
      kind: "sync",
      status: "failed",
      spec: {
        kind: "sync",
        creators: [{ service: "fanbox", creator_id: "demo-studio", alias: null, enabled: true }],
        output: "downloads",
        save_creator_indices: true,
        mix_posts: null,
        start_time: null,
        end_time: null,
        offset: 0,
        length: null,
        keywords: [],
        keywords_exclude: [],
      },
      presentation: null,
      position: 1,
      revision: 1,
      progress: {
        queued_files: 0,
        processed_files: 0,
        completed_files: 0,
        existing_files: 0,
        failed_files: 0,
        transferred_bytes: 0,
        total_bytes: null,
        speed_bps: 0,
        eta_seconds: null,
        active_creators: [],
        active_downloads: {},
      },
      error: "1 creator failed, 0 files failed.",
      failure: {
        summary: "1 creator failed, 0 files failed.",
        creator_failures: 1,
        file_failures: fileFailures.length,
        items: [failure, ...fileFailures],
      },
      blocked_by: null,
      created_at: "2026-07-23T00:00:00Z",
      updated_at: "2026-07-23T00:00:01Z",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/project")) return json(projectSummary);
        if (path.endsWith("/tasks")) return json([task]);
        if (path.endsWith("/creators")) return json([]);
        if (path.includes("/tasks/task-failed/events")) {
          return json([{
            id: 1,
            task_id: "task-failed",
            event_type: "creator.finished",
            data: { failure },
            created_at: "2026-07-23T00:00:01Z",
          }]);
        }
        if (path.endsWith("/tasks/task-failed/attempts")) return json([]);
        throw new Error(`Unexpected request: ${path}`);
      }),
    );

    render(<BrowserRouter><App /></BrowserRouter>);

    expect(await screen.findByRole("heading", { name: "Why this task failed" })).toBeInTheDocument();
    expect(screen.getAllByText("Pawchive returned data in an unsupported format.").length).toBeGreaterThan(0);
    expect(screen.getByText("items.8.tags", { exact: false })).toBeInTheDocument();
    expect(screen.getByText(/Update KToolBox/)).toBeInTheDocument();
    expect(screen.getByText("cover-1.jpg")).toBeInTheDocument();
    expect(screen.getByText("cover-3.jpg")).toBeInTheDocument();
    expect(screen.queryByText("cover-4.jpg")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Show 3 more file details" }));
    expect(screen.getByText("cover-4.jpg")).toBeInTheDocument();
    expect(screen.getByText("cover-6.jpg")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Collapse file details" }));
    expect(screen.queryByText("cover-4.jpg")).not.toBeInTheDocument();
    expect(await screen.findByText("Creator finished")).toBeInTheDocument();
    expect(screen.queryByText(/"code":/)).not.toBeInTheDocument();
  });

  it("navigates from overview statistics with a durable filter", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/project")) {
          return json({ name: "Fixture", root: "/fixture", project_config: "/fixture/ktoolbox.toml", dotenv_files: [], version: "1.0.0" });
        }
        if (path.endsWith("/tasks")) return json([]);
        if (path.endsWith("/creators")) return json([]);
        throw new Error(`Unexpected request: ${path}`);
      }),
    );

    render(<BrowserRouter><App /></BrowserRouter>);
    await user.click(await screen.findByRole("link", { name: "Active tasks: 0" }));
    expect(window.location.pathname).toBe("/tasks");
    expect(window.location.search).toBe("?status=active");
    expect(await screen.findByRole("button", { name: /Active/ })).toBeInTheDocument();
  });

  it("renders the creator roster with readable labels", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/creators");
    let creatorEnabled = true;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = String(input);
      if (path.endsWith("/session")) return json(session);
      if (path.endsWith("/creators") && init?.method === "POST") {
        return json({ service: "patreon", creator_id: "new-creator", alias: "Reference", enabled: true });
      }
      if (path.endsWith("/creators")) {
        return json([{ service: "fanbox", creator_id: "42", alias: null, enabled: creatorEnabled, name: "Studio Sample" }]);
      }
      if (path.endsWith("/creators/fanbox/42") && init?.method === "PUT") {
        creatorEnabled = false;
        return json({ service: "fanbox", creator_id: "42", alias: null, enabled: false });
      }
      throw new Error(`Unexpected request: ${path}`);
    });
    vi.stubGlobal(
      "fetch",
      fetchMock,
    );

    const { container } = render(<BrowserRouter><App /></BrowserRouter>);

    expect(await screen.findByRole("heading", { name: "Creators" })).toBeInTheDocument();
    expect((await screen.findAllByText("Studio Sample")).length).toBeGreaterThan(0);
    const creatorHeaders = screen.getAllByRole("columnheader");
    expect(creatorHeaders.map((header) => header.textContent)).toEqual([
      "",
      "Creator name",
      "Creator ID",
      "Platform",
      "Note",
      "Included in full sync",
      "Actions",
    ]);
    expect(creatorHeaders.slice(1).every((header) => header.querySelector(".table-column-icon"))).toBe(true);
    expect(container.querySelectorAll(".platform-label-icon").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Add creator" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Edit fanbox:42" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "Remove fanbox:42" }).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /Actions Studio Sample/ })).not.toBeInTheDocument();
    const desktopSwitchCell = container.querySelector(".list-switch-cell");
    expect(screen.getAllByRole("switch", { name: "Enabled" }).some((control) => desktopSwitchCell?.contains(control))).toBe(true);

    await user.click(screen.getAllByRole("checkbox", { name: "Select Studio Sample" })[0]);
    await user.click(screen.getByRole("button", { name: "Disable 1" }));
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/creators/fanbox/42"),
      expect.objectContaining({ method: "PUT" }),
    );

    await user.click(screen.getByRole("button", { name: "Add creator" }));
    expect(screen.getByRole("button", { name: /Parse creator URL/ })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Pawchive creator URL" })).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: "Pawchive creator path" })).not.toBeInTheDocument();
    await user.type(screen.getByRole("textbox", { name: "Pawchive creator URL" }), "https://pawchive.pw/patreon/user/new-creator");
    await user.type(screen.getByRole("textbox", { name: "Note" }), "Reference");
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Save" }));
    const createRequest = fetchMock.mock.calls.find(([path, options]) =>
      String(path).endsWith("/creators") && options?.method === "POST"
    );
    expect(createRequest).toBeDefined();
    expect(JSON.parse(String(createRequest?.[1]?.body))).toEqual({
      service: "patreon",
      creator_id: "new-creator",
      alias: "Reference",
      enabled: true,
    });

    await user.click(screen.getByRole("button", { name: "Add creator" }));
    await user.click(screen.getByRole("button", { name: /Parse creator URL/ }));
    await user.click(await screen.findByRole("option", { name: "Enter platform and creator ID" }));
    expect(screen.getByRole("group", { name: "Pawchive creator path" })).toBeInTheDocument();
    expect(screen.getByText("/platform/user/creator ID", { selector: "code" })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Platform" })).not.toHaveAttribute("readonly");
    expect(screen.getByRole("textbox", { name: "Creator ID" })).not.toHaveAttribute("readonly");
    expect(screen.getByRole("textbox", { name: "Note" })).toBeInTheDocument();
    await user.click(within(screen.getByRole("dialog")).getAllByRole("button", { name: "Close" }).at(-1)!);

    await user.click(screen.getAllByRole("button", { name: "Edit fanbox:42" })[0]);
    expect(screen.getByRole("combobox", { name: "Platform" })).toHaveAttribute("readonly");
    expect(screen.getByRole("textbox", { name: "Creator ID" })).toHaveAttribute("readonly");
  }, 15_000);

  it("renders scoped blocker controls from project TOML", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/blockers");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/creators")) {
          return json([{ service: "fanbox", creator_id: "42", alias: null, enabled: true, name: "Studio Sample" }]);
        }
        if (path.endsWith("/blockers")) {
          return json({
            blockers: [{
              id: "daily-sharing",
              type: "field-match",
              enabled: true,
              scope: { mode: "creators", creators: ["fanbox:42"] },
              options: {
                rule: {
                  kind: "group",
                  mode: "any",
                  negate: false,
                  conditions: [{
                    kind: "field",
                    field: "title",
                    operator: "contains",
                    values: ["daily"],
                    expected: true,
                    case_sensitive: false,
                    negate: false,
                  }],
                },
              },
            }],
          });
        }
        throw new Error(`Unexpected request: ${path}`);
      }),
    );

    const { container } = render(<BrowserRouter><App /></BrowserRouter>);

    expect(await screen.findByRole("heading", { name: "Blockers" })).toBeInTheDocument();
    expect(await screen.findByText("daily-sharing")).toBeInTheDocument();
    expect(screen.getByText(/Selected creators: fanbox:42/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Remove blocker" })).toBeInTheDocument();
    expect(container.querySelector(".list-switch-cell")).toContainElement(screen.getByRole("switch", { name: "Rule enabled" }));

    await user.click(screen.getByRole("button", { name: "Edit" }));
    expect(screen.getByRole("textbox", { name: "Matcher type" })).toHaveValue("Field match");
    expect(screen.queryByRole("button", { name: /Matcher type/ })).not.toBeInTheDocument();
    expect(screen.getByRole("switch", { name: "Invert this group" })).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "Invert this condition" })).toBeInTheDocument();
  });

  it("renders typed configuration labels and docstring descriptions", async () => {
    window.history.replaceState({}, "", "/configuration");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.includes("/config/schema")) {
          return json({
            locale: "en",
            sections: { api: "Pawchive API" },
            fields: [
              {
                path: "api.timeout",
                env_name: "KTOOLBOX_API__TIMEOUT",
                section: "api",
                label: "API request timeout",
                description: "Pawchive API request timeout",
                json_schema: { type: "number", minimum: 0 },
                default: 5,
                value: 5,
                is_set: true,
                secret: false,
                source: "default",
                apply_mode: "next_task",
              },
              {
                path: "logger.level",
                env_name: "KTOOLBOX_LOGGER__LEVEL",
                section: "api",
                label: "Log level",
                description: "Minimum level written to the log.",
                json_schema: { type: "string", enum: ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"] },
                default: "DEBUG",
                value: "INFO",
                is_set: true,
                secret: false,
                source: "default",
                apply_mode: "next_task",
                choice_mode: "fixed",
                choices: ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"].map((value) => ({ value, label: value })),
              },
              {
                path: "webui.host",
                env_name: "KTOOLBOX_WEBUI__HOST",
                section: "api",
                label: "Listen address",
                description: "Address used by the WebUI server.",
                json_schema: { type: "string" },
                default: "0.0.0.0",
                value: "127.0.0.1",
                is_set: true,
                secret: false,
                source: "default",
                apply_mode: "restart",
                choice_mode: "suggested",
                choices: [
                  { value: "127.0.0.1", label: "127.0.0.1" },
                  { value: "0.0.0.0", label: "0.0.0.0" },
                ],
              },
              {
                path: "job.post_structure.external_links",
                env_name: "KTOOLBOX_JOB__POST_STRUCTURE__EXTERNAL_LINKS",
                section: "api",
                label: "External links file name",
                description: "File name used inside each work directory.",
                json_schema: { type: "string" },
                default: "external_links.txt",
                value: "external_links.txt",
                is_set: true,
                secret: false,
                source: "default",
                apply_mode: "next_task",
              },
              {
                path: "downloader.bucket_path",
                env_name: "KTOOLBOX_DOWNLOADER__BUCKET_PATH",
                section: "api",
                label: "Storage bucket path",
                description: "Directory used for content-addressed files.",
                json_schema: { type: "string", format: "path" },
                default: "/srv/bucket",
                value: "/srv/bucket",
                is_set: true,
                secret: false,
                source: "default",
                apply_mode: "next_task",
                path_selector: { kind: "directory", scope: "host", value_mode: "absolute" },
              },
              {
                path: "logger.path",
                env_name: "KTOOLBOX_LOGGER__PATH",
                section: "api",
                label: "Log directory",
                description: "Directory containing ktoolbox.log.",
                json_schema: { anyOf: [{ type: "string", format: "path" }, { type: "null" }] },
                default: null,
                value: "/var/log/ktoolbox",
                is_set: true,
                secret: false,
                source: "environment",
                apply_mode: "next_task",
                path_selector: { kind: "directory", scope: "host", value_mode: "absolute" },
              },
            ],
          });
        }
        if (path.includes("/config/dotenv/")) {
          return json({ name: "dotenv", path: "/project/.env", content: "", revision: "rev" });
        }
        if (path.endsWith("/config/project")) {
          return json({
            name: "project",
            path: "/project/ktoolbox.toml",
            content: "schema_version = 1\n",
            revision: "project-rev",
            configuration: { schema_version: 1, creators: [], blockers: [] },
          });
        }
        throw new Error(`Unexpected request: ${path}`);
      }),
    );

    const { container } = render(<BrowserRouter><App /></BrowserRouter>);

    expect(await screen.findByRole("heading", { name: "Global configuration" })).toBeInTheDocument();
    expect(await screen.findByText("API request timeout")).toBeInTheDocument();
    expect(screen.getByText("Pawchive API request timeout")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Browse the remote computer for Storage bucket path" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Browse the remote computer for Log directory" })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Log level$/ })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Listen address" })).toHaveValue("127.0.0.1");
    expect(screen.getByRole("combobox", { name: "Listen address" })).toHaveClass("font-mono");
    expect(screen.getByRole("textbox", { name: "External links file name" })).toHaveValue("external_links.txt");
    expect(screen.queryByRole("button", { name: "Browse the remote computer for External links file name" })).not.toBeInTheDocument();
    expect(screen.queryByText("api.timeout")).not.toBeInTheDocument();
    const saveBar = container.querySelector(".config-save-bar");
    expect(saveBar).toBeInTheDocument();
    expect(saveBar?.closest(".form-surface")).toBeInTheDocument();
    expect(container.querySelector('[data-slot="scroll-shadow"]')).not.toBeInTheDocument();
  });

  it("shows a readable cleanup preview without exposing the task UUID", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/tasks/task-uuid-readable");
    const task = {
      id: "task-uuid-readable",
      kind: "sync",
      status: "completed",
      spec: {
        kind: "sync",
        creators: [{ service: "fanbox", creator_id: "42", alias: null, enabled: true }],
        output: "downloads",
        save_creator_indices: true,
        mix_posts: null,
        start_time: null,
        end_time: null,
        offset: 0,
        length: null,
        keywords: [],
        keywords_exclude: [],
      },
      presentation: null,
      position: 1,
      revision: 1,
      progress: {
        queued_files: 2,
        processed_files: 2,
        completed_files: 2,
        existing_files: 0,
        failed_files: 0,
        transferred_bytes: 3072,
        total_bytes: 3072,
        speed_bps: 0,
        eta_seconds: null,
        active_creators: [],
        active_downloads: {},
        waiting_retries: {},
      },
      error: null,
      failure: null,
      blocked_by: null,
      created_at: "2026-07-26T00:00:00Z",
      updated_at: "2026-07-26T00:01:00Z",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/project")) return json(projectSummary);
        if (path.endsWith("/tasks")) return json([task]);
        if (path.endsWith("/creators")) {
          return json([{ service: "fanbox", creator_id: "42", alias: null, enabled: true, name: "Readable Creator" }]);
        }
        if (path.includes("/tasks/task-uuid-readable/events")) return json([]);
        if (path.endsWith("/tasks/task-uuid-readable/attempts")) return json([]);
        if (path.endsWith("/tasks/task-uuid-readable/cleanup-preview")) {
          return json({
            task_id: "task-uuid-readable",
            artifacts: [
              { path: "/project/downloads/Readable Creator/work.json", size: 1024, mtime_ns: 1, removable: true, reason: null },
              { path: "/project/downloads/Readable Creator/archive/file.zip", size: 2048, mtime_ns: 1, removable: true, reason: null },
            ],
            removable_files: 2,
            removable_bytes: 3072,
          });
        }
        throw new Error(`Unexpected request: ${path}`);
      }),
    );

    render(<BrowserRouter><App /></BrowserRouter>);

    expect(await screen.findByRole("button", { name: "Rerun" })).toBeInTheDocument();
    await user.click(await screen.findByRole("button", { name: "Delete" }));
    const dialog = await screen.findByRole("dialog", { name: "Delete task" });
    expect(within(dialog).getAllByText("Readable Creator").length).toBeGreaterThan(0);
    expect(within(dialog).getByText("downloads", { selector: "code" })).toBeInTheDocument();
    expect(within(dialog).getByText("2 files to delete")).toBeInTheDocument();
    expect(within(dialog).queryByText("task-uuid-readable")).not.toBeInTheDocument();
    await user.click(within(dialog).getByText("2 files to delete"));
    expect(within(dialog).getByText("Readable Creator/work.json")).toBeInTheDocument();
    expect(within(dialog).getByText("Readable Creator/archive/file.zip")).toBeInTheDocument();
    await user.click(within(dialog).getByRole("checkbox", { name: "Also delete unchanged files created by this task" }));
    expect(within(dialog).getByText(/Only files recorded as created by this task/)).toBeInTheDocument();
    expect(within(dialog).queryByText(/task-uuid-readable/)).not.toBeInTheDocument();
    expect(screen.queryByText(/task-uuid-readable/)).not.toBeInTheDocument();
  });

  it("identifies completed automatic syncs without offering incompatible actions", async () => {
    window.history.replaceState({}, "", "/tasks/task-auto");
    const task = {
      id: "task-auto",
      kind: "sync",
      status: "completed",
      spec: {
        kind: "sync",
        creators: [{ service: "fanbox", creator_id: "42", alias: null, enabled: true }],
        output: "downloads",
        save_creator_indices: true,
        mix_posts: null,
        download_file: false,
        start_time: null,
        end_time: null,
        offset: 0,
        length: 20,
        keywords: [],
        keywords_exclude: [],
      },
      presentation: null,
      automatic_origin: {
        plan_id: "daily",
        plan_name: "Daily sync",
        run_id: "run-1",
        windows: [{
          creator_key: "fanbox:42",
          start_at: null,
          end_at: "2026-07-26T00:00:00Z",
          timezone: "UTC",
          baseline: true,
        }],
      },
      position: 1,
      revision: 1,
      progress: {
        queued_files: 0,
        processed_files: 0,
        completed_files: 0,
        existing_files: 0,
        failed_files: 0,
        transferred_bytes: 0,
        total_bytes: null,
        speed_bps: 0,
        eta_seconds: null,
        active_creators: [],
        active_downloads: {},
        waiting_retries: {},
      },
      error: null,
      failure: null,
      blocked_by: null,
      created_at: "2026-07-26T00:00:00Z",
      updated_at: "2026-07-26T00:01:00Z",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/project")) return json(projectSummary);
        if (path.endsWith("/tasks")) return json([task]);
        if (path.endsWith("/creators")) {
          return json([{ service: "fanbox", creator_id: "42", alias: null, enabled: true, name: "Readable Creator" }]);
        }
        if (path.includes("/tasks/task-auto/events")) {
          return json([{
            id: 1,
            task_id: "task-auto",
            event_type: "creator.finished",
            data: {
              creator: "fanbox:42",
              fetched_posts: 20,
              accepted_posts: 20,
              queued_files: 0,
              completed_files: 0,
              existing_files: 0,
              failed_files: 0,
            },
            created_at: "2026-07-26T00:00:30Z",
          }]);
        }
        if (path.endsWith("/tasks/task-auto/attempts")) return json([]);
        throw new Error(`Unexpected request: ${path}`);
      }),
    );

    render(<BrowserRouter><App /></BrowserRouter>);

    const automaticSync = await screen.findByRole("link", { name: "Automatic sync: Daily sync" });
    expect(automaticSync).toHaveAttribute("href", "/auto-sync");
    expect(screen.getByRole("progressbar", { name: /Overall progress/ })).toHaveAttribute("aria-valuenow", "100");
    expect(await screen.findByText(/checked 20 works · accepted 20/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Rerun" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Edit" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
  });

  it("keeps streaming creator discovery indeterminate while the queue is still growing", async () => {
    window.history.replaceState({}, "", "/tasks/task-streaming");
    const task = {
      id: "task-streaming",
      kind: "sync",
      status: "running",
      spec: {
        kind: "sync",
        creators: [
          { service: "fanbox", creator_id: "1", alias: null, enabled: true },
          { service: "fanbox", creator_id: "2", alias: null, enabled: true },
        ],
        output: "downloads",
        save_creator_indices: true,
        mix_posts: null,
        download_file: true,
        start_time: null,
        end_time: null,
        offset: 0,
        length: 20,
        keywords: [],
        keywords_exclude: [],
      },
      presentation: null,
      automatic_origin: null,
      position: 1,
      revision: 1,
      progress: {
        queued_files: 70,
        processed_files: 50,
        completed_files: 47,
        existing_files: 0,
        failed_files: 3,
        transferred_bytes: 304087040,
        total_bytes: 335544320,
        speed_bps: 1572864,
        eta_seconds: 20,
        active_creators: ["fanbox:1", "fanbox:2"],
        active_downloads: {},
        waiting_retries: {},
      },
      error: null,
      failure: null,
      blocked_by: null,
      created_at: "2026-07-26T00:00:00Z",
      updated_at: "2026-07-26T00:01:00Z",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/project")) return json(projectSummary);
        if (path.endsWith("/tasks")) return json([task]);
        if (path.endsWith("/creators")) {
          return json([
            { service: "fanbox", creator_id: "1", alias: null, enabled: true, name: "Creator One" },
            { service: "fanbox", creator_id: "2", alias: null, enabled: true, name: "Creator Two" },
          ]);
        }
        if (path.includes("/tasks/task-streaming/events")) return json([]);
        if (path.endsWith("/tasks/task-streaming/attempts")) return json([]);
        throw new Error(`Unexpected request: ${path}`);
      }),
    );

    render(<BrowserRouter><App /></BrowserRouter>);

    expect(await screen.findByText("50 / 70")).toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: /Overall progress/ })).not.toHaveAttribute("aria-valuenow");
  });
});
