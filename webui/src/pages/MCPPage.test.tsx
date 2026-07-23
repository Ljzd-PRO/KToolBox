import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../App";
import { queryClient } from "../lib/query";
import type { MCPToken } from "../types";

const session = {
  authenticated: true,
  username: "owner",
  csrf_token: "csrf-token",
  created_at: "2026-07-23T00:00:00Z",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function token(overrides: Partial<MCPToken & { token: string }> = {}): MCPToken & { token?: string } {
  return {
    id: "token-1",
    name: "Codex desktop",
    username: "owner",
    permission: "read" as const,
    scopes: ["mcp:read"],
    created_at: "2026-07-23T00:00:00Z",
    expires_at: "2026-08-22T00:00:00Z",
    last_used_at: null,
    revoked_at: null,
    active: true,
    ...overrides,
  };
}

afterEach(() => {
  queryClient.clear();
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/");
  localStorage.clear();
});

describe("MCP page", () => {
  it("shows service endpoints, token state, client configuration, and localized tools", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/mcp");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/mcp/status")) {
          return json({
            running: true,
            endpoint_path: "/mcp",
            openapi_path: "/api/v1/openapi.yaml",
            transport: "streamable-http",
            tool_count: 2,
          });
        }
        if (path.endsWith("/mcp/tokens")) return json([token()]);
        if (path.endsWith("/mcp/tools")) {
          return json([
            {
              name: "list_tasks",
              operation_id: "list_tasks",
              description: "Backend description",
              category: "tasks",
              scope: "mcp:read",
              safety: "read",
              open_world: false,
            },
            {
              name: "get_project_summary",
              operation_id: "project",
              description: "Project summary backend description",
              category: "project",
              scope: "mcp:read",
              safety: "read",
              open_world: false,
            },
          ]);
        }
        throw new Error(`Unexpected request: ${path}`);
      }),
    );

    render(<BrowserRouter><App /></BrowserRouter>);

    expect(await screen.findByRole("heading", { name: "MCP" })).toBeInTheDocument();
    expect((await screen.findAllByText("Codex desktop")).length).toBeGreaterThan(0);
    expect(screen.getAllByText(`${window.location.origin}/mcp`).length).toBeGreaterThan(0);
    expect(screen.getByText("List persistent tasks and their current states.")).not.toBeVisible();
    expect(screen.queryByText("Backend description")).not.toBeInTheDocument();
    await user.type(screen.getByRole("searchbox", { name: "Search tools" }), "list_tasks");
    expect(await screen.findByText("List persistent tasks and their current states.")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Codex" }));
    expect(screen.getByText(/bearer_token_env_var = "KTOOLBOX_MCP_TOKEN"/)).toBeInTheDocument();
  });

  it("shows a newly issued secret once and supports immediate revocation", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/mcp");
    let records: Array<MCPToken & { token?: string }> = [token({ expires_at: null })];
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = String(input);
      if (path.endsWith("/session")) return json(session);
      if (path.endsWith("/mcp/status")) {
        return json({
          running: true,
          endpoint_path: "/mcp",
          openapi_path: "/api/v1/openapi.yaml",
          transport: "streamable-http",
          tool_count: 0,
        });
      }
      if (path.endsWith("/mcp/tools")) return json([]);
      if (path.endsWith("/mcp/tokens") && init?.method === "POST") {
        const created = token({
          id: "token-2",
          name: "Automation",
          expires_at: null,
          token: "ktmcp_once_only",
        });
        records = [created, ...records];
        return json(created, 201);
      }
      if (path.endsWith("/mcp/tokens")) return json(records);
      if (path.endsWith("/mcp/tokens/token-1/revoke")) {
        records = records.map((record) => record.id === "token-1"
          ? { ...record, active: false, revoked_at: "2026-07-23T01:00:00Z" }
          : record);
        return json(records.find((record) => record.id === "token-1"));
      }
      throw new Error(`Unexpected request: ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<BrowserRouter><App /></BrowserRouter>);
    await user.click(await screen.findByRole("button", { name: "New access token" }));
    await user.type(screen.getByRole("textbox", { name: "Token name" }), "Automation");
    await user.type(screen.getByLabelText("Confirm account password"), "correct password");
    await user.click(screen.getByRole("button", { name: "Create access token" }));

    expect(await screen.findByText("ktmcp_once_only")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    await waitFor(() => expect(screen.queryByText("ktmcp_once_only")).not.toBeInTheDocument());

    const revokeButtons = screen.getAllByRole("button", { name: "Revoke" });
    await user.click(revokeButtons[revokeButtons.length - 1]);
    expect(screen.getByText("“Codex desktop” will stop working immediately. Existing WebUI sessions are not affected.")).toBeInTheDocument();
    await user.click(screen.getAllByRole("button", { name: "Revoke" }).at(-1)!);
    await waitFor(() => expect(screen.getAllByText("Revoked").length).toBeGreaterThan(0));
  });
});
