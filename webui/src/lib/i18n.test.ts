import { describe, expect, it } from "vitest";

import { resources, resolveLanguage } from "./i18n";

function flatten(value: unknown, prefix = "", output = new Map<string, string>()): Map<string, string> {
  if (typeof value === "string") {
    output.set(prefix, value);
    return output;
  }
  if (!value || typeof value !== "object") return output;
  for (const [key, child] of Object.entries(value)) {
    flatten(child, prefix ? `${prefix}.${key}` : key, output);
  }
  return output;
}

function contractKey(key: string): string {
  return key.replace(/_(?:zero|one|two|few|many|other)$/, "");
}

function tokens(value: string): string[] {
  return [...value.matchAll(/{{\s*([^},\s]+).*?}}|<\/?([a-z][a-z0-9]*)>/gi)]
    .map((match) => match[1] ?? match[2])
    .sort();
}

describe("localization contracts", () => {
  it("resolves the original browser language behavior", () => {
    expect(resolveLanguage(["zh-TW", "en-US"])).toBe("zh-CN");
    expect(resolveLanguage(["fr-FR", "en-US"])).toBe("en");
  });

  it("keeps translated keys and interpolation contracts aligned", () => {
    const english = flatten(resources.en.translation);
    const chinese = flatten(resources["zh-CN"].translation);
    expect(new Set([...chinese.keys()].map(contractKey))).toEqual(new Set([...english.keys()].map(contractKey)));

    for (const [key, value] of chinese) {
      const source = english.get(key) ?? english.get(contractKey(key));
      expect(source, key).toBeDefined();
      expect(tokens(value), key).toEqual(tokens(source ?? ""));
    }
  });
});
