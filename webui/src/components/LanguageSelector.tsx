import { Dropdown } from "@heroui/react";
import { IconLanguage } from "@tabler/icons-react";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import {
  currentLanguage,
  languageOptions,
  setLanguage,
  type AppLanguage,
} from "../lib/i18n";

export function LanguageSelector({ compact = true }: { compact?: boolean }) {
  const { t } = useTranslation();
  const language = currentLanguage();
  const selectedKeys = useMemo(() => new Set([language]), [language]);

  return (
    <Dropdown>
      <Dropdown.Trigger
        aria-label={t("shell.language")}
        className={
          compact
            ? "grid size-11 min-w-11 shrink-0 place-items-center rounded-lg text-foreground outline-none transition-colors hover:bg-default focus-visible:ring-2 focus-visible:ring-focus"
            : "flex min-h-11 items-center gap-2 rounded-lg px-3 text-sm font-semibold text-foreground outline-none transition-colors hover:bg-default focus-visible:ring-2 focus-visible:ring-focus"
        }
      >
        <IconLanguage aria-hidden="true" size={18} stroke={1.8} />
        {compact ? null : <span>{languageOptions.find((option) => option.code === language)?.nativeName}</span>}
      </Dropdown.Trigger>
      <Dropdown.Popover className="min-w-56" placement="bottom end">
        <Dropdown.Menu
          aria-label={t("shell.language")}
          selectedKeys={selectedKeys}
          selectionMode="single"
          onAction={(key) => {
            const next = String(key) as AppLanguage;
            if (next !== language) void setLanguage(next);
          }}
        >
          {languageOptions.map((option) => (
            <Dropdown.Item id={option.code} key={option.code} textValue={option.nativeName}>
              <span
                aria-hidden="true"
                className="grid size-7 shrink-0 place-items-center rounded-md bg-default font-mono text-[0.6875rem] font-bold text-muted"
              >
                {option.shortName}
              </span>
              <span className="min-w-0 flex-1 truncate font-medium" lang={option.code}>
                {option.nativeName}
              </span>
              <Dropdown.ItemIndicator type="checkmark" />
            </Dropdown.Item>
          ))}
        </Dropdown.Menu>
      </Dropdown.Popover>
    </Dropdown>
  );
}
