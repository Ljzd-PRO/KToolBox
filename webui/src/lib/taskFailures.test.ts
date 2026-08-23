import { describe, expect, it } from "vitest";

import i18n from "./i18n";
import {
  compactActivityEvents,
  eventMessage,
  failureAdvice,
  failureMessage,
  failureSummary,
  failureSubject,
  parseFailureItem,
  parseFailureReport,
} from "./taskFailures";
import type { FailureItem, TaskEvent } from "../types";

const incompatible: FailureItem = {
  code: "response_incompatible",
  stage: "work_list",
  message: "Response validation failed.",
  retryable: false,
  platform: "fanbox",
  creator_id: "demo-studio",
  file_name: null,
  http_status: null,
  operation: "list_creator_posts",
  fields: ["items.8.tags"],
};

describe("task failure presentation", () => {
  it("uses localized safe messages, subjects, and advice", async () => {
    await i18n.changeLanguage("zh-CN");
    expect(failureMessage(i18n.t, incompatible)).toContain("数据格式");
    expect(failureSubject(incompatible)).toBe("fanbox:demo-studio");
    expect(failureAdvice(i18n.t, incompatible)).toContain("更新");
    const missingFile: FailureItem = {
      ...incompatible,
      code: "resource_not_found",
      stage: "file_request",
      message: "The requested file was not found on the file server",
      platform: null,
      creator_id: null,
      file_name: "missing.bin",
      http_status: 404,
      operation: null,
      fields: [],
    };
    expect(failureMessage(i18n.t, missingFile)).toContain("文件服务器");
    expect(failureAdvice(i18n.t, missingFile)).toContain("稍后重试或跳过");
    expect(failureSummary(i18n.t, {
      summary: "Backend-only English summary",
      creator_failures: 1,
      file_failures: 2,
      items: [incompatible],
    })).toBe("作者失败 1 个，文件失败 2 个。");
  });

  it("preserves only a valid bounded failure shape from events", () => {
    expect(parseFailureItem({ ...incompatible, unsafe: "ignored" })).toEqual(incompatible);
    expect(parseFailureItem({ code: "not-real", stage: "work_list" })).toBeNull();
    expect(parseFailureReport({
      summary: "Safe summary",
      creator_failures: 1,
      file_failures: 0,
      items: [{ ...incompatible, unsafe: "ignored" }],
    })?.items).toEqual([incompatible]);
  });

  it("renders creator and download failures in activity messages", async () => {
    await i18n.changeLanguage("en");
    const event: TaskEvent = {
      id: 1,
      task_id: "fixture",
      event_type: "creator.finished",
      data: { failure: incompatible },
      created_at: "2026-07-23T00:00:00Z",
    };
    expect(eventMessage(i18n.t, event)).toContain("fanbox:demo-studio");
    expect(eventMessage(i18n.t, event)).toContain("format");
    expect(eventMessage(i18n.t, {
      ...event,
      event_type: "task.log",
      data: {
        message: "Backend-only English summary",
        failure_report: {
          summary: "Backend-only English summary",
          creator_failures: 1,
          file_failures: 0,
          items: [incompatible],
        },
      },
    })).toBe("Creator failures: 1; file failures: 0.");
  });

  it("renders structured creator and transfer details", async () => {
    await i18n.changeLanguage("en");
    const base: TaskEvent = {
      id: 2,
      task_id: "fixture",
      event_type: "creator.finished",
      data: {
        creator: "fanbox:demo",
        queued_files: 4,
        completed_files: 2,
        existing_files: 1,
        failed_files: 1,
      },
      created_at: "2026-07-23T00:00:00Z",
    };
    expect(eventMessage(i18n.t, base)).toContain("queued 4");
    expect(eventMessage(i18n.t, {
      ...base,
      event_type: "download.finished",
      data: {
        filename: "sample.bin",
        creator: "fanbox:demo",
        outcome: "completed",
        completed_bytes: 1024,
        total_bytes: 2048,
        elapsed_seconds: 2,
        average_speed_bps: 512,
      },
    })).toContain("512 B/s");
  });

  it("keeps only the latest retry for each download in the activity view", () => {
    const retry = (id: number, key: string, retryCount: number): TaskEvent => ({
      id,
      task_id: "fixture",
      event_type: "download.retrying",
      data: { key, retry_count: retryCount, status_code: 503 },
      created_at: `2026-07-23T00:00:0${id}Z`,
    });
    const finished: TaskEvent = {
      id: 4,
      task_id: "fixture",
      event_type: "download.finished",
      data: { key: "one", outcome: "failed" },
      created_at: "2026-07-23T00:00:04Z",
    };
    const existed: TaskEvent = {
      id: 5,
      task_id: "fixture",
      event_type: "download.finished",
      data: { key: "existing", outcome: "existed" },
      created_at: "2026-07-23T00:00:05Z",
    };

    expect(compactActivityEvents([
      retry(1, "one", 0),
      retry(2, "two", 0),
      retry(3, "one", 1),
      finished,
      existed,
    ]).map((event) => event.id)).toEqual([2, 3, 4]);
  });
});
