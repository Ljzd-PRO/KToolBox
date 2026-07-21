import { render, screen } from "@testing-library/react";
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

describe("task and post workflows", () => {
  it("shows persisted task speed, active files, and event history", async () => {
    window.history.replaceState({}, "", "/tasks/task-1");
    const task = {
      id: "task-1",
      kind: "download",
      status: "running",
      position: 1,
      revision: 0,
      spec: {
        kind: "download",
        service: "fanbox",
        creator_id: "42",
        post_id: "99",
        output: "/project/downloads",
        dump_post_data: true,
      },
      presentation: {
        target_key: "download/fanbox/42/99/",
        title: "Fictional fixture",
        creator_name: "Demo Studio",
      },
      progress: {
        queued_files: 2,
        processed_files: 1,
        completed_files: 1,
        existing_files: 0,
        failed_files: 0,
        transferred_bytes: 2048,
        total_bytes: 4096,
        speed_bps: 2048,
        eta_seconds: 1,
        active_creators: ["fanbox:42"],
        active_downloads: {
          file: {
            creator_key: "fanbox:42",
            filename: "a-very-long-but-safe-fixture-name.zip",
            total: 2048,
            completed: 1024,
            speed_bps: 1024,
          },
        },
      },
      error: null,
      blocked_by: null,
      created_at: "2026-07-21T00:00:00Z",
      updated_at: "2026-07-21T00:01:00Z",
    };
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const path = String(input);
      if (path.endsWith("/session")) return json(session);
      if (path.endsWith("/tasks")) return json([task]);
      if (path.endsWith("/creators")) return json([]);
      if (path.includes("/tasks/task-1/events")) {
        return json([{ id: 1, task_id: "task-1", event_type: "task.log", data: { level: "info", message: "fixture ready" }, created_at: "2026-07-21T00:00:30Z" }]);
      }
      if (path.endsWith("/tasks/task-1/attempts")) return json([]);
      throw new Error(`Unexpected request: ${path}`);
    }));

    render(<BrowserRouter><App /></BrowserRouter>);

    expect(await screen.findByRole("heading", { name: "Task details" })).toBeInTheDocument();
    expect(screen.getByText("Fictional fixture")).toBeInTheDocument();
    expect(screen.getByText("2.00 KiB/s")).toBeInTheDocument();
    expect(screen.getByText("a-very-long-but-safe-fixture-name.zip")).toBeInTheDocument();
    expect(await screen.findByText(/fixture ready/)).toBeInTheDocument();
  });

  it("shows recognizable task targets with every queue action directly available", async () => {
    window.history.replaceState({}, "", "/tasks");
    const progress = {
      queued_files: 4,
      processed_files: 2,
      completed_files: 2,
      existing_files: 0,
      failed_files: 0,
      transferred_bytes: 2048,
      total_bytes: 4096,
      speed_bps: 2048,
      eta_seconds: 1,
      active_creators: [],
      active_downloads: {},
    };
    const tasks = [
      {
        id: "download-task",
        kind: "download",
        status: "running",
        position: 1,
        revision: 1,
        spec: {
          kind: "download",
          service: "fanbox",
          creator_id: "42",
          post_id: "99",
          revision_id: "3",
          output: "/project/downloads/a-very-long-output-folder",
          dump_post_data: true,
        },
        presentation: {
          target_key: "download/fanbox/42/99/3",
          title: "Fictional cover study",
          creator_name: "Demo Studio",
        },
        progress,
        error: null,
        blocked_by: null,
        created_at: "2026-07-21T00:00:00Z",
        updated_at: "2026-07-21T00:01:00Z",
      },
      {
        id: "sync-task",
        kind: "sync",
        status: "completed",
        position: 2,
        revision: 1,
        spec: {
          kind: "sync",
          creators: [
            { service: "fanbox", creator_id: "demo-studio", alias: "Demo Studio", enabled: true },
            { service: "patreon", creator_id: "type-lab", alias: "Type Lab", enabled: true },
          ],
          output: "/project/downloads",
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
        progress: { ...progress, speed_bps: 0 },
        error: null,
        blocked_by: null,
        created_at: "2026-07-21T00:02:00Z",
        updated_at: "2026-07-21T00:03:00Z",
      },
    ];
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const path = String(input);
      if (path.endsWith("/session")) return json(session);
      if (path.endsWith("/tasks")) return json(tasks);
      if (path.endsWith("/creators")) return json([]);
      throw new Error(`Unexpected request: ${path}`);
    }));

    render(<BrowserRouter><App /></BrowserRouter>);

    expect(await screen.findAllByText("Fictional cover study")).toHaveLength(2);
    expect(screen.getAllByText("Demo Studio · fanbox:42 · #99 · rev. 3")).toHaveLength(2);
    expect(screen.getAllByText("2 creators")).toHaveLength(2);
    expect(screen.getAllByText("Demo Studio · Type Lab")).toHaveLength(2);
    expect(screen.getAllByRole("button", { name: "Task details" }).length).toBeGreaterThanOrEqual(4);
    expect(screen.getAllByRole("button", { name: "Pause" }).length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByRole("button", { name: "Resume" }).length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByRole("button", { name: "Stop" }).length).toBeGreaterThanOrEqual(4);
    expect(screen.getAllByRole("button", { name: "Edit" }).length).toBeGreaterThanOrEqual(4);
    expect(screen.getAllByRole("button", { name: "Move up" }).length).toBeGreaterThanOrEqual(4);
    expect(screen.getAllByRole("button", { name: "Move down" }).length).toBeGreaterThanOrEqual(4);
    expect(screen.getAllByRole("button", { name: "Delete" }).length).toBeGreaterThanOrEqual(4);
    expect(screen.getAllByRole("button", { name: "Move up" }).some((button) => button.getAttribute("aria-disabled") === "true")).toBe(true);
    expect(screen.getAllByRole("button", { name: "Delete" }).some((button) => button.getAttribute("aria-disabled") === "true")).toBe(true);
    expect(screen.queryByRole("button", { name: "Actions" })).not.toBeInTheDocument();
  });

  it("creates a download with a presentation snapshot without requesting remote media", async () => {
    window.history.replaceState({}, "", "/posts");
    const createdTask = {
      id: "task-created",
      kind: "download",
      status: "queued",
      position: 1,
      revision: 0,
      spec: {
        kind: "download",
        service: "fanbox",
        creator_id: "42",
        post_id: "99",
        revision_id: null,
        output: "downloads",
        dump_post_data: true,
      },
      presentation: {
        target_key: "download/fanbox/42/99/",
        title: "Fictional fixture",
        creator_name: "Demo Studio",
      },
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
      error: null,
      blocked_by: null,
      created_at: "2026-07-21T00:00:00Z",
      updated_at: "2026-07-21T00:00:00Z",
    };
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = String(input);
      if (path.endsWith("/session")) return json(session);
      if (path.endsWith("/tasks") && init?.method === "POST") return json(createdTask, 201);
      if (path.endsWith("/tasks")) return json([createdTask]);
      if (path.endsWith("/creators")) return json([]);
      if (path.includes("/tasks/task-created/events")) return json([]);
      if (path.endsWith("/tasks/task-created/attempts")) return json([]);
      if (path.includes("/pawchive/posts/fanbox/42/99/revisions")) return json([]);
      if (path.includes("/pawchive/posts/fanbox/42/99")) {
        return json({ id: "99", user: "42", service: "fanbox", title: "Fictional fixture", content: "Safe fixture body" });
      }
      if (path.includes("/pawchive/posts?")) {
        return json([{ id: "99", user: "42", service: "fanbox", title: "Fictional fixture", published: "2026-07-21T00:00:00Z" }]);
      }
      throw new Error(`Unexpected request: ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<BrowserRouter><App /></BrowserRouter>);
    await screen.findByRole("heading", { name: "Posts" });
    await user.type(screen.getByRole("textbox", { name: "Creator ID" }), "42");
    await user.type(screen.getByRole("textbox", { name: "Creator name" }), "Demo Studio");
    await user.click(screen.getByRole("button", { name: "Search posts" }));
    expect((await screen.findAllByText("Fictional fixture")).length).toBeGreaterThan(0);
    await user.click(screen.getAllByRole("button", { name: "Post details" })[0]);

    expect(await screen.findByText("Remote media stays unloaded")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Create download task" }));
    expect(await screen.findByRole("heading", { name: "Task details" })).toBeInTheDocument();
    const createCall = fetchMock.mock.calls.find(([input, init]) => String(input).endsWith("/tasks") && init?.method === "POST");
    expect(createCall).toBeDefined();
    expect(JSON.parse(String(createCall?.[1]?.body))).toEqual({
      spec: {
        kind: "download",
        service: "fanbox",
        creator_id: "42",
        post_id: "99",
        revision_id: null,
        output: "downloads",
        dump_post_data: true,
      },
      presentation: {
        target_key: "download/fanbox/42/99/",
        title: "Fictional fixture",
        creator_name: "Demo Studio",
      },
    });
    expect(fetchMock.mock.calls.every(([input]) => !/\.(jpg|png|gif|mp4)(\?|$)/i.test(String(input)))).toBe(true);
  });
});
