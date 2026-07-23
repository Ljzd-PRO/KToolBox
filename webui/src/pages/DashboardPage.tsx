import { Button, Chip, Surface, Table } from "@heroui/react";
import type { SortDescriptor } from "@heroui/react";
import { useQuery } from "@tanstack/react-query";
import {
  IconAddressBook as BookUser,
  IconArrowRight as ArrowRight,
  IconCircleCheck as CheckCircle2,
  IconClock as Clock3,
  IconPackages as Boxes,
  IconPlayerPlay as Play,
} from "@tabler/icons-react";
import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import {
  DataTableFrame,
  EmptyPanel,
  MobileSortControls,
  PageLoading,
  SortableColumn,
  TaskStatusChip,
} from "../components/ui";
import { TaskTarget } from "../components/TaskTarget";
import { api } from "../lib/api";
import { stableSort, taskStatusRank, taskTargetSortText } from "../lib/sorting";
import type { CreatorRosterItem, ProjectSummary, TaskRecord } from "../types";

export function DashboardPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const project = useQuery({ queryKey: ["project"], queryFn: () => api<ProjectSummary>("/project") });
  const tasks = useQuery({ queryKey: ["tasks"], queryFn: () => api<TaskRecord[]>("/tasks") });
  const creators = useQuery({ queryKey: ["creators"], queryFn: () => api<CreatorRosterItem[]>("/creators") });
  const [sortDescriptor, setSortDescriptor] = useState<SortDescriptor>({
    column: "created",
    direction: "descending",
  });

  const records = useMemo(() => tasks.data ?? [], [tasks.data]);
  const stats = [
    {
      label: t("overview.active"),
      value: records.filter((task) => ["running", "pause_requested", "stop_requested"].includes(task.status)).length,
      icon: Play,
      tone: "blue",
      href: "/tasks?status=active",
    },
    {
      label: t("overview.queued"),
      value: records.filter((task) => ["queued", "blocked"].includes(task.status)).length,
      icon: Clock3,
      tone: "yellow",
      href: "/tasks?status=waiting",
    },
    {
      label: t("overview.completed"),
      value: records.filter((task) => task.status === "completed").length,
      icon: CheckCircle2,
      tone: "green",
      href: "/tasks?status=completed",
    },
    {
      label: t("overview.creators"),
      value: (creators.data ?? []).filter((creator) => creator.enabled).length,
      icon: BookUser,
      tone: "teal",
      href: "/creators?status=enabled",
    },
  ];
  const recentRecords = useMemo(() => {
    const latest = [...records]
      .sort((left, right) => Date.parse(right.created_at) - Date.parse(left.created_at))
      .slice(0, 6);
    return stableSort(
      latest,
      sortDescriptor,
      (task, column) => {
        if (column === "target") return taskTargetSortText(task, creators.data ?? []);
        if (column === "status") return taskStatusRank(task.status);
        return Date.parse(task.created_at);
      },
      i18n.resolvedLanguage ?? i18n.language,
    );
  }, [creators.data, i18n.language, i18n.resolvedLanguage, records, sortDescriptor]);
  const sortOptions = [
    { value: "target", label: t("tasks.target") },
    { value: "status", label: t("common.status") },
    { value: "created", label: t("common.created") },
  ];

  if (project.isLoading || tasks.isLoading || creators.isLoading) return <PageLoading />;

  return (
    <div className="grid gap-5">
      <section className="overview-heading flex flex-col justify-between gap-3 lg:flex-row lg:items-center">
        <div className="flex min-w-0 items-center gap-2">
          <Chip color="accent" size="sm" variant="soft">
            {t("overview.eyebrow")}
          </Chip>
          <span className="truncate text-xs font-medium text-muted">{project.data?.name}</span>
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

      <section aria-label={t("overview.statistics")} className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {stats.map(({ label, value, icon: Icon, tone, href }) => (
          <Link aria-label={`${label}: ${value}`} className="stat-link rounded-lg" key={label} to={href}>
            <Surface className="stat-tile h-full rounded-lg border border-border p-4" data-tone={tone}>
              <div className="mb-4 flex items-center justify-between gap-3">
                <span className="text-sm font-medium text-muted">{label}</span>
                <span className="stat-icon grid size-9 place-items-center rounded-lg" aria-hidden="true">
                  <Icon size={18} />
                </span>
              </div>
              <div className="flex items-end justify-between gap-3">
                <div className="text-3xl font-semibold tabular-nums text-foreground">{value}</div>
                <ArrowRight aria-hidden="true" className="stat-arrow text-muted" size={17} />
              </div>
            </Surface>
          </Link>
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
          <>
            <MobileSortControls
              className="lg:hidden"
              descendingByDefault={new Set(["created"])}
              descriptor={sortDescriptor}
              options={sortOptions}
              onChange={(descriptor) => descriptor && setSortDescriptor(descriptor)}
            />
            <DataTableFrame className="hidden lg:block">
              <Table.Content
                aria-label={t("overview.recent")}
                sortDescriptor={sortDescriptor}
                onSortChange={setSortDescriptor}
              >
                  <Table.Header>
                    <SortableColumn id="target" isRowHeader>{t("tasks.target")}</SortableColumn>
                    <SortableColumn id="status">{t("common.status")}</SortableColumn>
                    <SortableColumn id="created">{t("common.created")}</SortableColumn>
                    <Table.Column className="text-right">{t("common.actions")}</Table.Column>
                  </Table.Header>
                  <Table.Body>
                    {recentRecords.map((task) => (
                      <Table.Row key={task.id}>
                        <Table.Cell className="min-w-60"><TaskTarget creators={creators.data} task={task} /></Table.Cell>
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
            </DataTableFrame>
            <div className="grid gap-3 lg:hidden">
              {recentRecords.map((task) => (
                <Surface className="grid gap-3 rounded-lg border border-border p-4" key={task.id}>
                  <div className="flex min-w-0 items-start justify-between gap-3">
                    <TaskTarget creators={creators.data} task={task} />
                    <TaskStatusChip status={task.status} />
                  </div>
                  <div className="flex items-center justify-between gap-3 border-t border-border pt-3">
                    <time className="text-xs text-muted">{new Intl.DateTimeFormat(i18n.resolvedLanguage, { dateStyle: "medium", timeStyle: "short" }).format(new Date(task.created_at))}</time>
                    <Button isIconOnly aria-label={t("tasks.details")} size="sm" variant="ghost" onPress={() => navigate(`/tasks/${task.id}`)}>
                      <ArrowRight aria-hidden="true" size={16} />
                    </Button>
                  </div>
                </Surface>
              ))}
            </div>
          </>
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
