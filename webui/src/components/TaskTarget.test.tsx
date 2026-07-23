import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import i18n from "../lib/i18n";
import type {
  CreatorRosterItem,
  SyncTaskSpec,
  TaskPresentationSnapshot,
  TaskRecord,
  TaskSpec,
} from "../types";
import { TaskTarget } from "./TaskTarget";

afterEach(async () => {
  await i18n.changeLanguage("en");
});

describe("TaskTarget", () => {
  it("uses the cached author name as the title for a single-author sync", () => {
    const spec = syncSpec([{ service: "fanbox", creator_id: "42", alias: "Local note", enabled: true }]);
    render(
      <TaskTarget
        creators={[rosterCreator("42", "Studio Sample")]}
        task={taskRecord(spec)}
      />,
    );

    expect(screen.getByTitle("Studio Sample")).toHaveTextContent("Studio Sample");
    expect(screen.queryByText("Local note", { exact: true })).not.toBeInTheDocument();
  });

  it("keeps the total author count visible while allowing a long first name to truncate", async () => {
    await i18n.changeLanguage("zh-CN");
    const creators = [
      { service: "fanbox", creator_id: "1", alias: null, enabled: true },
      { service: "fanbox", creator_id: "2", alias: null, enabled: true },
      { service: "fanbox", creator_id: "3", alias: null, enabled: true },
    ];
    render(
      <TaskTarget
        creators={[
          rosterCreator("1", "theordinarythatkeepsgoing"),
          rosterCreator("2", "第二位作者"),
          rosterCreator("3", "第三位作者"),
        ]}
        task={taskRecord(syncSpec(creators))}
      />,
    );

    const title = screen.getByTitle("theordinarythatkeepsgoing 等 3 位作者");
    expect(title.querySelector(".truncate")).toHaveTextContent("theordinarythatkeepsgoing");
    expect(title.querySelector(".shrink-0")).toHaveTextContent("等 3 位作者");
  });

  it("uses the saved work title and marks it as truncatable", () => {
    const presentation: TaskPresentationSnapshot = {
      target_key: "download/fanbox/42/99/",
      title: "A deliberately long work title",
      creator_name: "Studio Sample",
    };
    render(
      <TaskTarget
        task={taskRecord({
          kind: "download",
          post: null,
          service: "fanbox",
          creator_id: "42",
          post_id: "99",
          revision_id: null,
          output: "downloads",
          dump_post_data: true,
        }, presentation)}
      />,
    );

    expect(screen.getByTitle("A deliberately long work title")).toHaveClass("truncate");
  });
});

function syncSpec(creators: SyncTaskSpec["creators"]): SyncTaskSpec {
  return {
    kind: "sync",
    creators,
    output: "downloads",
    save_creator_indices: false,
    mix_posts: null,
    start_time: null,
    end_time: null,
    offset: 0,
    length: null,
    keywords: [],
    keywords_exclude: [],
  };
}

function rosterCreator(creatorId: string, name: string): CreatorRosterItem {
  return {
    service: "fanbox",
    creator_id: creatorId,
    alias: null,
    enabled: true,
    name,
  };
}

function taskRecord(
  spec: TaskSpec,
  presentation: TaskPresentationSnapshot | null = null,
): TaskRecord {
  return {
    id: "task-1",
    kind: spec.kind,
    status: "queued",
    spec,
    presentation,
    position: 1,
    revision: 1,
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
    failure: null,
    blocked_by: null,
    created_at: "2026-07-23T00:00:00Z",
    updated_at: "2026-07-23T00:00:00Z",
  };
}
