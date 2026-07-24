import { describe, expect, it } from "vitest";

import { parsePawchiveCreatorUrl } from "./pawchive";

describe("parsePawchiveCreatorUrl", () => {
  it.each([
    ["https://pawchive.pw/fanbox/user/123", { service: "fanbox", creatorId: "123" }],
    ["https://pawchive.pw/patreon/user/creator-name/post/456", { service: "patreon", creatorId: "creator-name" }],
    ["https://example.test/pixiv/user/%E4%BD%9C%E8%80%85", { service: "pixiv", creatorId: "作者" }],
  ])("parses %s", (value, expected) => {
    expect(parsePawchiveCreatorUrl(value)).toEqual(expected);
  });

  it.each([
    "",
    "fanbox:123",
    "ftp://pawchive.pw/fanbox/user/123",
    "https://pawchive.pw/posts",
    "https://pawchive.pw/fanbox/creator/123",
  ])("rejects %s", (value) => {
    expect(parsePawchiveCreatorUrl(value)).toBeNull();
  });
});
