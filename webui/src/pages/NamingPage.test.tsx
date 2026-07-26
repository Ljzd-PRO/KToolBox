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
  download_roots: ["downloads"],
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
            suggested_download_roots: ["downloads"],
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

    const rootInput = screen.getByRole("textbox", { name: "Download directory 1" });
    await user.clear(rootInput);
    expect(screen.getByText("Choose or enter a download directory.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Scan and review" })).toBeDisabled();
    await user.type(screen.getByRole("textbox", { name: "Download directory 1" }), "downloads");
    expect(screen.getByRole("textbox", { name: "Download directory 1" })).toHaveValue("downloads");
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Scan and review" })).toBeEnabled(),
    );

    await user.click(screen.getByRole("button", { name: "Scan and review" }));
    expect(await screen.findByRole("heading", { name: "Review naming changes" })).toBeInTheDocument();
    expect(screen.getByRole("switch", { name: "Convert downloaded creators" })).toBeChecked();
    for (const checkbox of screen.getAllByRole("checkbox", { name: "Select Sample Creator" })) {
      expect(checkbox).toBeChecked();
    }
    for (const checkbox of screen.getAllByRole("checkbox", { name: "Select Conflicted Creator" })) {
      expect(checkbox).toBeDisabled();
    }

    await user.click(screen.getByRole("switch", { name: "Convert downloaded creators" }));
    expect(screen.getByText("Existing downloads will stay where they are")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Save format only" }));

    await waitFor(() =>
      expect(applyBody).toEqual({
        preview_id: preview.id,
        selected_creators: ["fanbox:123"],
        convert_existing: false,
      }),
    );
  });

  it("shows the one-time migration summary and acknowledges it with CSRF", async () => {
    const user = userEvent.setup();
    let acknowledged = false;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/startup-notices/notice-1/acknowledge")) {
          expect(new Headers(init?.headers).get("X-CSRF-Token")).toBe("csrf-token");
          acknowledged = true;
          return json({
            id: "notice-1",
            kind: "naming_migrated",
            payload: {},
            created_at: "2026-07-26T00:00:00Z",
            acknowledged_at: "2026-07-26T00:01:00Z",
          });
        }
        if (path.endsWith("/startup-notices")) {
          return json(
            acknowledged
              ? []
              : [
                  {
                    id: "notice-1",
                    kind: "naming_migrated",
                    payload: {
                      backup_paths: ["/project/.env.naming-v1.bak"],
                      ignored_environment_keys: ["KTOOLBOX_JOB__CREATOR_FOLDER"],
                    },
                    created_at: "2026-07-26T00:00:00Z",
                    acknowledged_at: null,
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

    expect(await screen.findByRole("heading", { name: "Naming settings were moved" })).toBeInTheDocument();
    expect(screen.getByText("/project/.env.naming-v1.bak")).toBeInTheDocument();
    expect(screen.getByText("KTOOLBOX_JOB__CREATOR_FOLDER")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Got it" }));
    await waitFor(() =>
      expect(screen.queryByRole("heading", { name: "Naming settings were moved" })).not.toBeInTheDocument(),
    );
  });
});
