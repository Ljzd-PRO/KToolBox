import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../lib/auth";
import type { FilesystemBrowse, PathSelector } from "../types";
import { RemotePathField } from "./RemotePathField";

const directorySelector: PathSelector = { kind: "directory", scope: "project", value_mode: "absolute" };
const fileSelector: PathSelector = { kind: "file", scope: "project", value_mode: "project_relative" };

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function browserResponse({
  path = "/project",
  projectRelative = ".",
  parent = null,
  mode = "directory",
  suggestedName = null,
  entries = [],
}: {
  path?: string;
  projectRelative?: string;
  parent?: string | null;
  mode?: "directory" | "file";
  suggestedName?: string | null;
  entries?: FilesystemBrowse["entries"];
} = {}): FilesystemBrowse {
  return {
    scope: "project",
    mode,
    path,
    project_relative_path: projectRelative,
    parent,
    separator: "/",
    breadcrumbs: path === "/project"
      ? [{ label: "Project", path: "/project" }]
      : [{ label: "Project", path: "/project" }, { label: path.split("/").at(-1) ?? "", path }],
    locations: [{ id: "project", label: "Project", path: "/project" }],
    entries,
    suggested_name: suggestedName,
    offset: 0,
    limit: 100,
    has_more: false,
  };
}

function FieldHarness({ selector = directorySelector, initial = "downloads" }: { selector?: PathSelector; initial?: string }) {
  const [value, setValue] = useState(initial);
  return <RemotePathField label="Output" selector={selector} value={value} onChange={setValue} />;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("RemotePathField", () => {
  it("keeps manual input and only commits a browsed directory after confirmation", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input), "http://testserver");
      const requested = url.searchParams.get("path");
      if (requested === "/project/existing") {
        return json(browserResponse({
          path: "/project/existing",
          projectRelative: "existing",
          parent: "/project",
        }));
      }
      return json(browserResponse({
        suggestedName: "downloads",
        entries: [{
          name: "existing",
          path: "/project/existing",
          project_relative_path: "existing",
          kind: "directory",
          is_symlink: false,
          navigable: true,
        }],
      }));
    }));
    render(<FieldHarness />);

    const input = screen.getByRole("textbox", { name: "Output" });
    await user.clear(input);
    await user.type(input, "typed/by/hand");
    expect(input).toHaveValue("typed/by/hand");

    const browse = screen.getByRole("button", { name: "Browse the remote computer for Output" });
    await user.click(browse);
    const dialog = await screen.findByRole("dialog", { name: "Output" });
    await user.click(within(dialog).getByRole("option", { name: "existing" }));
    await waitFor(() => expect(within(dialog).getByText("existing")).toBeInTheDocument());
    await user.click(within(dialog).getByRole("button", { name: "Select directory" }));

    expect(input).toHaveValue("/project/existing");
    await waitFor(() => expect(browse).toHaveFocus());
  });

  it("does not mutate the field when the picker is cancelled", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn(async () => json(browserResponse())));
    render(<FieldHarness initial="keep/me" />);

    const browse = screen.getByRole("button", { name: "Browse the remote computer for Output" });
    await user.click(browse);
    const dialog = await screen.findByRole("dialog", { name: "Output" });
    await user.click(within(dialog).getByRole("button", { name: "Cancel" }));

    expect(screen.getByRole("textbox", { name: "Output" })).toHaveValue("keep/me");
    await waitFor(() => expect(browse).toHaveFocus());
  });

  it("accepts a new file name without creating a file", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      void input;
      void init;
      return json(browserResponse({ mode: "file", suggestedName: "content.txt" }));
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<FieldHarness initial="content.txt" selector={fileSelector} />);

    await user.click(screen.getByRole("button", { name: "Browse the remote computer for Output" }));
    const dialog = await screen.findByRole("dialog", { name: "Output" });
    const fileName = within(dialog).getByRole("textbox", { name: "File name" });
    await waitFor(() => expect(fileName).toHaveValue("content.txt"));
    await user.clear(fileName);
    await user.type(fileName, "new-content.txt");
    await user.click(within(dialog).getByRole("button", { name: "Select file" }));

    expect(screen.getByRole("textbox", { name: "Output" })).toHaveValue("new-content.txt");
    expect(fetchMock.mock.calls.every(([, init]) => init?.method !== "POST")).toBe(true);
  });

  it("creates one remote child directory with the session CSRF token and navigates into it", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = new URL(String(input), "http://testserver");
      if (url.pathname.endsWith("/session")) {
        return json({ authenticated: true, username: "owner", csrf_token: "csrf-token", created_at: "2026-07-22T00:00:00Z" });
      }
      if (url.pathname.endsWith("/filesystem/directories") && init?.method === "POST") {
        return json({
          name: "created",
          path: "/project/created",
          project_relative_path: "created",
          kind: "directory",
          is_symlink: false,
          navigable: true,
        }, 201);
      }
      if (url.searchParams.get("path") === "/project/created") {
        return json(browserResponse({ path: "/project/created", projectRelative: "created", parent: "/project" }));
      }
      return json(browserResponse());
    });
    vi.stubGlobal("fetch", fetchMock);
    const outerSubmit = vi.fn();
    render(
      <AuthProvider>
        <form onSubmit={outerSubmit}><FieldHarness initial="" /></form>
      </AuthProvider>,
    );
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());

    await user.click(screen.getByRole("button", { name: "Browse the remote computer for Output" }));
    const dialog = await screen.findByRole("dialog", { name: "Output" });
    await user.click(within(dialog).getByRole("button", { name: "New folder" }));
    await user.type(within(dialog).getByRole("textbox", { name: "Folder name" }), "created");
    await user.click(within(dialog).getByRole("button", { name: "Add" }));

    await waitFor(() => expect(within(dialog).getByText("created")).toBeInTheDocument());
    const createCall = fetchMock.mock.calls.find(([input, init]) => String(input).endsWith("/filesystem/directories") && init?.method === "POST");
    expect(createCall).toBeDefined();
    expect(new Headers(createCall?.[1]?.headers).get("X-CSRF-Token")).toBe("csrf-token");
    expect(JSON.parse(String(createCall?.[1]?.body))).toEqual({ scope: "project", parent: "/project", name: "created" });
    expect(outerSubmit).not.toHaveBeenCalled();
  });
});
