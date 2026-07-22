import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import { en } from "../locales/en";
import { fr } from "../locales/fr";
import { ja } from "../locales/ja";
import { ko } from "../locales/ko";
import { ru } from "../locales/ru";
import { zhCN } from "../locales/zh-CN";
import { zhHant } from "../locales/zh-Hant";

export const LANGUAGE_STORAGE_KEY = "ktoolbox-language";
export const supportedLanguages = ["zh-CN", "zh-Hant", "en", "ja", "ko", "fr", "ru"] as const;
export type AppLanguage = (typeof supportedLanguages)[number];

export type LanguageOption = {
  code: AppLanguage;
  nativeName: string;
  shortName: string;
  ariaLocale: string;
};

export const languageOptions: readonly LanguageOption[] = [
  { code: "zh-CN", nativeName: "简体中文", shortName: "简", ariaLocale: "zh-CN" },
  { code: "zh-Hant", nativeName: "繁體中文", shortName: "繁", ariaLocale: "zh-TW" },
  { code: "en", nativeName: "English", shortName: "EN", ariaLocale: "en-US" },
  { code: "ja", nativeName: "日本語", shortName: "日", ariaLocale: "ja-JP" },
  { code: "ko", nativeName: "한국어", shortName: "한", ariaLocale: "ko-KR" },
  { code: "fr", nativeName: "Français", shortName: "FR", ariaLocale: "fr-FR" },
  { code: "ru", nativeName: "Русский", shortName: "RU", ariaLocale: "ru-RU" },
] as const;

export const resources = {
  "zh-CN": { translation: zhCN },
  "zh-Hant": { translation: zhHant },
  en: { translation: en },
  ja: { translation: ja },
  ko: { translation: ko },
  fr: { translation: fr },
  ru: { translation: ru },
} as const;

export function resolveLanguage(languages: readonly string[]): AppLanguage {
  for (const candidate of languages) {
    const language = candidate.toLowerCase().replaceAll("_", "-");
    if (/^zh(?:-|$)/.test(language)) {
      return /(?:^|-)(?:tw|hk|mo|hant)(?:-|$)/.test(language) ? "zh-Hant" : "zh-CN";
    }
    if (/^ja(?:-|$)/.test(language)) return "ja";
    if (/^ko(?:-|$)/.test(language)) return "ko";
    if (/^fr(?:-|$)/.test(language)) return "fr";
    if (/^ru(?:-|$)/.test(language)) return "ru";
    if (/^en(?:-|$)/.test(language)) return "en";
  }
  return "en";
}

export function normalizeLanguage(language?: string): AppLanguage {
  return supportedLanguages.includes(language as AppLanguage)
    ? (language as AppLanguage)
    : resolveLanguage(language ? [language] : []);
}

export function currentLanguage(): AppLanguage {
  return normalizeLanguage(i18n.resolvedLanguage ?? i18n.language);
}

export function reactAriaLocale(language = currentLanguage()): string {
  return languageOptions.find((option) => option.code === language)?.ariaLocale ?? "en-US";
}

function applyDocumentLanguage(language: AppLanguage): void {
  document.documentElement.lang = language;
}

const storedLanguage = localStorage.getItem(LANGUAGE_STORAGE_KEY);
const initialLanguage = supportedLanguages.includes(storedLanguage as AppLanguage)
  ? (storedLanguage as AppLanguage)
  : resolveLanguage(navigator.languages?.length ? navigator.languages : [navigator.language]);

applyDocumentLanguage(initialLanguage);
void i18n.use(initReactI18next).init({
  resources,
  lng: initialLanguage,
  fallbackLng: "en",
  supportedLngs: supportedLanguages,
  load: "currentOnly",
  interpolation: { escapeValue: false },
  showSupportNotice: false,
});

export async function setLanguage(language: AppLanguage): Promise<void> {
  localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  applyDocumentLanguage(language);
  await i18n.changeLanguage(language);
}

export default i18n;
