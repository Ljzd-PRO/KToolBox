import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { TaskRecord, TaskSpec } from "../types";
import { TaskEditor } from "./TaskEditor";

const noopSave: (spec: TaskSpec) => Promise<void> = async () => undefined;

function renderEditor({ task, onSave = vi.fn(noopSave) }: { task?: TaskRecord; onSave?: (spec: TaskSpec) => Promise<void> } = {}) {
  render(
    <TaskEditor
      creators={[]}
      saving={false}
      task={task}
      onClose={() => undefined}
      onSave={onSave}
    />,
  );
  return onSave;
}

describe("TaskEditor", () => {
  it("uses two fixed task tabs and submits Chip filters with unlimited dates", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn(noopSave);
    renderEditor({ onSave });

    expect(screen.getByRole("tab", { name: "Sync creators" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Download post" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Scroll tabs/ })).not.toBeInTheDocument();
    expect(screen.getByText(/Synchronize every post from the selected creators/)).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "No start date" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "No end date" })).toBeChecked();

    await user.type(screen.getByRole("textbox", { name: "Required title keywords" }), "painting,");
    await user.type(screen.getByRole("textbox", { name: "Legacy excluded keywords" }), "daily，");
    await user.click(screen.getByRole("button", { name: "Create task" }));

    expect(onSave).toHaveBeenCalledWith(expect.objectContaining({
      kind: "sync",
      start_time: null,
      end_time: null,
      keywords: ["painting"],
      keywords_exclude: ["daily"],
      output: "downloads",
    }));
  });

  it("requires a date after its unlimited option is cleared", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn(noopSave);
    renderEditor({ onSave });

    const noStartDate = screen.getByRole("checkbox", { name: "No start date" });
    await user.click(noStartDate);
    expect(noStartDate).not.toBeChecked();
    const form = document.querySelector("#task-editor-form") as HTMLFormElement;
    expect(form.checkValidity()).toBe(true);
    fireEvent.submit(form);

    expect(onSave).not.toHaveBeenCalled();
    expect(await screen.findByText("Choose a start date or select No start date.")).toBeInTheDocument();
  });

  it("submits the composed Pawchive path without changing the REST task shape", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn(noopSave);
    renderEditor({ onSave });

    await user.click(screen.getByRole("tab", { name: "Download post" }));
    expect(screen.getByText(/Download one specified post/)).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Platform" })).toHaveValue("fanbox");
    await user.type(screen.getByRole("textbox", { name: "Creator ID" }), "42");
    await user.type(screen.getByRole("textbox", { name: "Post ID" }), "99");
    await user.type(screen.getByRole("textbox", { name: "Revision ID" }), "3");
    await user.click(screen.getByRole("button", { name: "Create task" }));

    expect(onSave).toHaveBeenCalledWith({
      kind: "download",
      post: null,
      service: "fanbox",
      creator_id: "42",
      post_id: "99",
      revision_id: "3",
      output: "downloads",
      dump_post_data: true,
    });
  });

  it("preserves a single existing date boundary while editing", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn(noopSave);
    const task: TaskRecord = {
      id: "task-1",
      kind: "sync",
      status: "queued",
      spec: {
        kind: "sync",
        creators: [],
        output: "downloads",
        save_creator_indices: false,
        mix_posts: null,
        start_time: "2026-07-10T00:00:00",
        end_time: null,
        offset: 0,
        length: null,
        keywords: [],
        keywords_exclude: [],
      },
      presentation: null,
      position: 1,
      revision: 0,
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
      created_at: "2026-07-22T00:00:00Z",
      updated_at: "2026-07-22T00:00:00Z",
    };
    renderEditor({ task, onSave });

    expect(screen.getByRole("checkbox", { name: "No start date" })).not.toBeChecked();
    expect(screen.getByRole("checkbox", { name: "No end date" })).toBeChecked();
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(onSave).toHaveBeenCalledWith(expect.objectContaining({
      start_time: "2026-07-10T00:00:00",
      end_time: null,
    }));
  });
});
