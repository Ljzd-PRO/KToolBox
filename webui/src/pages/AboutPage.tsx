import { Chip, Surface } from "@heroui/react";
import { useQuery } from "@tanstack/react-query";
import {
  IconBook2,
  IconBrandGithub,
  IconBug,
  IconExternalLink,
  IconInfoCircle,
  IconLicense,
  IconTool,
  IconUser,
  IconBrandPython,
  type TablerIcon,
} from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

import { InlineCode, PageHeader, PageLoading } from "../components/ui";
import { api } from "../lib/api";
import type { AboutInfo } from "../types";

export function AboutPage() {
  const { t } = useTranslation();
  const about = useQuery({ queryKey: ["about"], queryFn: () => api<AboutInfo>("/about") });
  if (about.isLoading) return <PageLoading />;
  if (!about.data) return null;

  const resources = [
    { key: "documentation", label: t("about.documentation"), icon: IconBook2 },
    { key: "repository", label: t("about.repository"), icon: IconBrandGithub },
    { key: "issues", label: t("about.issues"), icon: IconBug },
  ].filter(({ key }) => Boolean(about.data.urls[key]));

  return (
    <div className="grid min-w-0 gap-6">
      <PageHeader description={t("about.description")} title={t("about.title")} />
      <Surface className="flex min-w-0 flex-col gap-3 rounded-lg border border-border p-4 sm:flex-row sm:items-start sm:gap-4 sm:p-5">
        <span
          aria-hidden="true"
          className="brand-mark grid size-14 shrink-0 place-items-center rounded-lg"
        >
          <IconTool size={27} stroke={1.8} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-bold text-foreground">{t("brand")}</h2>
            <Chip color="accent" size="sm" variant="soft">
              v{about.data.version.replace(/^v/, "")}
            </Chip>
          </div>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
            {t("about.productDescription")}
          </p>
        </div>
      </Surface>
      <section className="grid min-w-0 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <AboutFact icon={IconLicense} label={t("about.license")} value={about.data.license} />
        <AboutFact
          icon={IconBrandPython}
          label={t("about.pythonVersion")}
          value={about.data.python_version}
        />
        <AboutFact
          icon={IconUser}
          label={t("about.author")}
          value={about.data.authors.join(", ")}
        />
      </section>
      <Surface className="overflow-hidden rounded-lg border border-border">
        <div className="flex items-center gap-3 border-b border-border px-4 py-3">
          <span aria-hidden="true" className="grid size-9 shrink-0 place-items-center rounded-lg bg-default text-muted">
            <IconInfoCircle size={18} stroke={1.8} />
          </span>
          <div className="min-w-0">
            <h2 className="font-semibold text-foreground">{t("about.resources")}</h2>
            <p className="mt-0.5 text-xs text-muted">{t("about.resourcesDescription")}</p>
          </div>
        </div>
        <div className="divide-y divide-border">
          {resources.map(({ key, label, icon: Icon }) => (
            <a
              aria-label={t("about.openResource", { name: label })}
              className="group flex min-h-14 min-w-0 items-center gap-3 px-4 py-3 outline-none transition-colors hover:bg-default focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-focus"
              href={about.data.urls[key]}
              key={key}
              rel="noopener noreferrer"
              target="_blank"
            >
              <Icon aria-hidden="true" className="shrink-0 text-accent" size={18} stroke={1.8} />
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-medium text-foreground">{label}</span>
                <InlineCode className="about-resource-url mt-0.5 border-0 bg-transparent p-0 text-xs font-normal text-muted" title={about.data.urls[key]}>
                  {about.data.urls[key]}
                </InlineCode>
              </span>
              <IconExternalLink
                aria-hidden="true"
                className="shrink-0 text-muted transition-colors group-hover:text-foreground"
                size={16}
              />
            </a>
          ))}
        </div>
      </Surface>
    </div>
  );
}

function AboutFact({
  icon: Icon,
  label,
  value,
}: {
  icon: TablerIcon;
  label: string;
  value: string;
}) {
  return (
    <Surface className="flex min-w-0 items-start gap-3 rounded-lg border border-border p-4">
      <span aria-hidden="true" className="grid size-10 shrink-0 place-items-center rounded-lg bg-default text-muted">
        <Icon size={19} stroke={1.8} />
      </span>
      <div className="min-w-0">
        <p className="text-xs font-medium text-muted">{label}</p>
        <p className="mt-1 break-words text-sm font-semibold text-foreground">{value}</p>
      </div>
    </Surface>
  );
}
