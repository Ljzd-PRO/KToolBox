import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import { en } from "../locales/en";
import { zhCN } from "../locales/zh-CN";

export const LANGUAGE_STORAGE_KEY = "ktoolbox-language";
export const supportedLanguages = ["en", "zh-CN"] as const;
export type AppLanguage = (typeof supportedLanguages)[number];

export const resources = {
  en: { translation: en },
  "zh-CN": { translation: zhCN },
} as const;

export function resolveLanguage(languages: readonly string[]): AppLanguage {
  return languages.some((language) => language.toLowerCase().startsWith("zh")) ? "zh-CN" : "en";
}

export function currentLanguage(): AppLanguage {
  return i18n.resolvedLanguage === "zh-CN" ? "zh-CN" : "en";
}

const storedLanguage = localStorage.getItem(LANGUAGE_STORAGE_KEY);
const initialLanguage = supportedLanguages.includes(storedLanguage as AppLanguage)
  ? (storedLanguage as AppLanguage)
  : resolveLanguage(navigator.languages?.length ? navigator.languages : [navigator.language]);

void i18n.use(initReactI18next).init({
  resources,
  lng: initialLanguage,
  fallbackLng: "en",
  supportedLngs: supportedLanguages,
  interpolation: { escapeValue: false },
  showSupportNotice: false,
});

export async function setLanguage(language: AppLanguage): Promise<void> {
  localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  await i18n.changeLanguage(language);
}

export async function toggleLanguage(): Promise<void> {
  await setLanguage(currentLanguage() === "zh-CN" ? "en" : "zh-CN");
}

export default i18n;
