import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../App";
import { queryClient } from "../lib/query";

const session = {
  authenticated: true,
  username: "owner",
  csrf_token: "csrf-token",
  created_at: "2026-07-27T00:00:00Z",
};

const creator = {
  service: "fanbox",
  creator_id: "42",
  alias: null,
  enabled: true,
  name: "Studio Sample",
};

const plan = {
  id: "daily-studio",
  name: "Daily studio",
  enabled: true,
  creators: ["fanbox:42"],
  schedule: { kind: "cron", expression: "0 3 * * *", timezone: "Asia/Shanghai" },
  initial_start_date: "2026-07-01",
  options: {
    output: "downloads",
    save_creator_indices: true,
    mix_posts: null,
    keywords: [],
    keywords_exclude: [],
  },
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

describe("automatic synchronization page", () => {
  it("renders plans, recent creator counts, and task-linked run history", async () => {
    window.history.replaceState({}, "", "/auto-sync");
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const path = String(input);
      if (path.endsWith("/session")) return json(session);
      if (path.endsWith("/auto-sync/plans")) {
        return json({
          plans: [plan],
          revision: "revision-1",
          next_runs: { "daily-studio": "2026-07-28T03:00:00Z" },
        });
      }
      if (path.endsWith("/creators")) return json([creator]);
      if (path.includes("/auto-sync/runs")) {
        return json([{
          id: "run-1",
          plan_id: "daily-studio",
          plan_name: "Daily studio",
          trigger: "scheduled",
          status: "completed",
          task_id: "task-1",
          scheduled_for: "2026-07-27T03:00:00Z",
          cutoff_at: "2026-07-27T03:00:00Z",
          created_at: "2026-07-27T03:00:00Z",
          started_at: "2026-07-27T03:00:01Z",
          finished_at: "2026-07-27T03:01:00Z",
          error: null,
        }]);
      }
      if (path.includes("/auto-sync/updates")) {
        return json([{
          service: "fanbox",
          creator_id: "42",
          creator_name: "Studio Sample",
          new_posts: 3,
          last_discovered_at: "2026-07-27T03:00:30Z",
        }]);
      }
      throw new Error(`Unexpected request: ${path}`);
    }));

    const { container } = render(<BrowserRouter><App /></BrowserRouter>);

    expect(await screen.findByRole("heading", { name: "Automatic sync", level: 1 })).toBeInTheDocument();
    expect((await screen.findAllByText("Daily studio")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("Studio Sample")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("+3").length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: "View task" })[0]).toHaveAttribute("href", "/tasks/task-1");
    expect(container.querySelectorAll(".table-column-icon").length).toBeGreaterThan(8);
  });

  it("creates a plan with a stable generated ID and selected creators", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/auto-sync");
    let createdBody: Record<string, unknown> | null = null;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = String(input);
      if (path.endsWith("/session")) return json(session);
      if (path.endsWith("/creators")) return json([creator]);
      if (path.includes("/auto-sync/runs")) return json([]);
      if (path.includes("/auto-sync/updates")) return json([]);
      if (path.endsWith("/auto-sync/plans") && init?.method === "POST") {
        createdBody = JSON.parse(String(init.body)) as Record<string, unknown>;
        return json({ plans: [createdBody], revision: "revision-2", next_runs: {} }, 201);
      }
      if (path.endsWith("/auto-sync/plans")) {
        return json({ plans: [], revision: "revision-1", next_runs: {} });
      }
      throw new Error(`Unexpected request: ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<BrowserRouter><App /></BrowserRouter>);
    await user.click(await screen.findByRole("button", { name: "New plan" }));

    const dialog = await screen.findByRole("dialog");
    const nameInput = within(dialog).getByLabelText("Plan name");
    const idInput = within(dialog).getByLabelText("Plan ID");
    expect(idInput).toHaveAttribute("readonly");
    expect((idInput as HTMLInputElement).value).toMatch(/^auto-[a-f0-9-]+$/u);

    await user.type(nameInput, "Weekly references");
    await user.click(within(dialog).getByRole("checkbox", { name: "Studio Sample" }));
    await user.click(within(dialog).getByRole("button", { name: "Save" }));

    await vi.waitFor(() => expect(createdBody).not.toBeNull());
    expect(createdBody).toMatchObject({
      name: "Weekly references",
      creators: ["fanbox:42"],
      schedule: { kind: "cron", expression: "0 3 * * *" },
      options: { output: "downloads" },
    });
    const postCall = fetchMock.mock.calls.find(([, init]) => init?.method === "POST");
    expect(new Headers(postCall?.[1]?.headers).get("If-Match")).toBe("\"revision-1\"");
  });
});
