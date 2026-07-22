import { describe, expect, it } from "vitest";

import { languageOptions, resources, resolveLanguage, supportedLanguages } from "./i18n";

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
  it("maps browser languages to all supported locales", () => {
    expect(resolveLanguage(["zh-TW", "en-US"])).toBe("zh-Hant");
    expect(resolveLanguage(["zh-HK"])).toBe("zh-Hant");
    expect(resolveLanguage(["zh-SG"])).toBe("zh-CN");
    expect(resolveLanguage(["ja-JP"])).toBe("ja");
    expect(resolveLanguage(["ko-KR"])).toBe("ko");
    expect(resolveLanguage(["fr-CA"])).toBe("fr");
    expect(resolveLanguage(["ru-RU"])).toBe("ru");
    expect(resolveLanguage(["de-DE", "en-GB"])).toBe("en");
    expect(resolveLanguage(["de-DE"])).toBe("en");
  });

  it("registers each locale with one native label and React Aria locale", () => {
    expect(languageOptions.map((option) => option.code)).toEqual(supportedLanguages);
    expect(new Set(languageOptions.map((option) => option.nativeName)).size).toBe(supportedLanguages.length);
    expect(languageOptions.every((option) => option.ariaLocale.includes("-"))).toBe(true);
  });

  it.each(supportedLanguages.filter((language) => language !== "en"))(
    "keeps %s keys and interpolation contracts aligned",
    (language) => {
    const english = flatten(resources.en.translation);
      const translated = flatten(resources[language].translation);
      expect(new Set([...translated.keys()].map(contractKey))).toEqual(new Set([...english.keys()].map(contractKey)));

      for (const [key, value] of translated) {
      const source = english.get(key) ?? english.get(contractKey(key));
      expect(source, key).toBeDefined();
      expect(tokens(value), key).toEqual(tokens(source ?? ""));
    }
    },
  );
});
