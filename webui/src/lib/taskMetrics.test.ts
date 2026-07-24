import { describe, expect, it } from "vitest";

import { taskDownloadSpeed, totalDownloadSpeed } from "./taskMetrics";
import type { TaskRecord } from "../types";

function task(status: TaskRecord["status"], speed: number): TaskRecord {
  return {
    id: `${status}-${speed}`,
    kind: "download",
    status,
    spec: {
      kind: "download",
      service: "fanbox",
      creator_id: "creator",
      post_id: "work",
      output: "downloads",
      dump_post_data: true,
    },
    presentation: null,
    position: 1,
    revision: 1,
    progress: {
      queued_files: 1,
      processed_files: 0,
      completed_files: 0,
      existing_files: 0,
      failed_files: 0,
      transferred_bytes: 0,
      total_bytes: 100,
      speed_bps: speed,
      eta_seconds: null,
      active_creators: [],
      active_downloads: {},
      waiting_retries: {},
    },
    error: null,
    failure: null,
    blocked_by: null,
    created_at: "2026-07-24T00:00:00Z",
    updated_at: "2026-07-24T00:00:00Z",
  };
}

describe("task download speed", () => {
  it("only includes finite positive speeds from active tasks", () => {
    const records = [
      task("running", 120),
      task("pause_requested", 30),
      task("completed", 900),
      task("running", Number.NaN),
      task("running", -10),
    ];

    expect(taskDownloadSpeed(records[0])).toBe(120);
    expect(taskDownloadSpeed(records[2])).toBe(0);
    expect(totalDownloadSpeed(records)).toBe(150);
  });
});
