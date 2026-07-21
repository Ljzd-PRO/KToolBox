import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

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
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/");
  localStorage.clear();
});

describe("project workflows", () => {
  it("renders the creator roster with readable labels", async () => {
    window.history.replaceState({}, "", "/creators");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/creators")) {
          return json([{ service: "fanbox", creator_id: "42", alias: "Studio Sample", enabled: true }]);
        }
        throw new Error(`Unexpected request: ${path}`);
      }),
    );

    render(<BrowserRouter><App /></BrowserRouter>);

    expect(await screen.findByRole("heading", { name: "Creators" })).toBeInTheDocument();
    expect(screen.getAllByText("Studio Sample").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Add creator" })).toBeInTheDocument();
  });

  it("renders scoped blocker controls from project TOML", async () => {
    window.history.replaceState({}, "", "/blockers");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/creators")) {
          return json([{ service: "fanbox", creator_id: "42", alias: "Studio Sample", enabled: true }]);
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

    render(<BrowserRouter><App /></BrowserRouter>);

    expect(await screen.findByRole("heading", { name: "Blockers" })).toBeInTheDocument();
    expect(screen.getByText("daily-sharing")).toBeInTheDocument();
    expect(screen.getByText(/Selected creators: fanbox:42/)).toBeInTheDocument();
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

    render(<BrowserRouter><App /></BrowserRouter>);

    expect(await screen.findByRole("heading", { name: "Configuration" })).toBeInTheDocument();
    expect(screen.getByText("API request timeout")).toBeInTheDocument();
    expect(screen.getByText("Pawchive API request timeout")).toBeInTheDocument();
    expect(screen.queryByText("api.timeout")).not.toBeInTheDocument();
  });
});
