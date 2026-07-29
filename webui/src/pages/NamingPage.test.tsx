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
      target: "/project/downloads/Sample Creator [fanbox-123]",
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

const noLegacyMigration = {
  pending: false,
  project_revision: "revision-1",
  sources: [],
  fields: [],
  ignored_environment_keys: [],
};

const layoutVersions = [
  {
    id: "naming-layout-source",
    revision: "naming-revision-source",
    naming,
    origin: "project_change",
    created_at: "2026-07-25T00:00:00Z",
    is_current: false,
  },
  {
    id: "naming-layout-older",
    revision: "naming-revision-older",
    naming: {
      ...naming,
      post_dirname_format: "{post_id}",
    },
    origin: "recovered",
    created_at: "2026-07-24T00:00:00Z",
    is_current: false,
  },
  {
    id: "naming-layout-current",
    revision: "naming-revision-current",
    naming,
    origin: "project_current",
    created_at: "2026-07-26T00:00:00Z",
    is_current: true,
  },
];

const legacyMigration = {
  pending: true,
  project_revision: "revision-1",
  sources: [
    {
      name: ".env",
      path: "/project/.env",
      revision: "dotenv-revision-1",
      keys: ["KTOOLBOX_JOB__POST_DIRNAME_FORMAT"],
    },
  ],
  fields: [
    {
      path: "post_dirname_format",
      env_key: "KTOOLBOX_JOB__POST_DIRNAME_FORMAT",
      legacy_value: "{title}",
      current_value: "{title} [{post_id}]",
      sources: [".env"],
    },
  ],
  ignored_environment_keys: [],
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

describe("Naming format page", { timeout: 10_000 }, () => {
  it("scans real roots and defaults to converting every safe creator", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/naming");
    let applyBody: Record<string, unknown> | undefined;
    let previewBody: Record<string, unknown> | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/naming/legacy-migration")) return json(noLegacyMigration);
        if (path.endsWith("/naming/layout-versions")) return json(layoutVersions);
        if (path.endsWith("/startup-notices")) return json([]);
        if (path.endsWith("/naming/conversions")) return json([]);
        if (path.endsWith("/naming/legacy-context")) {
          return json({
            roots: ["downloads"],
            conversion_pending: true,
          });
        }
        if (path.endsWith("/naming/preview")) {
          previewBody = JSON.parse(String(init?.body)) as Record<string, unknown>;
          return json(preview);
        }
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
            default_output: "downloads",
            resolved_default_output: "/project/downloads",
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
    const unselectedVersion = screen
      .getAllByRole("checkbox", { name: /Select naming version/ })
      .find((checkbox) => !checkbox.hasAttribute("disabled") && !checkbox.hasAttribute("checked"));
    expect(unselectedVersion).toBeDefined();
    await user.click(unselectedVersion!);
    expect(screen.queryByRole("heading", { name: "Conversion history" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: /Conversion history/ }));
    expect(screen.getByRole("heading", { name: "Conversion history" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Conversion history/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
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
    expect(previewBody).toEqual({
      roots: ["downloads"],
      source: {
        kind: "project_layout",
        version_ids: ["naming-layout-source", "naming-layout-older"],
      },
    });
    expect(
      screen.getAllByText("Creator directory unchanged · 1 internal moves"),
    ).not.toHaveLength(0);
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

  it("keeps pasted drafts separate and previews a normalized pasted source", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/naming?tab=legacy");
    let parseBody: Record<string, unknown> | undefined;
    let previewBody: Record<string, unknown> | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/naming/legacy-migration")) return json(noLegacyMigration);
        if (path.endsWith("/naming/layout-versions")) return json(layoutVersions);
        if (path.endsWith("/startup-notices")) return json([]);
        if (path.endsWith("/naming/conversions")) return json([]);
        if (path.endsWith("/naming/legacy-context")) {
          return json({ roots: ["downloads"], conversion_pending: false });
        }
        if (path.endsWith("/naming/source/parse")) {
          parseBody = JSON.parse(String(init?.body)) as Record<string, unknown>;
          return json({
            format: "env",
            naming,
            digest: "a".repeat(64),
            recognized_fields: ["post_dirname_format"],
            defaulted_fields: ["creator_dirname_format"],
            warnings: [{ code: "ignored_unknown_entries", count: 1 }],
            differences: [
              {
                path: "post_dirname_format",
                source_value: "{title}",
                target_value: "{title} [{post_id}]",
              },
            ],
          });
        }
        if (path.endsWith("/naming/preview")) {
          previewBody = JSON.parse(String(init?.body)) as Record<string, unknown>;
          return json({
            ...preview,
            source: {
              kind: "pasted_config",
              format: "env",
              naming,
              digest: "a".repeat(64),
            },
          });
        }
        if (path.endsWith("/naming")) {
          return json({
            default_output: "downloads",
            resolved_default_output: "/project/downloads",
            naming,
            revision: "revision-1",
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

    await user.click(await screen.findByRole("tab", { name: "Paste configuration" }));
    const editor = screen.getByRole("textbox", {
      name: "Legacy .env naming settings",
    });
    const content = "KTOOLBOX_JOB__MIX_POSTS=true";
    await user.click(editor);
    await user.paste(content);
    await user.click(screen.getByRole("button", { name: "Parse configuration" }));
    await waitFor(() =>
      expect(parseBody).toEqual({ format: "env", content }),
    );
    expect(await screen.findByText("Legacy format parsed")).toBeInTheDocument();
    expect(screen.getByText("1 naming fields were recognized.")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Project history" }));
    await user.click(screen.getByRole("tab", { name: "Paste configuration" }));
    expect(
      screen.getByRole("textbox", { name: "Legacy .env naming settings" }),
    ).toHaveTextContent(content);
    await user.click(screen.getByRole("button", { name: "Scan old locations" }));
    expect(await screen.findByRole("heading", { name: "Review naming changes" })).toBeInTheDocument();
    expect(previewBody).toMatchObject({
      roots: ["downloads"],
      source: {
        kind: "pasted_config",
        format: "env",
        digest: "a".repeat(64),
      },
    });
    expect((previewBody?.source as { content?: string }).content).toBeUndefined();
  });

  it("saves directory structure and naming templates independently", async () => {
    const user = userEvent.setup();
    window.history.replaceState({}, "", "/naming");
    const updates: Array<Record<string, unknown>> = [];
    const ignoredLayouts = new Set<string>();
    let previewRequests = 0;
    let currentNaming = structuredClone(naming);
    let currentDefaultOutput = "downloads";
    let revision = "revision-1";
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/naming/legacy-migration")) return json(noLegacyMigration);
        if (path.endsWith("/naming/layout-versions")) return json(layoutVersions);
        const resolveMatch = path.match(/\/startup-notices\/(layout-\d+)\/resolve$/u);
        if (resolveMatch) {
          const id = resolveMatch[1];
          expect(JSON.parse(String(init?.body))).toEqual({ action: "ignored" });
          ignoredLayouts.add(id);
          return json({
            id,
            kind: "legacy_layout_conversion",
            payload: {},
            created_at: "2026-07-26T00:00:00Z",
            acknowledged_at: "2026-07-26T00:01:00Z",
            resolution: "ignored",
            resolved_at: "2026-07-26T00:01:00Z",
          });
        }
        if (path.endsWith("/startup-notices")) {
          const id = `layout-${updates.length}`;
          return json(
            updates.length && !ignoredLayouts.has(id)
              ? [{
                  id,
                  kind: "legacy_layout_conversion",
                  payload: {},
                  created_at: "2026-07-26T00:00:00Z",
                  acknowledged_at: null,
                  resolution: null,
                  resolved_at: null,
                }]
              : [],
          );
        }
        if (path.endsWith("/naming/conversions")) return json([]);
        if (path.endsWith("/naming/preview")) {
          previewRequests += 1;
          return json(preview);
        }
        if (path.endsWith("/naming/legacy-context")) {
          return json({ roots: [], conversion_pending: false });
        }
        if (path.endsWith("/naming") && init?.method === "PATCH") {
          const body = JSON.parse(String(init.body)) as {
            section: "structure" | "templates";
            naming: typeof naming;
            default_output?: string;
          };
          updates.push(body as unknown as Record<string, unknown>);
          currentNaming = body.naming;
          if (body.default_output) currentDefaultOutput = body.default_output;
          revision = `revision-${updates.length + 1}`;
          return json({
            default_output: currentDefaultOutput,
            resolved_default_output: `/project/${currentDefaultOutput}`,
            naming: currentNaming,
            revision,
            conversion_pending: true,
          });
        }
        if (path.endsWith("/naming")) {
          return json({
            default_output: currentDefaultOutput,
            resolved_default_output: `/project/${currentDefaultOutput}`,
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
    const defaultOutput = screen.getByRole("textbox", { name: "Default download location" });
    await user.clear(defaultOutput);
    await user.type(defaultOutput, "archive");
    await user.click(screen.getByRole("switch", { name: /Group by year/ }));
    await user.click(screen.getByRole("button", { name: "Save directory structure" }));
    await waitFor(() => expect(updates).toHaveLength(1));
    expect(updates[0]).toMatchObject({
      section: "structure",
      revision: "revision-1",
      default_output: "archive",
    });
    expect(await screen.findByRole("heading", { name: "Review existing downloads" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Review conversion" }));
    expect(screen.getByRole("tab", { name: /Legacy download conversion/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(previewRequests).toBe(0);

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

  it("dismisses legacy migration only for the current view and migrates after review", async () => {
    const user = userEvent.setup();
    let migrated = false;
    let applyBody: Record<string, unknown> | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path.endsWith("/session")) return json(session);
        if (path.endsWith("/naming/legacy-migration/apply")) {
          expect(new Headers(init?.headers).get("X-CSRF-Token")).toBe("csrf-token");
          applyBody = JSON.parse(String(init?.body)) as Record<string, unknown>;
          migrated = true;
          return json({
            migrated: true,
            backup_paths: ["/project/.ktoolbox/migrations/project-naming-v2/.env"],
            naming,
            project_revision: "revision-2",
            ignored_environment_keys: [],
          });
        }
        if (path.endsWith("/naming/legacy-migration")) {
          return json(migrated ? noLegacyMigration : legacyMigration);
        }
        if (path.endsWith("/naming/layout-versions")) return json(layoutVersions);
        if (path.endsWith("/startup-notices")) return json([]);
        if (path.endsWith("/naming/legacy-context")) {
          return json({ roots: ["/project/downloads"], conversion_pending: true });
        }
        if (path.endsWith("/naming")) {
          return json({
            default_output: "downloads",
            resolved_default_output: "/project/downloads",
            naming,
            revision: migrated ? "revision-2" : "revision-1",
            conversion_pending: true,
          });
        }
        if (path.endsWith("/tasks")) return json([]);
        throw new Error(`Unexpected request: ${path}`);
      }),
    );

    const first = render(
      <BrowserRouter>
        <App />
      </BrowserRouter>,
    );

    expect(await screen.findByRole("heading", { name: "Migrate legacy naming settings" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Ignore" }));
    await waitFor(() =>
      expect(screen.queryByRole("heading", { name: "Migrate legacy naming settings" })).not.toBeInTheDocument(),
    );
    expect(migrated).toBe(false);

    first.unmount();
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>,
    );
    expect(await screen.findByRole("heading", { name: "Migrate legacy naming settings" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Review changes" }));
    expect(await screen.findByRole("heading", { name: "Review configuration changes" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Migrate configuration" }));
    await waitFor(() =>
      expect(applyBody).toEqual({
        selected_fields: ["post_dirname_format"],
        project_revision: "revision-1",
        source_revisions: { ".env": "dotenv-revision-1" },
      }),
    );
    expect(await screen.findByText("Configuration migration is complete. You can now scan one or more old download locations, or do this later from Naming format.")).toBeInTheDocument();
  });
});
