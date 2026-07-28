import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../App";
import i18n from "../lib/i18n";
import { queryClient } from "../lib/query";

const session = {
  authenticated: true,
  username: "owner",
  csrf_token: "csrf-token",
  created_at: "2026-07-26T00:00:00Z",
};

const naming = {
  creator_dirname_format: "{creator_name} [{service}-{creator_id}]",
  post_dirname_format: "{title} [{post_id}]",
  revision_dirname_format: "revision-{revision_id}",
  post_structure: {
    attachments: "attachments",
    content: "content.txt",
    external_links: "external_links.txt",
    file: "{id}_{}",
    revisions: "revisions",
  },
  mix_posts: false,
  sequential_filename: false,
  sequential_filename_excludes: [],
  filename_format: "{}",
  group_by_year: false,
  group_by_month: false,
  year_dirname_format: "{year}",
  month_dirname_format: "{month:02d}",
};

const preview = {
  id: "preview-1",
  revision: "revision-1",
  fingerprint: "fingerprint-1",
  roots: ["/project/downloads"],
  creators: [
    {
      key: "fanbox:123",
      name: "Sample Creator",
      source: "/project/downloads/Sample Creator [fanbox-123]",
      target: "/project/downloads/Sample Creator (123)",
      works: 2,
      files: 5,
      bytes: 4096,
      operations: 1,
      skipped: 0,
      conflicts: [],
      selectable: true,
    },
    {
      key: "fanbox:456",
      name: "Conflicted Creator",
      source: "/project/downloads/Conflicted Creator [fanbox-456]",
      target: "/project/downloads/Existing",
      works: 1,
      files: 2,
      bytes: 1024,
      operations: 0,
      skipped: 0,
      conflicts: ["target already exists"],
      selectable: false,
    },
  ],
  creator_count: 2,
  work_count: 3,
  file_count: 7,
  total_bytes: 5120,
  skipped_count: 0,
  conflict_count: 0,
  created_at: "2026-07-26T00:00:00Z",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(async () => {
  cleanup();
  queryClient.clear();
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/");
  localStorage.clear();
  await i18n.changeLanguage("en");
});

describe("Naming format page", () => {
  it("scans real roots and defaults to converting every safe creator", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/naming");
    let applyBody: Record<string, unknown> | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/startup-notices")) return json([]);
        if (path.endsWith("/naming/conversions")) return json([]);
        if (path.endsWith("/naming/legacy-context")) {
          return json({
            roots: ["downloads"],
            conversion_pending: true,
          });
        }
        if (path.endsWith("/naming/preview")) return json(preview);
        if (path.endsWith("/naming/apply")) {
          applyBody = JSON.parse(String(init?.body)) as Record<string, unknown>;
          return json({
            id: preview.id,
            status: "completed",
            preview,
            selected_creators: [],
            progress: { completed_operations: 0, total_operations: 0, current_creator: null },
            error: null,
            created_at: preview.created_at,
            updated_at: preview.created_at,
          });
        }
        if (path.endsWith("/naming")) {
          return json({
            naming,
            revision: "revision-1",
            conversion_pending: true,
          });
        }
        throw new Error(`Unexpected request: ${path}`);
      }),
    );

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Naming format" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Naming format/ })).toHaveAttribute("href", "/naming");
    expect(await screen.findByText("Attachments directory")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: /Legacy download conversion/ }));
    const rootInput = screen.getByRole("textbox", { name: "Old location 1" });
    await user.clear(rootInput);
    expect(screen.getByText("Choose or enter an old download location.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Scan old locations" })).toBeDisabled();
    await user.type(screen.getByRole("textbox", { name: "Old location 1" }), "downloads");
    expect(screen.getByRole("textbox", { name: "Old location 1" })).toHaveValue("downloads");
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Scan old locations" })).toBeEnabled(),
    );

    await user.click(screen.getByRole("button", { name: "Scan old locations" }));
    expect(await screen.findByRole("heading", { name: "Review naming changes" })).toBeInTheDocument();
    for (const checkbox of screen.getAllByRole("checkbox", { name: "Select Sample Creator" })) {
      expect(checkbox).toBeChecked();
    }
    for (const checkbox of screen.getAllByRole("checkbox", { name: "Select Conflicted Creator" })) {
      expect(checkbox).toBeDisabled();
    }

    await user.click(screen.getByRole("button", { name: "Apply and convert" }));

    await waitFor(() =>
      expect(applyBody).toEqual({
        preview_id: preview.id,
        selected_creators: ["fanbox:123"],
      }),
    );
  });

  it("saves directory structure and naming templates independently", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/naming");
    const updates: Array<Record<string, unknown>> = [];
    let currentNaming = structuredClone(naming);
    let revision = "revision-1";
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/startup-notices")) return json([]);
        if (path.endsWith("/naming/conversions")) return json([]);
        if (path.endsWith("/naming/legacy-context")) {
          return json({ roots: [], conversion_pending: false });
        }
        if (path.endsWith("/naming") && init?.method === "PATCH") {
          const body = JSON.parse(String(init.body)) as {
            section: "structure" | "templates";
            naming: typeof naming;
          };
          updates.push(body as unknown as Record<string, unknown>);
          currentNaming = body.naming;
          revision = `revision-${updates.length + 1}`;
          return json({
            naming: currentNaming,
            revision,
            conversion_pending: true,
          });
        }
        if (path.endsWith("/naming")) {
          return json({
            naming: currentNaming,
            revision,
            conversion_pending: false,
          });
        }
        throw new Error(`Unexpected request: ${path}`);
      }),
    );

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>,
    );

    expect(await screen.findByText("Attachments directory")).toBeInTheDocument();
    await user.click(screen.getByRole("switch", { name: /Group by year/ }));
    await user.click(screen.getByRole("button", { name: "Save directory structure" }));
    await waitFor(() => expect(updates).toHaveLength(1));
    expect(updates[0]).toMatchObject({ section: "structure", revision: "revision-1" });

    await user.click(screen.getByRole("tab", { name: /Naming templates/ }));
    const creatorTemplate = screen.getByRole("textbox", {
      name: "Creator directory template",
    });
    await user.clear(creatorTemplate);
    await user.type(creatorTemplate, "{creator_name} ({creator_id})");
    await user.click(screen.getByRole("button", { name: "Save naming templates" }));
    await waitFor(() => expect(updates).toHaveLength(2));
    expect(updates[1]).toMatchObject({ section: "templates", revision: "revision-2" });
  });

  it("requires an explicit first-start decision and persists ignore", async () => {
    const user = userEvent.setup();
    let resolved = false;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/startup-notices/decision-1/resolve")) {
          expect(new Headers(init?.headers).get("X-CSRF-Token")).toBe("csrf-token");
          expect(JSON.parse(String(init?.body))).toEqual({ action: "ignored" });
          resolved = true;
          return json({
            id: "decision-1",
            kind: "legacy_layout_conversion",
            payload: {},
            created_at: "2026-07-26T00:00:00Z",
            acknowledged_at: null,
            resolution: "ignored",
            resolved_at: "2026-07-26T00:01:00Z",
          });
        }
        if (path.endsWith("/startup-notices")) {
          return json(
            resolved
              ? []
              : [
                  {
                    id: "decision-1",
                    kind: "legacy_layout_conversion",
                    payload: {},
                    created_at: "2026-07-26T00:00:00Z",
                    acknowledged_at: null,
                    resolution: null,
                    resolved_at: null,
                  },
                ],
          );
        }
        if (path.endsWith("/tasks")) return json([]);
        throw new Error(`Unexpected request: ${path}`);
      }),
    );

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Review existing downloads" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ignore" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Review conversion" })).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(screen.getByRole("heading", { name: "Review existing downloads" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Ignore" }));
    await waitFor(() =>
      expect(screen.queryByRole("heading", { name: "Review existing downloads" })).not.toBeInTheDocument(),
    );
    expect(resolved).toBe(true);
  });
});
