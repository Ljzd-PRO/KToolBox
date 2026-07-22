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

describe("project workflows", () => {
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
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/creators")) {
          return json([{ service: "fanbox", creator_id: "42", alias: null, enabled: true, name: "Studio Sample" }]);
        }
        throw new Error(`Unexpected request: ${path}`);
      }),
    );

    const { container } = render(<BrowserRouter><App /></BrowserRouter>);

    expect(await screen.findByRole("heading", { name: "Creators" })).toBeInTheDocument();
    expect((await screen.findAllByText("Studio Sample")).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("columnheader").map((header) => header.textContent)).toEqual([
      "Creator name",
      "Creator ID",
      "Platform",
      "Note",
      "Status",
      "Actions",
    ]);
    expect(screen.getByRole("button", { name: "Add creator" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Edit fanbox:42" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "Remove fanbox:42" }).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /Actions Studio Sample/ })).not.toBeInTheDocument();
    expect(container.querySelector(".list-switch-cell")).toContainElement(screen.getAllByRole("switch")[0]);

    await user.click(screen.getByRole("button", { name: "Add creator" }));
    expect(screen.getByRole("group", { name: "Pawchive creator path" })).toBeInTheDocument();
    expect(screen.getByText("/platform/user/creator ID", { selector: "code" })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Platform" })).not.toHaveAttribute("readonly");
    expect(screen.getByRole("textbox", { name: "Creator ID" })).not.toHaveAttribute("readonly");
    expect(screen.getByRole("textbox", { name: "Note" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Close" }));

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
            fields: [{
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
            }],
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
    expect(screen.queryByText("api.timeout")).not.toBeInTheDocument();
    const saveBar = container.querySelector(".config-save-bar");
    expect(saveBar).toBeInTheDocument();
    expect(saveBar?.closest(".form-surface")).toBeInTheDocument();
    expect(container.querySelector('[data-slot="scroll-shadow"]')).not.toBeInTheDocument();
  });
});
