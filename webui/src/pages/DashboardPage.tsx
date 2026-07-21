import { Button, Chip, Surface, Table } from "@heroui/react";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, BookUser, Boxes, CheckCircle2, Clock3, Play } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { EmptyPanel, PageLoading, TaskStatusChip } from "../components/ui";
import { api } from "../lib/api";
import type { CreatorReference, ProjectSummary, TaskRecord } from "../types";

export function DashboardPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const project = useQuery({ queryKey: ["project"], queryFn: () => api<ProjectSummary>("/project") });
  const tasks = useQuery({ queryKey: ["tasks"], queryFn: () => api<TaskRecord[]>("/tasks"), refetchInterval: 2000 });
  const creators = useQuery({ queryKey: ["creators"], queryFn: () => api<CreatorReference[]>("/creators") });

  if (project.isLoading || tasks.isLoading || creators.isLoading) return <PageLoading />;
  const records = tasks.data ?? [];
  const stats = [
    {
      label: t("overview.active"),
      value: records.filter((task) => ["running", "pause_requested", "stop_requested"].includes(task.status)).length,
      icon: Play,
      tone: "blue",
    },
    {
      label: t("overview.queued"),
      value: records.filter((task) => ["queued", "blocked"].includes(task.status)).length,
      icon: Clock3,
      tone: "yellow",
    },
    {
      label: t("overview.completed"),
      value: records.filter((task) => task.status === "completed").length,
      icon: CheckCircle2,
      tone: "green",
    },
    {
      label: t("overview.creators"),
      value: (creators.data ?? []).filter((creator) => creator.enabled).length,
      icon: BookUser,
      tone: "teal",
    },
  ];

  return (
    <div className="grid gap-6">
      <section className="overview-heading flex flex-col justify-between gap-5 border-b border-border pb-6 md:flex-row md:items-end">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <Chip color="accent" size="sm" variant="soft">
              {t("overview.eyebrow")}
            </Chip>
            <span className="truncate text-xs text-muted">{project.data?.name}</span>
          </div>
          <h1 className="max-w-3xl text-2xl font-semibold text-foreground sm:text-3xl">{t("overview.title")}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted">{t("overview.description")}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="primary" onPress={() => navigate("/tasks?create=sync")}>
            <Play aria-hidden="true" size={18} />
            {t("overview.newSync")}
          </Button>
          <Button variant="outline" onPress={() => navigate("/tasks")}>
            <Boxes aria-hidden="true" size={18} />
            {t("overview.openTasks")}
          </Button>
        </div>
      </section>

      <section aria-label="Statistics" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {stats.map(({ label, value, icon: Icon, tone }) => (
          <Surface className="stat-tile rounded-lg border border-border p-4" data-tone={tone} key={label}>
            <div className="mb-4 flex items-center justify-between gap-3">
              <span className="text-sm font-medium text-muted">{label}</span>
              <span className="stat-icon grid size-9 place-items-center rounded-lg" aria-hidden="true">
                <Icon size={18} />
              </span>
            </div>
            <div className="text-3xl font-semibold tabular-nums text-foreground">{value}</div>
          </Surface>
        ))}
      </section>

      <section className="grid gap-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">{t("overview.recent")}</h2>
          <Button size="sm" variant="ghost" onPress={() => navigate("/tasks")}>
            {t("overview.openTasks")}
            <ArrowRight aria-hidden="true" size={16} />
          </Button>
        </div>
        {records.length ? (
          <Surface className="rounded-lg border border-border">
            <Table>
              <Table.ScrollContainer>
                <Table.Content aria-label={t("overview.recent")}>
                  <Table.Header>
                    <Table.Column isRowHeader>{t("common.type")}</Table.Column>
                    <Table.Column>{t("common.status")}</Table.Column>
                    <Table.Column>{t("common.created")}</Table.Column>
                    <Table.Column className="text-right">{t("common.actions")}</Table.Column>
                  </Table.Header>
                  <Table.Body>
                    {records.slice(0, 6).map((task) => (
                      <Table.Row key={task.id}>
                        <Table.Cell className="capitalize">{t(`common.${task.kind}`)}</Table.Cell>
                        <Table.Cell>
                          <TaskStatusChip status={task.status} />
                        </Table.Cell>
                        <Table.Cell className="text-muted">
                          {new Intl.DateTimeFormat(i18n.resolvedLanguage, {
                            dateStyle: "medium",
                            timeStyle: "short",
                          }).format(new Date(task.created_at))}
                        </Table.Cell>
                        <Table.Cell className="text-right">
                          <Button
                            aria-label={t("overview.openTasks")}
                            isIconOnly
                            size="sm"
                            variant="ghost"
                            onPress={() => navigate(`/tasks/${task.id}`)}
                          >
                            <ArrowRight aria-hidden="true" size={16} />
                          </Button>
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table.Content>
              </Table.ScrollContainer>
            </Table>
          </Surface>
        ) : (
          <EmptyPanel title={t("overview.empty")} />
        )}
      </section>

      <Surface className="path-strip flex min-w-0 items-center gap-3 rounded-lg border border-border px-4 py-3">
        <Boxes aria-hidden="true" className="shrink-0 text-muted" size={18} />
        <span className="shrink-0 text-xs font-medium text-muted">{t("overview.projectPath")}</span>
        <code className="min-w-0 truncate text-xs text-foreground">{project.data?.root}</code>
      </Surface>
    </div>
  );
}
