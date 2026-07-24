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

afterEach(() => {
  queryClient.clear();
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/");
  localStorage.clear();
});

describe("project workflows", () => {
  it("explains structured task failures without exposing raw event JSON", async () => {
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
        file_failures: 0,
        items: [failure],
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
    expect(container.querySelector(".list-switch-cell")).toContainElement(screen.getAllByRole("switch")[0]);

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
  });

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

    expect(await screen.findByRole("heading", { name: "Configuration" })).toBeInTheDocument();
    expect(await screen.findByText("API request timeout")).toBeInTheDocument();
    expect(screen.getByText("Pawchive API request timeout")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Browse the remote computer for Storage bucket path" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Browse the remote computer for Log directory" })).toBeDisabled();
    expect(screen.queryByText("api.timeout")).not.toBeInTheDocument();
    const saveBar = container.querySelector(".config-save-bar");
    expect(saveBar).toBeInTheDocument();
    expect(saveBar?.closest(".form-surface")).toBeInTheDocument();
    expect(container.querySelector('[data-slot="scroll-shadow"]')).not.toBeInTheDocument();
  });
});
