import { describe, expect, it } from "vitest";

import { normalizeTableSort, stableSort, taskStatusRank } from "./sorting";

describe("stableSort", () => {
  it("sorts numbers naturally and keeps empty values last in both directions", () => {
    const records = [
      { id: "empty", value: null },
      { id: "ten", value: 10 },
      { id: "two", value: 2 },
    ];
    const ascending = stableSort(records, { column: "value", direction: "ascending" }, (item) => item.value, "en");
    const descending = stableSort(records, { column: "value", direction: "descending" }, (item) => item.value, "en");
    expect(ascending.map((item) => item.id)).toEqual(["two", "ten", "empty"]);
    expect(descending.map((item) => item.id)).toEqual(["ten", "two", "empty"]);
  });

  it("uses locale-aware natural text comparison and remains stable", () => {
    const records = [
      { id: "first", value: "作品 10" },
      { id: "second", value: "作品 2" },
      { id: "same", value: "作品 2" },
    ];
    const result = stableSort(records, { column: "value", direction: "ascending" }, (item) => item.value, "zh-CN");
    expect(result.map((item) => item.id)).toEqual(["second", "same", "first"]);
  });

  it("uses a fixed task status priority and sensible first-click directions", () => {
    expect(taskStatusRank("running")).toBeLessThan(taskStatusRank("queued"));
    expect(taskStatusRank("queued")).toBeLessThan(taskStatusRank("completed"));
    expect(normalizeTableSort(null, { column: "created", direction: "ascending" }, new Set(["created"]))).toEqual({
      column: "created",
      direction: "descending",
    });
  });
});
