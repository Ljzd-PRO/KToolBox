import { describe, expect, it } from "vitest";

import { formatBytes } from "./format";

describe("localized formatting", () => {
  it("uses locale-specific decimal separators for byte values", () => {
    expect(formatBytes(1536, "", "en-US")).toBe("1.50 KiB");
    expect(formatBytes(1536, "", "fr-FR")).toMatch(/^1,50[\s\u202f]KiB$/u);
  });
});
