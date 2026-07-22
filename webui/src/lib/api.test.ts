import { afterEach, describe, expect, it, vi } from "vitest";

import { api, ApiError, detailText, errorText } from "./api";
import i18n, { setLanguage } from "./i18n";

afterEach(async () => {
  vi.unstubAllGlobals();
  await i18n.changeLanguage("en");
});

describe("API error messages", () => {
  it("extracts readable text from supported legacy response shapes", () => {
    expect(detailText(" Plain failure ")).toBe("Plain failure");
    expect(detailText({ detail: { reason: "Nested failure" } })).toBe("Nested failure");
    expect(detailText({ errors: ["First", "First", { error: "Second" }] })).toBe("First; Second");
    expect(
      detailText([
        { loc: ["body", "creator_id"], msg: "Field required" },
        { loc: ["query", "offset"], msg: "Must be a multiple of 50" },
      ]),
    ).toBe("creator id: Field required; offset: Must be a multiple of 50");
  });

  it("uses a readable fallback instead of serializing unknown objects", () => {
    expect(detailText({ code: "unknown_shape", payload: { private: true } })).toBe("Request failed");
    expect(errorText({ message: "Object failure" })).toBe("Object failure");
    expect(errorText(null)).toBe("The request could not be completed.");
  });

  it("prefers the backend message while preserving structured detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: { code: "duplicate", existing_task_id: "task-1" },
            code: "task_duplicate",
            params: { existing_task_id: "task-1" },
            message: "An identical active task already exists",
          }),
          { status: 409, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    const error = await api("/tasks", { method: "POST", body: {} }).catch((reason: unknown) => reason);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 409,
      detail: { code: "duplicate", existing_task_id: "task-1" },
      code: "task_duplicate",
      params: { existing_task_id: "task-1" },
      message: "An identical active task already exists",
    });
  });

  it("localizes stable backend codes in the active language", async () => {
    await setLanguage("zh-CN");
    const error = new ApiError(
      409,
      { message: "An identical active task already exists" },
      "task_duplicate",
      {},
      "An identical active task already exists",
    );
    expect(errorText(error)).toBe("相同的活动任务已存在。");
    expect(errorText(new TypeError("Failed to fetch"))).toBe("KToolBox 无法连接服务器，请检查网络后重试。");
  });

  it("parses FastAPI validation arrays from legacy servers", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: [
              { loc: ["body", "username"], msg: "Field required", input: {} },
              { loc: ["body", "password"], msg: "Field required", input: {} },
            ],
          }),
          { status: 422, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    await expect(api("/session/login", { method: "POST", body: {} })).rejects.toThrow(
      "username: Field required; password: Field required",
    );
  });

  it("falls back to HTTP status text for non-JSON proxy errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("gateway unavailable", { status: 502, statusText: "Bad Gateway" })),
    );

    await expect(api("/health")).rejects.toThrow("Bad Gateway");
  });
});
