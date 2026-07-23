import { describe, expect, it } from "vitest";

import i18n from "./i18n";
import {
  eventMessage,
  failureAdvice,
  failureMessage,
  failureSubject,
  parseFailureItem,
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
  });

  it("preserves only a valid bounded failure shape from events", () => {
    expect(parseFailureItem({ ...incompatible, unsafe: "ignored" })).toEqual(incompatible);
    expect(parseFailureItem({ code: "not-real", stage: "work_list" })).toBeNull();
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
  });
});
