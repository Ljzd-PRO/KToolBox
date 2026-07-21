import { IconTools as Construction } from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

import { EmptyPanel, PageHeader } from "../components/ui";

export function PlaceholderPage({ page }: { page: string }) {
  const { t } = useTranslation();
  return (
    <div className="grid gap-6">
      <PageHeader description={t("overview.description")} title={t(`nav.${page}`)} />
      <div className="relative">
        <EmptyPanel title={t(`nav.${page}`)} />
        <Construction aria-hidden="true" className="pointer-events-none absolute left-1/2 top-10 -translate-x-1/2 text-muted" size={22} />
      </div>
    </div>
  );
}
