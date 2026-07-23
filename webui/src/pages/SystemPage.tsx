import { Button, Chip, Surface, toast } from "@heroui/react";
import { useQuery } from "@tanstack/react-query";
import {
  IconCircleCheck as CheckCircle2,
  IconCloudCog as CloudCog,
  IconCloudDataConnection as CloudDataConnection,
  IconFileCode as FileCode2,
  IconFolderOpen as FolderOpen,
  IconPlugConnected as PlugConnected,
  IconPlugConnectedX as PlugConnectedX,
  IconRefresh as RefreshCw,
} from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

import { PageHeader, PageLoading } from "../components/ui";
import { api, errorText } from "../lib/api";
import { useRealtime, type RealtimeStatus } from "../lib/realtime";
import type { ProjectSummary } from "../types";

export function SystemPage() {
  const { t, i18n } = useTranslation();
  const realtime = useRealtime();
  const project = useQuery({ queryKey: ["project"], queryFn: () => api<ProjectSummary>("/project") });
  const pawchive = useQuery({
    queryKey: ["pawchive-version"],
    queryFn: () => api<{ version: string }>("/pawchive/site-version"),
    enabled: false,
    retry: false,
  });
  if (project.isLoading) return <PageLoading />;

  async function checkVersion() {
    const result = await pawchive.refetch();
    if (result.error) toast.danger(t("system.unavailable"), { description: errorText(result.error) });
    else toast.success(t("system.pawchiveVersion"), { description: result.data?.version });
  }

  const rows = [
    { label: t("overview.projectPath"), value: project.data?.root, icon: FolderOpen },
    { label: t("system.projectConfig"), value: project.data?.project_config, icon: FileCode2 },
    { label: t("system.environmentFiles"), value: project.data?.dotenv_files.join(" · "), icon: CloudCog },
  ];
  const realtimeColor = realtimeStatusColor(realtime.status);
  const RealtimeIcon = realtime.status === "connected" ? PlugConnected : PlugConnectedX;
  const lastUpdate = realtime.lastSignalAt
    ? new Intl.DateTimeFormat(i18n.resolvedLanguage ?? i18n.language, {
        dateStyle: "medium",
        timeStyle: "medium",
      }).format(realtime.lastSignalAt)
    : t("realtime.neverUpdated");

  return (
    <div className="grid min-w-0 gap-6">
      <PageHeader description={t("system.description")} title={t("system.title")} />
      <section className="grid min-w-0 gap-3 md:grid-cols-2">
        <Surface className="min-w-0 rounded-lg border border-border p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm text-muted">{t("system.appVersion")}</p>
              <p className="mt-2 text-2xl font-semibold">{project.data?.version}</p>
            </div>
            <Chip color="success" size="sm" variant="soft">
              <CheckCircle2 aria-hidden="true" size={14} />
              {t("system.apiReady")}
            </Chip>
          </div>
        </Surface>
        <Surface className="min-w-0 rounded-lg border border-border p-5">
          <div className="flex min-w-0 flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              <p className="text-sm text-muted">{t("system.pawchiveVersion")}</p>
              <p className="mt-2 truncate text-2xl font-semibold">{pawchive.data?.version ?? t("common.unknown")}</p>
            </div>
            <Button className="max-w-full" isPending={pawchive.isFetching} size="sm" variant="outline" onPress={() => void checkVersion()}>
              <RefreshCw aria-hidden="true" size={16} />
              {t("system.check")}
            </Button>
          </div>
        </Surface>
      </section>
      <Surface className="grid min-w-0 gap-4 rounded-lg border border-border p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex min-w-0 items-start gap-3">
            <span
              aria-hidden="true"
              className="grid size-10 shrink-0 place-items-center rounded-lg bg-default text-muted"
            >
              <CloudDataConnection size={19} stroke={1.8} />
            </span>
            <div className="min-w-0">
              <h2 className="font-semibold text-foreground">{t("realtime.title")}</h2>
              <p className="mt-1 text-sm leading-relaxed text-muted">
                {t("realtime.description")}
              </p>
            </div>
          </div>
          <Chip color={realtimeColor} variant="soft">
            <RealtimeIcon aria-hidden="true" size={15} />
            {t(`realtime.statuses.${realtime.status}`)}
          </Chip>
        </div>
        <div className="grid gap-3 border-t border-border pt-4 sm:grid-cols-2">
          <div>
            <p className="text-xs font-medium text-muted">{t("realtime.mode")}</p>
            <p className="mt-1 text-sm text-foreground">
              {realtime.status === "fallback"
                ? t("realtime.modeFallback")
                : t("realtime.modeLive")}
            </p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted">{t("realtime.lastUpdate")}</p>
            <p className="mt-1 text-sm text-foreground">{lastUpdate}</p>
          </div>
        </div>
        <div className="flex flex-wrap justify-end gap-2">
          <Button variant="outline" onPress={realtime.refreshNow}>
            <RefreshCw aria-hidden="true" size={16} />
            {t("realtime.refreshNow")}
          </Button>
          <Button variant="primary" onPress={realtime.reconnect}>
            <PlugConnected aria-hidden="true" size={16} />
            {t("realtime.reconnect")}
          </Button>
        </div>
      </Surface>
      <section className="grid min-w-0 gap-3">
        {rows.map(({ label, value, icon: Icon }) => (
          <Surface className="flex min-w-0 items-start gap-4 rounded-lg border border-border p-4" key={label}>
            <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-default text-muted" aria-hidden="true">
              <Icon size={18} />
            </span>
            <div className="min-w-0">
              <p className="text-sm font-medium">{label}</p>
              <code className="mt-1 block break-all text-xs leading-relaxed text-muted">{value}</code>
            </div>
          </Surface>
        ))}
      </section>
    </div>
  );
}

function realtimeStatusColor(
  status: RealtimeStatus,
): "accent" | "danger" | "success" | "warning" {
  if (status === "connected") return "success";
  if (status === "offline") return "danger";
  if (status === "fallback" || status === "reconnecting") return "warning";
  return "accent";
}
