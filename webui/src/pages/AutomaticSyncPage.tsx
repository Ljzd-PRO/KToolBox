import {
  Alert,
  Button,
  Chip,
  SearchField,
  Surface,
  Table,
  Tabs,
  toast,
} from "@heroui/react";
import type { SortDescriptor } from "@heroui/react";
import { parseDate, today, getLocalTimeZone, type DateValue } from "@internationalized/date";
import {
  IconAlertTriangle,
  IconCalendarClock,
  IconCalendarRepeat,
  IconCheck,
  IconClock,
  IconEdit,
  IconFolder,
  IconHistory,
  IconPlayerPause,
  IconPlayerPlay,
  IconPlus,
  IconRefresh,
  IconSearch,
  IconTags,
  IconTrash,
  IconUser,
  IconUsers,
  IconX,
} from "@tabler/icons-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CronExpressionParser } from "cron-parser";
import cronstrue from "cronstrue";
import "cronstrue/locales/fr";
import "cronstrue/locales/ja";
import "cronstrue/locales/ko";
import "cronstrue/locales/ru";
import "cronstrue/locales/zh_CN";
import "cronstrue/locales/zh_TW";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import {
  ChipListField,
  ConfirmModal,
  DataTableFrame,
  DatePickerInput,
  EmptyPanel,
  FormField,
  FormModal,
  FormSurface,
  FormSwitchField,
  IconButton,
  MobileSortControls,
  NumberInput,
  PageHeader,
  PageLoading,
  PlatformLabel,
  SelectField,
  SelectionCheckbox,
  SortableColumn,
  TableColumnLabel,
  ComboBoxField,
} from "../components/ui";
import { RemotePathField } from "../components/RemotePathField";
import { api, ApiError, errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import { formatDateTime } from "../lib/format";
import { TASK_OUTPUT_PATH_SELECTOR } from "../lib/pathSelectors";
import { stableSort } from "../lib/sorting";
import type {
  AutomaticSyncPlan,
  AutomaticSyncPlanList,
  AutomaticSyncRun,
  AutomaticSyncRunNow,
  AutomaticSyncUpdate,
  CreatorRosterItem,
} from "../types";

type UpdatePeriod = "today" | "1d" | "7d" | "14d" | "30d";
type Frequency = "hourly" | "daily" | "weekly" | "monthly";
type CronMode = "visual" | "advanced";

type PlanDraft = {
  id: string;
  name: string;
  enabled: boolean;
  creators: string[];
  initial_start_date: string | null;
  schedule:
    | { kind: "cron"; expression: string; timezone: string }
    | { kind: "interval"; every: number; unit: "minutes" | "hours" | "days"; anchor_at: string | null; timezone: string };
  options: {
    output: string;
    save_creator_indices: boolean;
    mix_posts: boolean | null;
    keywords: string[];
      keywords_exclude: string[];
  };
};

const runStatusOrder = ["running", "queued", "paused", "failed", "interrupted", "completed", "skipped"];
const timezoneSuggestions = [
  "Asia/Shanghai",
  "Asia/Tokyo",
  "Asia/Seoul",
  "Europe/Paris",
  "Europe/Moscow",
  "America/New_York",
  "America/Los_Angeles",
  "UTC",
];

function blankPlan(): PlanDraft {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  const suffix = globalThis.crypto?.randomUUID?.().slice(0, 8) ?? Date.now().toString(36);
  return {
    id: `auto-${suffix}`,
    name: "",
    enabled: true,
    creators: [],
    schedule: { kind: "cron", expression: "0 3 * * *", timezone },
    initial_start_date: today(getLocalTimeZone()).toString(),
    options: {
      output: "",
      save_creator_indices: false,
      mix_posts: null,
      keywords: [],
      keywords_exclude: [],
    },
  };
}

function normalizePlan(plan: AutomaticSyncPlan): PlanDraft {
  const schedule = plan.schedule?.kind === "interval"
    ? {
        kind: "interval" as const,
        every: plan.schedule.every,
        unit: plan.schedule.unit,
        anchor_at: plan.schedule.anchor_at ?? null,
        timezone: plan.schedule.timezone,
      }
    : {
        kind: "cron" as const,
        expression: plan.schedule?.expression ?? "0 3 * * *",
        timezone: plan.schedule?.timezone ?? "UTC",
      };
  return {
    ...plan,
    schedule,
    initial_start_date: plan.initial_start_date ?? null,
    options: {
      output: plan.options?.output ?? "",
      save_creator_indices: plan.options?.save_creator_indices ?? false,
      mix_posts: plan.options?.mix_posts ?? null,
      keywords: [...(plan.options?.keywords ?? [])],
      keywords_exclude: [...(plan.options?.keywords_exclude ?? [])],
    },
  };
}

function creatorKey(creator: CreatorRosterItem): string {
  return `${creator.service}:${creator.creator_id}`;
}

function creatorLabel(creator: CreatorRosterItem): string {
  return creator.name || creator.alias || creator.creator_id;
}

function parseVisualCron(expression: string): {
  frequency: Frequency;
  hour: number;
  minute: number;
  weekdays: number[];
  monthDay: number;
} | null {
  const [minuteText, hourText, day, month, weekday] = expression.trim().split(/\s+/u);
  const minute = Number(minuteText);
  const hour = hourText === "*" ? 0 : Number(hourText);
  if (!Number.isInteger(minute) || minute < 0 || minute > 59 || month !== "*") return null;
  if (hourText === "*" && day === "*" && weekday === "*") {
    return { frequency: "hourly", hour: 0, minute, weekdays: [1], monthDay: 1 };
  }
  if (!Number.isInteger(hour) || hour < 0 || hour > 23) return null;
  if (day === "*" && weekday === "*") {
    return { frequency: "daily", hour, minute, weekdays: [1], monthDay: 1 };
  }
  if (day === "*" && /^([0-6],?)+$/u.test(weekday)) {
    return { frequency: "weekly", hour, minute, weekdays: weekday.split(",").map(Number), monthDay: 1 };
  }
  const monthDay = Number(day);
  if (weekday === "*" && Number.isInteger(monthDay) && monthDay >= 1 && monthDay <= 31) {
    return { frequency: "monthly", hour, minute, weekdays: [1], monthDay };
  }
  return null;
}

function buildCron(
  frequency: Frequency,
  hour: number,
  minute: number,
  weekdays: number[],
  monthDay: number,
): string {
  if (frequency === "hourly") return `${minute} * * * *`;
  if (frequency === "weekly") return `${minute} ${hour} * * ${weekdays.length ? weekdays.join(",") : 1}`;
  if (frequency === "monthly") return `${minute} ${hour} ${monthDay} * *`;
  return `${minute} ${hour} * * *`;
}

function intervalMinutes(plan: PlanDraft): number {
  if (plan.schedule.kind !== "interval") return 0;
  return plan.schedule.every * { minutes: 1, hours: 60, days: 1440 }[plan.schedule.unit];
}

function runTone(status: AutomaticSyncRun["status"]): React.ComponentProps<typeof Chip>["color"] {
  if (status === "completed") return "success";
  if (status === "failed" || status === "interrupted") return "danger";
  if (status === "running") return "accent";
  if (status === "paused" || status === "skipped") return "warning";
  return "default";
}

export function AutomaticSyncPage() {
  const { t, i18n } = useTranslation();
  const { session } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [period, setPeriod] = useState<UpdatePeriod>("30d");
  const [editor, setEditor] = useState<PlanDraft | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<AutomaticSyncPlan | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [cronMode, setCronMode] = useState<CronMode>("visual");
  const [planSort, setPlanSort] = useState<SortDescriptor>({ column: "name", direction: "ascending" });
  const [updateSort, setUpdateSort] = useState<SortDescriptor>({ column: "discovered", direction: "descending" });
  const [runSort, setRunSort] = useState<SortDescriptor>({ column: "started", direction: "descending" });
  const updateTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  const updatePeriodOptions = (["today", "1d", "7d", "14d", "30d"] as const).map((value) => ({
    value,
    label: t(`automaticSync.periods.${value}`),
  }));
  const updatePeriodLabel = updatePeriodOptions.find((option) => option.value === period)?.label ?? period;

  const plansQuery = useQuery({
    queryKey: ["auto-sync-plans"],
    queryFn: () => api<AutomaticSyncPlanList>("/auto-sync/plans"),
  });
  const creatorsQuery = useQuery({
    queryKey: ["creators"],
    queryFn: () => api<CreatorRosterItem[]>("/creators"),
  });
  const runsQuery = useQuery({
    queryKey: ["auto-sync-runs"],
    queryFn: () => api<AutomaticSyncRun[]>("/auto-sync/runs?limit=100"),
  });
  const updatesQuery = useQuery({
    queryKey: ["auto-sync-updates", period, updateTimezone],
    queryFn: () => {
      const parameters = new URLSearchParams({ period, timezone: updateTimezone });
      return api<AutomaticSyncUpdate[]>(`/auto-sync/updates?${parameters.toString()}`);
    },
  });

  const plans = plansQuery.data?.plans ?? [];
  const runs = runsQuery.data ?? [];
  const updates = updatesQuery.data ?? [];
  const activeRuns = runs.filter((run) => ["queued", "running", "paused"].includes(run.status));
  const newWorkCount = updates.reduce((total, item) => total + item.new_posts, 0);
  const sortedPlans = stableSort(
    plans,
    planSort,
    (plan, column) => {
      if (column === "name") return plan.name;
      if (column === "schedule") return scheduleText(plan);
      if (column === "creators") return plan.creators.length;
      if (column === "nextRun") return plansQuery.data?.next_runs[plan.id] ? Date.parse(plansQuery.data.next_runs[plan.id] ?? "") : null;
      return plan.enabled;
    },
    i18n.resolvedLanguage ?? i18n.language,
  );
  const sortedUpdates = stableSort(
    updates,
    updateSort,
    (item, column) => {
      if (column === "creator") return item.creator_name || item.creator_id;
      if (column === "platform") return item.service;
      if (column === "newWorks") return item.new_posts;
      return Date.parse(item.last_discovered_at);
    },
    i18n.resolvedLanguage ?? i18n.language,
  );
  const sortedRuns = stableSort(
    runs,
    runSort,
    (run, column) => {
      if (column === "name") return run.plan_name;
      if (column === "status") return runStatusOrder.indexOf(run.status);
      if (column === "trigger") return run.trigger;
      return Date.parse(run.started_at ?? run.created_at);
    },
    i18n.resolvedLanguage ?? i18n.language,
  );

  if (plansQuery.isLoading || creatorsQuery.isLoading || runsQuery.isLoading) return <PageLoading />;

  function openNew() {
    setEditingId(null);
    setCronMode("visual");
    setSearch("");
    setEditor(blankPlan());
  }

  function openEdit(plan: AutomaticSyncPlan) {
    const draft = normalizePlan(plan);
    setEditingId(plan.id);
    setCronMode(draft.schedule.kind === "cron" && parseVisualCron(draft.schedule.expression) ? "visual" : "advanced");
    setSearch("");
    setEditor(draft);
  }

  async function refreshAll() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["auto-sync-plans"] }),
      queryClient.invalidateQueries({ queryKey: ["auto-sync-runs"] }),
      queryClient.invalidateQueries({ queryKey: ["auto-sync-updates"] }),
      queryClient.invalidateQueries({ queryKey: ["tasks"] }),
    ]);
  }

  async function mutatePlan(path: string, method: string, success: string) {
    if (!session || !plansQuery.data) return;
    setBusy(path);
    try {
      await api(path, {
        method,
        csrfToken: session.csrf_token,
        headers: { "If-Match": `"${plansQuery.data.revision}"` },
      });
      toast.success(success);
      await refreshAll();
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    } finally {
      setBusy(null);
    }
  }

  async function savePlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editor || !session || !plansQuery.data) return;
    const validation = validateDraft(editor);
    if (validation) {
      toast.warning(t("common.error"), { description: t(validation) });
      return;
    }
    setBusy("save");
    try {
      await api<AutomaticSyncPlanList>(
        editingId ? `/auto-sync/plans/${editingId}` : "/auto-sync/plans",
        {
          method: editingId ? "PUT" : "POST",
          body: {
            ...editor,
            options: {
              ...editor.options,
              output: editor.options.output.trim() || null,
            },
          },
          csrfToken: session.csrf_token,
          headers: { "If-Match": `"${plansQuery.data.revision}"` },
        },
      );
      toast.success(t(editingId ? "automaticSync.messages.updated" : "automaticSync.messages.created"));
      setEditor(null);
      await refreshAll();
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    } finally {
      setBusy(null);
    }
  }

  async function runNow(plan: AutomaticSyncPlan) {
    if (!session) return;
    setBusy(`run:${plan.id}`);
    try {
      const result = await api<AutomaticSyncRunNow>(`/auto-sync/plans/${plan.id}/run`, {
        method: "POST",
        csrfToken: session.csrf_token,
      });
      toast.success(t("automaticSync.messages.started"));
      await refreshAll();
      navigate(`/tasks/${result.task_id}`);
    } catch (error) {
      if (error instanceof ApiError && error.status === 409 && isRecord(error.detail)) {
        const taskId = typeof error.detail.current_task_id === "string"
          ? error.detail.current_task_id
          : isRecord(error.detail.detail) && typeof error.detail.detail.current_task_id === "string"
            ? error.detail.detail.current_task_id
            : null;
        toast.warning(t("automaticSync.messages.conflict"));
        if (taskId) navigate(`/tasks/${taskId}`);
      } else {
        toast.danger(t("common.error"), { description: errorText(error) });
      }
    } finally {
      setBusy(null);
    }
  }

  async function removePlan() {
    if (!deleteTarget) return;
    const id = deleteTarget.id;
    await mutatePlan(`/auto-sync/plans/${id}`, "DELETE", t("automaticSync.messages.deleted"));
    setDeleteTarget(null);
  }

  const stats = [
    { label: t("automaticSync.stats.active"), value: plans.filter((plan) => plan.enabled).length, icon: IconCalendarRepeat, tone: "blue" },
    { label: t("automaticSync.stats.paused"), value: plans.filter((plan) => !plan.enabled).length, icon: IconPlayerPause, tone: "yellow" },
    { label: t("automaticSync.stats.running"), value: activeRuns.length, icon: IconRefresh, tone: "teal" },
  ];

  return (
    <div className="grid gap-5">
      <PageHeader
        showDescription
        description={t("automaticSync.description")}
        title={t("automaticSync.title")}
        actions={
          <Button variant="primary" onPress={openNew}>
            <IconPlus aria-hidden="true" size={18} />
            {t("automaticSync.newPlan")}
          </Button>
        }
      />

      <section aria-label={t("automaticSync.title")} className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {stats.map(({ label, value, icon: Icon, tone }) => (
          <Surface className="stat-tile h-full rounded-lg border border-border p-4" data-tone={tone} key={label}>
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm font-medium text-muted">{label}</span>
              <span className="stat-icon grid size-9 place-items-center rounded-lg" aria-hidden="true">
                <Icon size={18} />
              </span>
            </div>
            <p className="mt-3 text-3xl font-semibold tabular-nums text-foreground">{value}</p>
          </Surface>
        ))}
        <Surface className="stat-tile h-full rounded-lg border border-border p-4" data-tone="green">
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm font-medium text-muted">{t("automaticSync.stats.newWorks")}</span>
            <span className="stat-icon grid size-9 place-items-center rounded-lg" aria-hidden="true">
              <IconHistory size={18} />
            </span>
          </div>
          <p className="mt-3 text-3xl font-semibold tabular-nums text-foreground">{newWorkCount}</p>
          <div className="mt-3">
            <SelectField
              icon={IconCalendarClock}
              label={t("automaticSync.statsPeriod")}
              value={period}
              options={updatePeriodOptions}
              onChange={(value) => setPeriod(value as UpdatePeriod)}
            />
          </div>
        </Surface>
      </section>

      <section className="grid gap-3">
        <h2 className="text-lg font-semibold text-foreground">{t("automaticSync.plans")}</h2>
        {plans.length ? (
          <>
            <MobileSortControls
              className="xl:hidden"
              descriptor={planSort}
              options={[
                { value: "name", label: t("automaticSync.columns.name") },
                { value: "schedule", label: t("automaticSync.columns.schedule") },
                { value: "creators", label: t("automaticSync.columns.creators") },
                { value: "nextRun", label: t("automaticSync.columns.nextRun") },
                { value: "status", label: t("automaticSync.columns.status") },
              ]}
              onChange={(value) => value && setPlanSort(value)}
            />
            <DataTableFrame className="hidden xl:block">
              <Table.Content aria-label={t("automaticSync.plans")} sortDescriptor={planSort} onSortChange={setPlanSort}>
                <Table.Header>
                  <SortableColumn id="name" icon={IconCalendarRepeat} isRowHeader>{t("automaticSync.columns.name")}</SortableColumn>
                  <SortableColumn id="schedule" icon={IconClock}>{t("automaticSync.columns.schedule")}</SortableColumn>
                  <SortableColumn id="creators" icon={IconUsers}>{t("automaticSync.columns.creators")}</SortableColumn>
                  <SortableColumn id="nextRun" icon={IconCalendarClock}>{t("automaticSync.columns.nextRun")}</SortableColumn>
                  <SortableColumn id="status" icon={IconPlayerPlay}>{t("automaticSync.columns.status")}</SortableColumn>
                  <Table.Column className="w-56">
                    <TableColumnLabel icon={IconEdit}>{t("automaticSync.columns.actions")}</TableColumnLabel>
                  </Table.Column>
                </Table.Header>
                <Table.Body>
                  {sortedPlans.map((plan) => (
                    <Table.Row id={plan.id} key={plan.id}>
                      <Table.Cell>
                        <div className="grid min-w-44 gap-1">
                          <span className="font-semibold text-foreground">{plan.name}</span>
                          <code className="text-xs text-muted">{plan.id}</code>
                        </div>
                      </Table.Cell>
                      <Table.Cell className="text-sm text-muted">{scheduleText(plan)}</Table.Cell>
                      <Table.Cell className="tabular-nums">{plan.creators.length}</Table.Cell>
                      <Table.Cell className="text-sm text-muted">
                        {plansQuery.data?.next_runs[plan.id]
                          ? formatDateTime(plansQuery.data.next_runs[plan.id] ?? "", i18n.resolvedLanguage ?? i18n.language)
                          : "—"}
                      </Table.Cell>
                      <Table.Cell>
                        <Chip color={plan.enabled ? "success" : "warning"} size="sm" variant="soft">
                          {t(`automaticSync.statuses.${plan.enabled ? "enabled" : "paused"}`)}
                        </Chip>
                      </Table.Cell>
                      <Table.Cell>
                        <div className="flex justify-end gap-1">
                          <IconButton icon={IconPlayerPlay} isDisabled={busy !== null} label={t("automaticSync.runNow")} variant="ghost" onPress={() => void runNow(plan)} />
                          <IconButton
                            icon={plan.enabled ? IconPlayerPause : IconRefresh}
                            isDisabled={busy !== null}
                            label={t(plan.enabled ? "automaticSync.pause" : "automaticSync.resume")}
                            variant={plan.enabled ? "ghost" : "outline"}
                            onPress={() => void mutatePlan(
                              `/auto-sync/plans/${plan.id}/${plan.enabled ? "pause" : "resume"}`,
                              "POST",
                              t(plan.enabled ? "automaticSync.messages.paused" : "automaticSync.messages.resumed"),
                            )}
                          />
                          <IconButton icon={IconEdit} isDisabled={busy !== null} label={t("common.edit")} onPress={() => openEdit(plan)} />
                          <IconButton icon={IconTrash} isDisabled={busy !== null} label={t("common.delete")} className="text-danger" onPress={() => setDeleteTarget(plan)} />
                        </div>
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Content>
            </DataTableFrame>
            <div className="grid gap-3 md:grid-cols-2 xl:hidden">
              {sortedPlans.map((plan) => (
                <Surface className="grid gap-3 rounded-lg border border-border p-3" key={plan.id}>
                  <div className="flex min-w-0 items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-foreground">{plan.name}</p>
                      <code className="text-xs text-muted">{plan.id}</code>
                    </div>
                    <Chip color={plan.enabled ? "success" : "warning"} size="sm" variant="soft">
                      {t(`automaticSync.statuses.${plan.enabled ? "enabled" : "paused"}`)}
                    </Chip>
                  </div>
                  <dl className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-1 text-sm">
                    <dt className="text-muted">{t("automaticSync.columns.schedule")}</dt>
                    <dd className="truncate text-right">{scheduleText(plan)}</dd>
                    <dt className="text-muted">{t("automaticSync.columns.creators")}</dt>
                    <dd className="text-right tabular-nums">{plan.creators.length}</dd>
                    <dt className="text-muted">{t("automaticSync.columns.nextRun")}</dt>
                    <dd className="text-right text-xs">{plansQuery.data?.next_runs[plan.id] ? formatDateTime(plansQuery.data.next_runs[plan.id] ?? "", i18n.resolvedLanguage ?? i18n.language) : "—"}</dd>
                  </dl>
                  <div className="flex flex-wrap justify-end gap-1 border-t border-border pt-2">
                    <IconButton icon={IconPlayerPlay} isDisabled={busy !== null} label={t("automaticSync.runNow")} onPress={() => void runNow(plan)} />
                    <IconButton icon={plan.enabled ? IconPlayerPause : IconRefresh} isDisabled={busy !== null} label={t(plan.enabled ? "automaticSync.pause" : "automaticSync.resume")} onPress={() => void mutatePlan(`/auto-sync/plans/${plan.id}/${plan.enabled ? "pause" : "resume"}`, "POST", t(plan.enabled ? "automaticSync.messages.paused" : "automaticSync.messages.resumed"))} />
                    <IconButton icon={IconEdit} isDisabled={busy !== null} label={t("common.edit")} onPress={() => openEdit(plan)} />
                    <IconButton icon={IconTrash} isDisabled={busy !== null} label={t("common.delete")} className="text-danger" onPress={() => setDeleteTarget(plan)} />
                  </div>
                </Surface>
              ))}
            </div>
          </>
        ) : <EmptyPanel description={t("automaticSync.emptyPlansHint")} title={t("automaticSync.emptyPlans")} />}
      </section>

      <section className="grid gap-3">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <h2 className="text-lg font-semibold text-foreground">{t("automaticSync.updates")}</h2>
          <Chip color="accent" size="sm" variant="soft">
            {t("automaticSync.periodSummary", { period: updatePeriodLabel })}
          </Chip>
        </div>
        {updates.length ? (
          <>
            <MobileSortControls
              className="xl:hidden"
              descriptor={updateSort}
              options={[
                { value: "creator", label: t("automaticSync.columns.creator") },
                { value: "platform", label: t("automaticSync.columns.platform") },
                { value: "newWorks", label: t("automaticSync.columns.newWorks") },
                { value: "discovered", label: t("automaticSync.columns.discovered") },
              ]}
              onChange={(value) => value && setUpdateSort(value)}
            />
            <DataTableFrame className="hidden xl:block">
              <Table.Content aria-label={t("automaticSync.updates")} sortDescriptor={updateSort} onSortChange={setUpdateSort}>
                <Table.Header>
                  <SortableColumn id="creator" icon={IconUser} isRowHeader>{t("automaticSync.columns.creator")}</SortableColumn>
                  <SortableColumn id="platform" icon={IconTags}>{t("automaticSync.columns.platform")}</SortableColumn>
                  <SortableColumn id="newWorks" icon={IconHistory}>{t("automaticSync.columns.newWorks")}</SortableColumn>
                  <SortableColumn id="discovered" icon={IconClock}>{t("automaticSync.columns.discovered")}</SortableColumn>
                </Table.Header>
                <Table.Body>
                  {sortedUpdates.map((item) => (
                    <Table.Row id={`${item.service}:${item.creator_id}`} key={`${item.service}:${item.creator_id}`}>
                      <Table.Cell><span className="font-semibold">{item.creator_name || item.creator_id}</span></Table.Cell>
                      <Table.Cell><PlatformLabel platform={item.service} /></Table.Cell>
                      <Table.Cell><Chip color="success" size="sm" variant="soft">+{item.new_posts}</Chip></Table.Cell>
                      <Table.Cell className="text-sm text-muted">{formatDateTime(item.last_discovered_at, i18n.resolvedLanguage ?? i18n.language)}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Content>
            </DataTableFrame>
            <div className="grid gap-3 md:grid-cols-2 xl:hidden">
              {sortedUpdates.map((item) => (
                <Surface className="flex items-center justify-between gap-3 rounded-lg border border-border p-3" key={`${item.service}:${item.creator_id}`}>
                  <div className="min-w-0">
                    <p className="truncate font-semibold">{item.creator_name || item.creator_id}</p>
                    <div className="mt-1 text-xs text-muted"><PlatformLabel platform={item.service} /></div>
                    <time className="mt-1 block text-xs text-muted">{formatDateTime(item.last_discovered_at, i18n.resolvedLanguage ?? i18n.language)}</time>
                  </div>
                  <Chip color="success" variant="soft">+{item.new_posts}</Chip>
                </Surface>
              ))}
            </div>
          </>
        ) : <EmptyPanel description={t("automaticSync.emptyUpdatesHint")} title={t("automaticSync.emptyUpdates")} />}
      </section>

      <section className="grid gap-3">
        <h2 className="text-lg font-semibold text-foreground">{t("automaticSync.runs")}</h2>
        {runs.length ? (
          <>
            <MobileSortControls
              className="xl:hidden"
              descriptor={runSort}
              options={[
                { value: "name", label: t("automaticSync.columns.name") },
                { value: "status", label: t("automaticSync.columns.status") },
                { value: "trigger", label: t("automaticSync.columns.trigger") },
                { value: "started", label: t("automaticSync.columns.started") },
              ]}
              onChange={(value) => value && setRunSort(value)}
            />
            <DataTableFrame className="hidden xl:block">
              <Table.Content aria-label={t("automaticSync.runs")} sortDescriptor={runSort} onSortChange={setRunSort}>
                <Table.Header>
                  <SortableColumn id="name" icon={IconCalendarRepeat} isRowHeader>{t("automaticSync.columns.name")}</SortableColumn>
                  <SortableColumn id="status" icon={IconPlayerPlay}>{t("automaticSync.columns.status")}</SortableColumn>
                  <SortableColumn id="trigger" icon={IconRefresh}>{t("automaticSync.columns.trigger")}</SortableColumn>
                  <SortableColumn id="started" icon={IconClock}>{t("automaticSync.columns.started")}</SortableColumn>
                  <Table.Column><TableColumnLabel icon={IconHistory}>{t("automaticSync.columns.task")}</TableColumnLabel></Table.Column>
                </Table.Header>
                <Table.Body>
                  {sortedRuns.map((run) => (
                    <Table.Row id={run.id} key={run.id}>
                      <Table.Cell><span className="font-semibold">{run.plan_name}</span></Table.Cell>
                      <Table.Cell><Chip color={runTone(run.status)} size="sm" variant="soft">{t(`automaticSync.statuses.${run.status}`)}</Chip></Table.Cell>
                      <Table.Cell>{t(`automaticSync.triggers.${run.trigger}`)}</Table.Cell>
                      <Table.Cell className="text-sm text-muted">{formatDateTime(run.started_at ?? run.created_at, i18n.resolvedLanguage ?? i18n.language)}</Table.Cell>
                      <Table.Cell>{run.task_id ? <Link className="font-semibold text-accent hover:underline" to={`/tasks/${run.task_id}`}>{t("automaticSync.viewTask")}</Link> : "—"}</Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Content>
            </DataTableFrame>
            <div className="grid gap-3 md:grid-cols-2 xl:hidden">
              {sortedRuns.map((run) => (
                <Surface className="grid gap-2 rounded-lg border border-border p-3" key={run.id}>
                  <div className="flex items-start justify-between gap-3">
                    <span className="font-semibold">{run.plan_name}</span>
                    <Chip color={runTone(run.status)} size="sm" variant="soft">{t(`automaticSync.statuses.${run.status}`)}</Chip>
                  </div>
                  <div className="flex items-center justify-between gap-3 text-xs text-muted">
                    <span>{t(`automaticSync.triggers.${run.trigger}`)}</span>
                    <time>{formatDateTime(run.started_at ?? run.created_at, i18n.resolvedLanguage ?? i18n.language)}</time>
                  </div>
                  {run.task_id ? <Link className="text-sm font-semibold text-accent" to={`/tasks/${run.task_id}`}>{t("automaticSync.viewTask")}</Link> : null}
                </Surface>
              ))}
            </div>
          </>
        ) : <EmptyPanel description={t("automaticSync.emptyRunsHint")} title={t("automaticSync.emptyRuns")} />}
      </section>

      <PlanEditor
        creators={creatorsQuery.data ?? []}
        draft={editor}
        editing={Boolean(editingId)}
        mode={cronMode}
        saving={busy === "save"}
        search={search}
        onModeChange={setCronMode}
        onSearchChange={setSearch}
        onChange={setEditor}
        onClose={() => setEditor(null)}
        onSubmit={savePlan}
      />

      <ConfirmModal
        open={Boolean(deleteTarget)}
        title={t("automaticSync.deleteTitle")}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        actions={
          <>
            <Button variant="ghost" onPress={() => setDeleteTarget(null)}><IconX aria-hidden="true" size={18} />{t("common.cancel")}</Button>
            <Button isDisabled={busy !== null} variant="danger" onPress={() => void removePlan()}><IconTrash aria-hidden="true" size={18} />{t("automaticSync.deleteConfirm")}</Button>
          </>
        }
      >
        <p className="text-sm leading-relaxed text-muted">{t("automaticSync.deleteBody")}</p>
        {deleteTarget ? <p className="mt-3 font-semibold text-foreground">{deleteTarget.name}</p> : null}
      </ConfirmModal>
    </div>
  );
}

function PlanEditor({
  creators,
  draft,
  editing,
  mode,
  saving,
  search,
  onModeChange,
  onSearchChange,
  onChange,
  onClose,
  onSubmit,
}: {
  creators: CreatorRosterItem[];
  draft: PlanDraft | null;
  editing: boolean;
  mode: CronMode;
  saving: boolean;
  search: string;
  onModeChange: (mode: CronMode) => void;
  onSearchChange: (value: string) => void;
  onChange: (draft: PlanDraft | null) => void;
  onClose: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  const { t, i18n } = useTranslation();
  if (!draft) return null;
  const safeDraft = draft;
  const normalizedSearch = search.trim().toLocaleLowerCase();
  const visibleCreators = creators.filter((creator) => {
    const value = `${creatorLabel(creator)} ${creator.service} ${creator.creator_id}`.toLocaleLowerCase();
    return !normalizedSearch || value.includes(normalizedSearch);
  });
  const visual = draft.schedule.kind === "cron" ? parseVisualCron(draft.schedule.expression) : null;
  const currentVisual = visual ?? { frequency: "daily" as const, hour: 3, minute: 0, weekdays: [1], monthDay: 1 };
  const allVisibleSelected = visibleCreators.length > 0 && visibleCreators.every((creator) => draft.creators.includes(creatorKey(creator)));
  const selectedDate: DateValue | null = draft.initial_start_date ? parseDate(draft.initial_start_date) : null;
  const timezone = draft.schedule.timezone;
  const cronDetails = draft.schedule.kind === "cron"
    ? describeCron(draft.schedule.expression, timezone, i18n.resolvedLanguage ?? i18n.language)
    : null;
  const timezoneOptions = [...new Set([Intl.DateTimeFormat().resolvedOptions().timeZone, ...timezoneSuggestions])]
    .filter(Boolean)
    .map((value) => ({ value, label: value }));
  const weekdayLabels = Array.from({ length: 7 }, (_, day) => {
    const date = new Date(Date.UTC(2026, 6, 26 + day));
    return new Intl.DateTimeFormat(i18n.resolvedLanguage, { weekday: "short", timeZone: "UTC" }).format(date);
  });

  function patch(patchValue: Partial<PlanDraft>) {
    onChange({ ...safeDraft, ...patchValue });
  }

  function patchSchedule(schedule: PlanDraft["schedule"]) {
    patch({ schedule });
  }

  function setVisual(next: Partial<typeof currentVisual>) {
    if (safeDraft.schedule.kind !== "cron") return;
    const value = { ...currentVisual, ...next };
    patchSchedule({
      ...safeDraft.schedule,
      expression: buildCron(value.frequency, value.hour, value.minute, value.weekdays, value.monthDay),
    });
  }

  return (
    <FormModal
      isWide
      open
      size="lg"
      title={t(editing ? "automaticSync.editPlan" : "automaticSync.newPlan")}
      onOpenChange={(open) => !open && onClose()}
      actions={
        <>
          <Button type="button" variant="ghost" onPress={onClose}><IconX aria-hidden="true" size={18} />{t("common.cancel")}</Button>
          <Button isPending={saving} type="submit" variant="primary" form="automatic-sync-plan-form"><IconCheck aria-hidden="true" size={18} />{t("common.save")}</Button>
        </>
      }
    >
      <form className="grid gap-4" id="automatic-sync-plan-form" onSubmit={onSubmit}>
        <FormSurface className="grid gap-4">
          <SectionHeading description={t("automaticSync.detailsHint")} icon={IconCalendarRepeat} title={t("automaticSync.details")} />
          <div className="grid gap-4 md:grid-cols-2">
            <FormField
              isRequired
              icon={IconCalendarRepeat}
              label={t("automaticSync.name")}
              description={t("automaticSync.nameHint")}
              value={draft.name}
              onChange={(name) => patch({ name })}
            />
            <FormField
              isRequired
              isReadOnly
              icon={IconTags}
              label={t("automaticSync.id")}
              description={t("automaticSync.idHint")}
              value={draft.id}
              onChange={(id) => patch({ id })}
            />
          </div>
          <FormSwitchField
            icon={IconPlayerPlay}
            isSelected={draft.enabled}
            label={t("automaticSync.enabled")}
            description={t("automaticSync.enabledHint")}
            onChange={(enabled) => patch({ enabled })}
          />
          <div className="grid gap-2">
            <div>
              <h4 className="flex items-center gap-2 text-sm font-semibold text-[var(--text-secondary)]"><IconUsers aria-hidden="true" className="text-[var(--accent-strong)]" size={16} />{t("automaticSync.creators")}</h4>
              <p className="mt-1 text-xs text-muted">{t("automaticSync.creatorsHint")}</p>
            </div>
            <SearchField aria-label={t("automaticSync.searchCreators")} value={search} onChange={onSearchChange}>
              <SearchField.Group>
                <SearchField.SearchIcon><IconSearch aria-hidden="true" size={16} /></SearchField.SearchIcon>
                <SearchField.Input placeholder={t("automaticSync.searchCreators")} />
                <SearchField.ClearButton aria-label={t("common.clearSearch")} />
              </SearchField.Group>
            </SearchField>
            <div className="flex items-center justify-between gap-3">
              <SelectionCheckbox
                showLabel
                isIndeterminate={!allVisibleSelected && visibleCreators.some((creator) => draft.creators.includes(creatorKey(creator)))}
                isSelected={allVisibleSelected}
                label={t("automaticSync.selectAll")}
                onChange={(selected) => {
                  const visibleKeys = new Set(visibleCreators.map(creatorKey));
                  patch({
                    creators: selected
                      ? [...new Set([...draft.creators, ...visibleKeys])]
                      : draft.creators.filter((key) => !visibleKeys.has(key)),
                  });
                }}
              />
              <Chip color="accent" size="sm" variant="soft">{t("automaticSync.selected", { count: draft.creators.length })}</Chip>
            </div>
            <div className="max-h-56 overflow-y-auto rounded-lg border border-border bg-surface [scrollbar-gutter:stable]">
              {visibleCreators.length ? visibleCreators.map((creator) => {
                const key = creatorKey(creator);
                return (
                  <div className="flex min-h-12 items-center gap-3 border-b border-border px-3 last:border-b-0" key={key}>
                    <SelectionCheckbox
                      isSelected={draft.creators.includes(key)}
                      label={creatorLabel(creator)}
                      onChange={(selected) => patch({
                        creators: selected ? [...draft.creators, key] : draft.creators.filter((value) => value !== key),
                      })}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold">{creatorLabel(creator)}</p>
                      <p className="truncate text-xs text-muted">{creator.service}:{creator.creator_id}</p>
                    </div>
                  </div>
                );
              }) : <p className="p-4 text-sm text-muted">{t("automaticSync.noCreators")}</p>}
            </div>
          </div>
        </FormSurface>

        <FormSurface className="grid gap-4">
          <SectionHeading description={t("automaticSync.scheduleHint")} icon={IconCalendarClock} title={t("automaticSync.scheduleSection")} />
          <SelectField
            icon={IconCalendarClock}
            label={t("automaticSync.kind")}
            value={draft.schedule.kind}
            options={[
              { value: "cron", label: t("automaticSync.cron"), icon: IconCalendarClock },
              { value: "interval", label: t("automaticSync.interval"), icon: IconRefresh },
            ]}
            onChange={(kind) => {
              if (kind === draft.schedule.kind) return;
              patchSchedule(kind === "cron"
                ? { kind: "cron", expression: "0 3 * * *", timezone }
                : { kind: "interval", every: 24, unit: "hours", anchor_at: null, timezone });
            }}
          />
          <ComboBoxField
            icon={IconClock}
            label={t("automaticSync.timezone")}
            description={t("automaticSync.timezoneHint")}
            options={timezoneOptions}
            value={timezone}
            onChange={(next) => patchSchedule({ ...draft.schedule, timezone: next })}
          />
          {draft.schedule.kind === "cron" ? (
            <Tabs selectedKey={mode} onSelectionChange={(key) => onModeChange(String(key) as CronMode)}>
              <Tabs.List>
                <Tabs.Tab id="visual">{t("automaticSync.visual")}</Tabs.Tab>
                <Tabs.Tab id="advanced">{t("automaticSync.advanced")}</Tabs.Tab>
              </Tabs.List>
              <Tabs.Panel id="visual">
                {!visual && mode === "visual" ? (
                  <Alert status="warning"><Alert.Indicator><IconAlertTriangle size={18} /></Alert.Indicator><Alert.Content>{t("automaticSync.validation.cron")}</Alert.Content></Alert>
                ) : null}
                <div className="mt-4 grid gap-4">
                  <SelectField
                    label={t("automaticSync.frequency")}
                    value={currentVisual.frequency}
                    options={(["hourly", "daily", "weekly", "monthly"] as const).map((value) => ({ value, label: t(`automaticSync.frequencies.${value}`) }))}
                    onChange={(frequency) => setVisual({ frequency: frequency as Frequency })}
                  />
                  <div className="grid grid-cols-2 gap-3">
                    {currentVisual.frequency === "hourly" ? null : (
                      <SelectField label={t("automaticSync.hour")} value={String(currentVisual.hour)} options={numberOptions(24)} onChange={(value) => setVisual({ hour: Number(value) })} />
                    )}
                    <SelectField label={t("automaticSync.minute")} value={String(currentVisual.minute)} options={numberOptions(60)} onChange={(value) => setVisual({ minute: Number(value) })} />
                  </div>
                  {currentVisual.frequency === "weekly" ? (
                    <div className="grid gap-2">
                      <p className="text-sm font-semibold">{t("automaticSync.weekdays")}</p>
                      <div className="grid grid-cols-4 gap-2 sm:grid-cols-7">
                        {weekdayLabels.map((label, value) => (
                          <SelectionCheckbox
                            showLabel
                            isSelected={currentVisual.weekdays.includes(value)}
                            key={value}
                            label={label}
                            onChange={(selected) => {
                              const weekdays = selected
                                ? [...new Set([...currentVisual.weekdays, value])].sort()
                                : currentVisual.weekdays.filter((day) => day !== value);
                              if (weekdays.length) setVisual({ weekdays });
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  ) : null}
                  {currentVisual.frequency === "monthly" ? (
                    <NumberInput label={t("automaticSync.monthDay")} minValue={1} maxValue={31} value={currentVisual.monthDay} onChange={(monthDay) => setVisual({ monthDay })} />
                  ) : null}
                </div>
              </Tabs.Panel>
              <Tabs.Panel id="advanced">
                <div className="mt-4">
                  <FormField
                    icon={IconCalendarClock}
                    label={t("automaticSync.expression")}
                    description={t("automaticSync.expressionHint")}
                    inputClassName="font-mono"
                    value={draft.schedule.expression}
                    onChange={(expression) => patchSchedule({
                      kind: "cron",
                      expression,
                      timezone: draft.schedule.timezone,
                    })}
                  />
                </div>
              </Tabs.Panel>
            </Tabs>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <NumberInput
                label={t("automaticSync.intervalEvery")}
                minValue={1}
                value={draft.schedule.every}
                onChange={(every) => patchSchedule({
                  kind: "interval",
                  every,
                  unit: draft.schedule.kind === "interval" ? draft.schedule.unit : "hours",
                  anchor_at: draft.schedule.kind === "interval" ? draft.schedule.anchor_at : null,
                  timezone: draft.schedule.timezone,
                })}
              />
              <SelectField
                label={t("automaticSync.unit")}
                value={draft.schedule.unit}
                options={(["minutes", "hours", "days"] as const).map((value) => ({ value, label: t(`automaticSync.units.${value}`) }))}
                onChange={(unit) => patchSchedule({
                  kind: "interval",
                  every: draft.schedule.kind === "interval" ? draft.schedule.every : 24,
                  unit: unit as "minutes" | "hours" | "days",
                  anchor_at: draft.schedule.kind === "interval" ? draft.schedule.anchor_at : null,
                  timezone: draft.schedule.timezone,
                })}
              />
            </div>
          )}
          {cronDetails ? (
            <div aria-live="polite" className="grid gap-2 border-t border-border pt-4">
              <p className="text-xs font-semibold uppercase text-muted">{t("automaticSync.schedulePreview")}</p>
              <p className="text-sm leading-relaxed text-foreground">
                {cronDetails.description}
                <span className="text-muted"> · </span>
                <code className="text-xs text-muted">{timezone}</code>
              </p>
              <p className="text-xs font-semibold text-muted">{t("automaticSync.nextRuns")}</p>
              <ol className="grid gap-1 text-sm text-muted sm:grid-cols-3">
                {cronDetails.next.map((value) => (
                  <li className="rounded-md bg-[var(--surface-tertiary)] px-3 py-2" key={value.toISOString()}>
                    {formatDateTime(value.toISOString(), i18n.resolvedLanguage ?? i18n.language)}
                  </li>
                ))}
              </ol>
            </div>
          ) : null}
        </FormSurface>

        <FormSurface className="grid gap-4">
          <SectionHeading description={t("automaticSync.firstRunHint")} icon={IconHistory} title={t("automaticSync.firstRun")} />
          <FormSwitchField
            icon={IconHistory}
            isSelected={draft.initial_start_date === null}
            label={t("automaticSync.unlimited")}
            description={t("automaticSync.unlimitedHint")}
            onChange={(unlimited) => patch({ initial_start_date: unlimited ? null : today(getLocalTimeZone()).toString() })}
          />
          <DatePickerInput
            icon={IconCalendarClock}
            isDisabled={draft.initial_start_date === null}
            label={t("automaticSync.initialDate")}
            value={selectedDate}
            onChange={(value) => patch({ initial_start_date: value?.toString() ?? null })}
          />
        </FormSurface>

        <FormSurface className="grid gap-4">
          <SectionHeading description={t("automaticSync.optionsHint")} icon={IconRefresh} title={t("automaticSync.options")} />
          <RemotePathField
            description={t("automaticSync.outputHint")}
            icon={IconFolder}
            label={t("automaticSync.output")}
            selector={TASK_OUTPUT_PATH_SELECTOR}
            value={draft.options.output}
            onChange={(output) => patch({ options: { ...draft.options, output } })}
          />
          <div className="grid gap-3 md:grid-cols-2">
            <FormSwitchField icon={IconHistory} isSelected={draft.options.save_creator_indices} label={t("automaticSync.saveIndex")} description={t("automaticSync.saveIndexHint")} onChange={(save_creator_indices) => patch({ options: { ...draft.options, save_creator_indices } })} />
            <SelectField
              icon={IconFolder}
              label={t("automaticSync.mixWorks")}
              value={draft.options.mix_posts === null ? "project" : draft.options.mix_posts ? "enabled" : "disabled"}
              options={(["project", "enabled", "disabled"] as const).map((value) => ({ value, label: t(`automaticSync.mix.${value}`) }))}
              onChange={(value) => patch({ options: { ...draft.options, mix_posts: value === "project" ? null : value === "enabled" } })}
            />
          </div>
          <ChipListField icon={IconTags} label={t("automaticSync.includeKeywords")} values={draft.options.keywords} onChange={(keywords) => patch({ options: { ...draft.options, keywords } })} />
          <ChipListField icon={IconTags} label={t("automaticSync.excludeKeywords")} values={draft.options.keywords_exclude} onChange={(keywords_exclude) => patch({ options: { ...draft.options, keywords_exclude } })} />
        </FormSurface>
      </form>
    </FormModal>
  );
}

function SectionHeading({ title, description, icon: Icon }: { title: string; description: string; icon: typeof IconCalendarRepeat }) {
  return (
    <div className="flex items-start gap-3 border-b border-border pb-3">
      <span className="page-title-icon grid size-9 shrink-0 place-items-center rounded-lg"><Icon aria-hidden="true" size={18} /></span>
      <div>
        <h3 className="font-semibold text-foreground">{title}</h3>
        <p className="mt-1 text-xs leading-relaxed text-muted">{description}</p>
      </div>
    </div>
  );
}

function scheduleText(plan: AutomaticSyncPlan): string {
  if (plan.schedule?.kind === "interval") return `${plan.schedule.every} ${plan.schedule.unit} · ${plan.schedule.timezone}`;
  return `${plan.schedule?.expression ?? "0 3 * * *"} · ${plan.schedule?.timezone ?? "UTC"}`;
}

function numberOptions(length: number) {
  return Array.from({ length }, (_, value) => ({ value: String(value), label: String(value).padStart(2, "0") }));
}

function validateDraft(draft: PlanDraft): string | null {
  if (!draft.name.trim()) return "automaticSync.validation.name";
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/u.test(draft.id)) return "automaticSync.validation.id";
  if (!draft.creators.length) return "automaticSync.validation.creators";
  if (draft.schedule.kind === "cron" && draft.schedule.expression.trim().split(/\s+/u).length !== 5) return "automaticSync.validation.cron";
  if (draft.schedule.kind === "interval" && intervalMinutes(draft) < 15) return "automaticSync.validation.interval";
  return null;
}

function describeCron(expression: string, timezone: string, language: string) {
  try {
    const interval = CronExpressionParser.parse(expression, {
      currentDate: new Date(),
      tz: timezone,
    });
    const next = Array.from({ length: 3 }, () => interval.next().toDate());
    return {
      description: cronstrue.toString(expression, {
        locale: cronLocale(language),
        use24HourTimeFormat: true,
      }),
      next,
    };
  } catch {
    return null;
  }
}

function cronLocale(language: string): string {
  if (language.startsWith("zh-Hant")) return "zh_TW";
  if (language.startsWith("zh")) return "zh_CN";
  if (language.startsWith("ja")) return "ja";
  if (language.startsWith("ko")) return "ko";
  if (language.startsWith("fr")) return "fr";
  if (language.startsWith("ru")) return "ru";
  return "en";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
