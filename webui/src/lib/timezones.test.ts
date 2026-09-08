import { describe, expect, it } from "vitest";

import {
  formatUtcOffset,
  timeZoneOffsetMinutes,
  timeZonePresentation,
} from "./timezones";

describe("timezone presentation", () => {
  it("uses an explicit UTC label", () => {
    expect(timeZonePresentation("UTC", new Date("2026-01-15T12:00:00Z"))).toEqual({
      abbreviation: "UTC",
      offset: "UTC",
    });
  });

  it("uses an unambiguous offset when a short name is ambiguous", () => {
    const presentation = timeZonePresentation(
      "Asia/Shanghai",
      new Date("2026-01-15T12:00:00Z"),
    );
    expect(presentation.abbreviation).toBe("UTC+08");
    expect(presentation.offset).toBe("UTC+08:00");
  });

  it("reflects daylight-saving changes for stable abbreviations", () => {
    const winter = timeZonePresentation(
      "America/New_York",
      new Date("2026-01-15T12:00:00Z"),
    );
    const summer = timeZonePresentation(
      "America/New_York",
      new Date("2026-07-15T12:00:00Z"),
    );
    expect(winter.abbreviation).toBe("EST");
    expect(summer.abbreviation).toBe("EDT");
    expect(winter.offset).toBe("UTC-05:00");
    expect(summer.offset).toBe("UTC-04:00");
  });

  it("formats positive and negative offsets", () => {
    expect(formatUtcOffset(330)).toBe("UTC+05:30");
    expect(formatUtcOffset(-420, false)).toBe("UTC-07");
    expect(timeZoneOffsetMinutes("Asia/Tokyo", new Date("2026-01-01T00:00:00Z"))).toBe(540);
  });
});
