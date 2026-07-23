import {
  Button,
  Chip,
  Surface,
  Table,
  toast,
} from "@heroui/react";
import type { SortDescriptor } from "@heroui/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  IconArrowDown as ArrowDown,
  IconArrowLeft as ArrowLeft,
  IconArrowUp as ArrowUp,
  IconActivity as Activity,
  IconAlertTriangle as AlertTriangle,
  IconCircleCheck as CircleCheck,
  IconClock as Clock,
  IconEye as Eye,
  IconFilter as Filter,
  IconPencil as Pencil,
  IconPlayerPause as Pause,
  IconPlayerPlay as Play,
  IconPlayerStop as Square,
  IconPlugConnectedX as Interrupted,
  IconPlus as Plus,
  IconRefresh as Refresh,
  IconTrash as Trash2,
  IconX as X,
} from "@tabler/icons-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import { TaskEditor } from "../components/TaskEditor";
import { TaskTarget } from "../components/TaskTarget";
import {
  ConfirmModal,
  DataTableFrame,
  EmptyPanel,
  FormCheckbox,
  FormSurface,
  IconButton,
  MobileSortControls,
  PageHeader,
  PageLoading,
  ProgressMeter,
  SelectField,
  SortableColumn,
  TaskStatusChip,
} from "../components/ui";
import { api, errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import { formatBytes, formatDateTime, formatDuration, taskPercent } from "../lib/format";
import {
  eventLabel,
  eventMessage,
  failureAdvice,
  failureMessage,
  failureSummary,
  failureStageLabel,
  failureSubject,
  taskFailureItems,
} from "../lib/taskFailures";
import {
  normalizeTableSort,
  stableSort,
  taskStatusRank,
  taskTargetSortText,
} from "../lib/sorting";
import type {
  CreatorRosterItem,
  FailureItem,
  TaskFailureReport,
  TaskAttempt,
  TaskCleanupPreview,
  TaskEvent,
  TaskRecord,
  TaskSpec,
  TaskStatus,
} from "../types";

const pausable = new Set<TaskStatus>(["queued", "blocked", "running"]);
const stoppable = new Set<TaskStatus>(["queued", "blocked", "running", "paused"]);
const resumable = new Set<TaskStatus>(["paused", "stopped", "completed", "failed", "interrupted"]);
const editable = new Set<TaskStatus>(["queued", "blocked", "paused", "stopped", "completed", "failed", "interrupted"]);
const deletable = new Set<TaskStatus>(["paused", "stopped", "completed", "failed", "interrupted"]);
const speedVisible = new Set<TaskStatus>(["running", "pause_requested", "stop_requested"]);
const descendingTaskColumns = new Set(["progress", "speed", "created"]);

type TaskStatusFilter =
  | "all"
  | "active"
  | "waiting"
  | "paused"
  | "completed"
  | "failed"
  | "stopped"
  | "interrupted";

export function TasksPage() {
  const { t } = useTranslation();
  const { taskId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const tasksQuery = useQuery({ queryKey: ["tasks"], queryFn: () => api<TaskRecord[]>("/tasks") });
  const creatorsQuery = useQuery({ queryKey: ["creators"], queryFn: () => api<CreatorRosterItem[]>("/creators") });
  const [editor, setEditor] = useState<TaskRecord | "new" | null>(() =>
    searchParams.get("create") === "sync" ? "new" : null,
  );
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState<TaskRecord | null>(null);
  const [deleteOutput, setDeleteOutput] = useState(false);
  const statusFilter = taskStatusFilter(searchParams.get("status"));
  useEffect(() => {
    if (searchParams.get("create") !== "sync") return;
    const next = new URLSearchParams(searchParams);
    next.delete("create");
    setSearchParams(next, { replace: true });
  }, [searchParams, setSearchParams]);

  const cleanupQuery = useQuery({
    queryKey: ["task-cleanup", removing?.id],
    queryFn: () => api<TaskCleanupPreview>(`/tasks/${removing?.id}/cleanup-preview`),
    enabled: Boolean(removing),
  });
  const eventsQuery = useQuery({
    queryKey: ["task-events", taskId],
    queryFn: () => api<TaskEvent[]>(`/tasks/${taskId}/events?limit=200`),
    enabled: Boolean(taskId),
  });
  const attemptsQuery = useQuery({
    queryKey: ["task-attempts", taskId],
    queryFn: () => api<TaskAttempt[]>(`/tasks/${taskId}/attempts`),
    enabled: Boolean(taskId),
  });

  if (tasksQuery.isLoading || creatorsQuery.isLoading) return <PageLoading />;
  const tasks = tasksQuery.data ?? [];
  const selected = taskId ? tasks.find((task) => task.id === taskId) : undefined;

  async function saveTask(spec: TaskSpec) {
    if (!session || !editor) return;
    setSaving(true);
    try {
      const task = editor === "new"
        ? await api<TaskRecord>("/tasks", { method: "POST", body: { spec }, csrfToken: session.csrf_token })
        : await api<TaskRecord>(`/tasks/${editor.id}`, {
            method: "PATCH",
            body: { spec },
            csrfToken: session.csrf_token,
          });
      setEditor(null);
      await queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success(editor === "new" ? t("tasks.created") : t("tasks.updated"));
      navigate(`/tasks/${task.id}`);
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    } finally {
      setSaving(false);
    }
  }

  async function taskAction(task: TaskRecord, action: "pause" | "resume" | "stop") {
    if (!session) return;
    try {
      await api<TaskRecord>(`/tasks/${task.id}/${action}`, {
        method: "POST",
        csrfToken: session.csrf_token,
      });
      await queryClient.invalidateQueries({ queryKey: ["tasks"] });
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    }
  }

  async function reorder(task: TaskRecord, position: number) {
    if (!session) return;
    try {
      await api<TaskRecord>(`/tasks/${task.id}/reorder`, {
        method: "POST",
        body: { position },
        csrfToken: session.csrf_token,
      });
      await queryClient.invalidateQueries({ queryKey: ["tasks"] });
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    }
  }

  async function deleteTask() {
    if (!session || !removing) return;
    const parameters = new URLSearchParams({ delete_output: String(deleteOutput) });
    if (deleteOutput) parameters.set("confirmation", removing.id);
    try {
      await api<TaskCleanupPreview>(`/tasks/${removing.id}?${parameters.toString()}`, {
        method: "DELETE",
        csrfToken: session.csrf_token,
      });
      if (taskId === removing.id) navigate("/tasks");
      setRemoving(null);
      setDeleteOutput(false);
      await queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success(t("tasks.deleted"));
    } catch (error) {
      toast.danger(t("common.error"), { description: errorText(error) });
    }
  }

  const handlers: TaskHandlers = {
    details: (task) => navigate(`/tasks/${task.id}`),
    edit: setEditor,
    remove: (task) => {
      setDeleteOutput(false);
      setRemoving(task);
    },
    pause: (task) => void taskAction(task, "pause"),
    resume: (task) => void taskAction(task, "resume"),
    stop: (task) => void taskAction(task, "stop"),
    reorder: (task, position) => void reorder(task, position),
  };

  function changeStatusFilter(value: string) {
    const next = new URLSearchParams(searchParams);
    if (value === "all") next.delete("status");
    else next.set("status", value);
    setSearchParams(next, { replace: true });
  }

  return (
    <div className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-6">
      {taskId && selected ? (
        <TaskDetails
          attempts={attemptsQuery.data ?? []}
          creators={creatorsQuery.data ?? []}
          events={eventsQuery.data ?? []}
          task={selected}
          handlers={handlers}
          onBack={() => navigate("/tasks")}
        />
      ) : (
        <TaskList
          creators={creatorsQuery.data ?? []}
          handlers={handlers}
          statusFilter={statusFilter}
          tasks={tasks}
          onCreate={() => setEditor("new")}
          onStatusFilterChange={changeStatusFilter}
        />
      )}

      {editor ? (
        <TaskEditor
          creators={creatorsQuery.data ?? []}
          key={editor === "new" ? "new" : `${editor.id}-${editor.revision}`}
          saving={saving}
          task={editor === "new" ? undefined : editor}
          onClose={() => setEditor(null)}
          onSave={saveTask}
        />
      ) : null}

      <ConfirmModal
        actions={
          <>
            <Button variant="ghost" onPress={() => setRemoving(null)}><X aria-hidden="true" size={17} />{t("common.cancel")}</Button>
            <Button variant="danger" onPress={() => void deleteTask()}>
              <Trash2 aria-hidden="true" size={17} />
              {t("common.delete")}
            </Button>
          </>
        }
        open={removing !== null}
        title={t("tasks.cleanupTitle")}
        onOpenChange={(open) => !open && setRemoving(null)}
      >
        <div className="grid gap-4">
          <p className="text-sm leading-relaxed text-muted">{t("tasks.cleanupBody")}</p>
          {cleanupQuery.isLoading ? <PageLoading /> : (
            <Surface className="grid gap-2 rounded-lg border border-border p-4">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm text-muted">{t("tasks.removable")}</span>
                <strong>{cleanupQuery.data?.removable_files ?? 0}</strong>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm text-muted">{t("tasks.outputSize")}</span>
                <strong>{formatBytes(cleanupQuery.data?.removable_bytes)}</strong>
              </div>
            </Surface>
          )}
          <FormCheckbox isSelected={deleteOutput} label={t("tasks.deleteOutput")} onChange={setDeleteOutput} />
          {deleteOutput ? <p className="break-all text-xs text-danger">{t("tasks.deleteConfirmation", { id: removing?.id })}</p> : null}
        </div>
      </ConfirmModal>
    </div>
  );
}

type TaskHandlers = {
  details: (task: TaskRecord) => void;
  edit: (task: TaskRecord) => void;
  remove: (task: TaskRecord) => void;
  pause: (task: TaskRecord) => void;
  resume: (task: TaskRecord) => void;
  stop: (task: TaskRecord) => void;
  reorder: (task: TaskRecord, position: number) => void;
};

function TaskList({
  tasks,
  creators,
  handlers,
  statusFilter,
  onCreate,
  onStatusFilterChange,
}: {
  tasks: TaskRecord[];
  creators: CreatorRosterItem[];
  handlers: TaskHandlers;
  statusFilter: TaskStatusFilter;
  onCreate: () => void;
  onStatusFilterChange: (value: string) => void;
}) {
  const { t, i18n } = useTranslation();
  const [sortDescriptor, setSortDescriptor] = useState<SortDescriptor | null>(null);
  const filteredTasks = useMemo(
    () => tasks.filter((task) => matchesTaskStatus(task.status, statusFilter)),
    [statusFilter, tasks],
  );
  const visibleTasks = useMemo(() => {
    if (!sortDescriptor) return [...filteredTasks].sort((left, right) => left.position - right.position);
    return stableSort(
      filteredTasks,
      sortDescriptor,
      (task, column) => {
        if (column === "target") return taskTargetSortText(task, creators);
        if (column === "status") return taskStatusRank(task.status);
        if (column === "progress") {
          return taskPercent(
            task.progress.processed_files,
            task.progress.queued_files,
            task.progress.transferred_bytes,
            task.progress.total_bytes,
          );
        }
        if (column === "speed") return taskSpeed(task);
        if (column === "output") return task.spec.output;
        return Date.parse(task.created_at);
      },
      i18n.resolvedLanguage ?? i18n.language,
    );
  }, [creators, filteredTasks, i18n.language, i18n.resolvedLanguage, sortDescriptor]);
  const reorderLocked = statusFilter !== "all" || sortDescriptor !== null;
  const statusOptions = [
    { value: "all", label: t("tasks.allStatuses"), icon: Filter },
    { value: "active", label: t("tasks.activeStatuses"), icon: Activity, tone: "accent" as const },
    { value: "waiting", label: t("tasks.waitingStatuses"), icon: Clock, tone: "warning" as const },
    { value: "paused", label: t("tasks.statuses.paused"), icon: Pause, tone: "warning" as const },
    { value: "completed", label: t("tasks.statuses.completed"), icon: CircleCheck, tone: "success" as const },
    { value: "failed", label: t("tasks.statuses.failed"), icon: AlertTriangle, tone: "danger" as const },
    { value: "stopped", label: t("tasks.statuses.stopped"), icon: Square },
    { value: "interrupted", label: t("tasks.statuses.interrupted"), icon: Interrupted, tone: "danger" as const },
  ];
  const sortOptions = [
    { value: "queue", label: t("tasks.queueOrder") },
    { value: "target", label: t("tasks.target") },
    { value: "status", label: t("common.status") },
    { value: "progress", label: t("tasks.progress") },
    { value: "speed", label: t("tasks.totalSpeed") },
    { value: "output", label: t("tasks.output") },
    { value: "created", label: t("common.created") },
  ];
  return (
    <>
      <PageHeader
        description={t("tasks.description")}
        title={t("tasks.title")}
        actions={<Button variant="primary" onPress={onCreate}><Plus aria-hidden="true" size={18} />{t("tasks.create")}</Button>}
      />
      <FormSurface className="grid gap-3 p-3 xl:grid-cols-[minmax(0,16rem)_minmax(0,1fr)]">
        <SelectField
          icon={Filter}
          label={t("tasks.statusFilter")}
          options={statusOptions}
          value={statusFilter}
          onChange={onStatusFilterChange}
        />
        <MobileSortControls
          className="xl:hidden"
          defaultValue="queue"
          descendingByDefault={descendingTaskColumns}
          descriptor={sortDescriptor}
          options={sortOptions}
          onChange={setSortDescriptor}
        />
      </FormSurface>
      {reorderLocked ? (
        <Chip color="warning" size="sm" variant="soft">
          {sortDescriptor ? t("tasks.sortedView") : t("tasks.filteredView")}
        </Chip>
      ) : null}
      {!visibleTasks.length ? <EmptyPanel title={t("tasks.empty")} /> : (
        <>
          <DataTableFrame className="hidden xl:block">
            <Table.Content
              aria-label={t("tasks.title")}
              className="task-table-content min-w-[940px]"
              sortDescriptor={sortDescriptor ?? undefined}
              onSortChange={(next) => setSortDescriptor(
                normalizeTableSort(sortDescriptor, next, descendingTaskColumns),
              )}
            >
              <Table.Header>
                <SortableColumn id="target" isRowHeader>{t("tasks.target")}</SortableColumn>
                <SortableColumn id="status">{t("common.status")}</SortableColumn>
                <SortableColumn id="progress">{t("tasks.progress")}</SortableColumn>
                <SortableColumn id="speed">{t("tasks.totalSpeed")}</SortableColumn>
                <SortableColumn id="output">{t("tasks.output")}</SortableColumn>
                <SortableColumn id="created">{t("common.created")}</SortableColumn>
                <Table.Column>{t("common.actions")}</Table.Column>
              </Table.Header>
              <Table.Body>
                {visibleTasks.map((task, index) => (
                  <Table.Row className="task-table-row" id={task.id} key={task.id}>
                    <Table.Cell className="w-56 min-w-56 max-w-56"><TaskTarget creators={creators} task={task} /></Table.Cell>
                    <Table.Cell className="min-w-24"><TaskStatusChip status={task.status} /></Table.Cell>
                    <Table.Cell className="min-w-28"><TaskProgressSummary task={task} /></Table.Cell>
                    <Table.Cell className="min-w-20 whitespace-nowrap text-sm font-medium tabular-nums">{formatBytes(taskSpeed(task), "/s")}</Table.Cell>
                    <Table.Cell><code className="block max-w-28 truncate text-xs text-muted" title={task.spec.output}>{task.spec.output}</code></Table.Cell>
                    <Table.Cell className="w-24 max-w-24 text-xs leading-relaxed text-muted"><TaskCreatedTime locale={i18n.language} value={task.created_at} /></Table.Cell>
                    <Table.Cell className="w-[196px] min-w-[196px]"><TaskActions canMoveDown={index < visibleTasks.length - 1} canMoveUp={index > 0} reorderLocked={reorderLocked} task={task} handlers={handlers} /></Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Content>
          </DataTableFrame>
          <div className="grid gap-3 xl:hidden">
            {visibleTasks.map((task, index) => (
              <Surface className="data-mobile-card task-mobile-card grid gap-4 rounded-lg border border-border p-4" key={task.id}>
                <div className="flex min-w-0 items-start gap-3">
                  <div className="min-w-0 flex-1"><TaskTarget creators={creators} task={task} /></div>
                  <div className="ml-auto shrink-0"><TaskStatusChip status={task.status} /></div>
                </div>
                <div className="grid grid-cols-[minmax(0,1fr)_auto] items-end gap-4">
                  <TaskProgressSummary task={task} />
                  <div className="text-right">
                    <p className="text-xs text-muted">{t("tasks.totalSpeed")}</p>
                    <strong className="text-sm tabular-nums text-foreground">{formatBytes(taskSpeed(task), "/s")}</strong>
                  </div>
                </div>
                <div className="grid gap-1 border-t border-border pt-3 text-xs text-muted">
                  <code className="truncate" title={task.spec.output}>{task.spec.output}</code>
                  <span>{formatDateTime(task.created_at, i18n.language)}</span>
                </div>
                <TaskActions mobile canMoveDown={index < visibleTasks.length - 1} canMoveUp={index > 0} reorderLocked={reorderLocked} task={task} handlers={handlers} />
              </Surface>
            ))}
          </div>
        </>
      )}
    </>
  );
}

function TaskProgressSummary({ task }: { task: TaskRecord }) {
  const percent = taskPercent(
    task.progress.processed_files,
    task.progress.queued_files,
    task.progress.transferred_bytes,
    task.progress.total_bytes,
  );
  return (
    <div className="grid gap-1.5">
      <div className="h-1.5 overflow-hidden rounded-full bg-default">
        <div className="h-full bg-accent transition-[width]" style={{ width: `${Math.min(100, percent)}%` }} />
      </div>
      <span className="text-xs tabular-nums text-muted">{task.progress.processed_files}/{task.progress.queued_files}</span>
    </div>
  );
}

function TaskCreatedTime({ value, locale }: { value: string; locale: string }) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return <time>{value}</time>;
  const day = new Intl.DateTimeFormat(locale, { year: "numeric", month: "2-digit", day: "2-digit" }).format(date);
  const time = new Intl.DateTimeFormat(locale, { hour: "2-digit", minute: "2-digit" }).format(date);
  return (
    <time className="grid whitespace-nowrap" dateTime={value} title={formatDateTime(value, locale)}>
      <span>{day}</span>
      <span>{time}</span>
    </time>
  );
}

function TaskActions({
  task,
  handlers,
  canMoveUp,
  canMoveDown,
  reorderLocked,
  mobile = false,
}: {
  task: TaskRecord;
  handlers: TaskHandlers;
  canMoveUp: boolean;
  canMoveDown: boolean;
  reorderLocked: boolean;
  mobile?: boolean;
}) {
  const { t } = useTranslation();
  const canPause = pausable.has(task.status);
  const canResume = resumable.has(task.status);
  const canStop = stoppable.has(task.status);
  const canEdit = editable.has(task.status);
  const canDelete = deletable.has(task.status);
  const status = t(`tasks.statuses.${task.status}`);
  const unavailable = (action: string) => t("tasks.actionUnavailable", { action, status });
  const lifecycleAction = canResume ? t("tasks.resume") : t("tasks.pause");
  return (
    <div className={mobile ? "task-action-grid grid grid-cols-4 justify-items-center gap-1 border-t border-border pt-3" : "task-action-grid grid w-[188px] grid-cols-4 justify-items-center gap-1"}>
      <IconButton icon={Eye} label={t("tasks.details")} onPress={() => handlers.details(task)} />
      <IconButton
        icon={canResume ? Play : Pause}
        isDisabled={!canPause && !canResume}
        label={lifecycleAction}
        tooltip={canPause || canResume ? lifecycleAction : unavailable(lifecycleAction)}
        onPress={() => canResume ? handlers.resume(task) : handlers.pause(task)}
      />
      <IconButton icon={Square} isDisabled={!canStop} label={t("tasks.stop")} tooltip={canStop ? t("tasks.stop") : unavailable(t("tasks.stop"))} onPress={() => handlers.stop(task)} />
      <IconButton icon={Pencil} isDisabled={!canEdit} label={t("common.edit")} tooltip={canEdit ? t("common.edit") : unavailable(t("common.edit"))} onPress={() => handlers.edit(task)} />
      <IconButton icon={ArrowUp} isDisabled={reorderLocked || !canMoveUp} label={t("tasks.moveUp")} tooltip={reorderLocked ? t("tasks.filteredView") : canMoveUp ? t("tasks.moveUp") : t("tasks.firstInQueue")} onPress={() => handlers.reorder(task, Math.max(1, task.position - 1))} />
      <IconButton icon={ArrowDown} isDisabled={reorderLocked || !canMoveDown} label={t("tasks.moveDown")} tooltip={reorderLocked ? t("tasks.filteredView") : canMoveDown ? t("tasks.moveDown") : t("tasks.lastInQueue")} onPress={() => handlers.reorder(task, task.position + 1)} />
      <IconButton className="text-danger" icon={Trash2} isDisabled={!canDelete} label={t("common.delete")} tooltip={canDelete ? t("common.delete") : unavailable(t("common.delete"))} onPress={() => handlers.remove(task)} />
    </div>
  );
}

function TaskDetails({
  task,
  creators,
  events,
  attempts,
  handlers,
  onBack,
}: {
  task: TaskRecord;
  creators: CreatorRosterItem[];
  events: TaskEvent[];
  attempts: TaskAttempt[];
  handlers: TaskHandlers;
  onBack: () => void;
}) {
  const { t, i18n } = useTranslation();
  const progress = task.progress;
  const percent = taskPercent(progress.processed_files, progress.queued_files, progress.transferred_bytes, progress.total_bytes);
  const waitingRetries = Object.entries(progress.waiting_retries ?? {});
  return (
    <>
      <PageHeader
        description={`${t(`common.${task.kind}`)} · ${task.id}`}
        showDescription
        title={t("tasks.details")}
        actions={
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onPress={onBack}><ArrowLeft aria-hidden="true" size={17} />{t("common.back")}</Button>
            {pausable.has(task.status) ? <Button variant="outline" onPress={() => handlers.pause(task)}><Pause aria-hidden="true" size={17} />{t("tasks.pause")}</Button> : null}
            {resumable.has(task.status) ? <Button variant="primary" onPress={() => handlers.resume(task)}><Play aria-hidden="true" size={17} />{t("tasks.resume")}</Button> : null}
            {stoppable.has(task.status) ? <Button variant="danger" onPress={() => handlers.stop(task)}><Square aria-hidden="true" size={17} />{t("tasks.stop")}</Button> : null}
          </div>
        }
      />
      <Surface className="flex flex-col justify-between gap-4 rounded-lg border border-border p-4 sm:flex-row sm:items-center">
        <TaskTarget creators={creators} task={task} />
        <div className="flex shrink-0 flex-wrap items-center gap-2"><TaskStatusChip status={task.status} /><Chip size="sm" variant="soft">{t("tasks.attempts", { count: attempts.length })}</Chip></div>
      </Surface>
      <TaskFailurePanel
        fallback={task.error}
        report={task.failure ?? attempts[attempts.length - 1]?.failure}
      />
      <Surface className="grid gap-5 rounded-lg border border-border p-5">
        <ProgressMeter isIndeterminate={task.status === "running" && !progress.total_bytes && !progress.queued_files} label={t("tasks.progress")} value={percent} />
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label={t("tasks.totalSpeed")} value={formatBytes(taskSpeed(task), "/s")} />
          <Metric label={t("tasks.transferred")} value={`${formatBytes(progress.transferred_bytes)} / ${formatBytes(progress.total_bytes)}`} />
          <Metric label={t("tasks.files")} value={`${progress.processed_files} / ${progress.queued_files}`} />
          <Metric label={t("tasks.eta")} value={formatDuration(progress.eta_seconds)} />
        </div>
      </Surface>
      <div className="grid items-stretch gap-5 lg:grid-cols-3">
        <Surface className="grid content-start gap-4 rounded-lg border border-border p-5">
          <div className="flex items-center justify-between gap-3"><h2 className="font-semibold">{t("tasks.activeCreators")}</h2><Chip size="sm" variant="soft">{progress.active_creators.length}</Chip></div>
          {progress.active_creators.length ? <div className="flex flex-wrap gap-2">{progress.active_creators.map((creator) => <Chip color="accent" key={creator} size="sm" variant="soft">{creator}</Chip>)}</div> : <p className="text-sm text-muted">{t("common.none")}</p>}
        </Surface>
        <Surface className="grid content-start gap-4 rounded-lg border border-border p-5">
          <div className="flex items-center justify-between gap-3"><h2 className="font-semibold">{t("tasks.activeDownloads")}</h2><Chip size="sm" variant="soft">{Object.keys(progress.active_downloads).length}</Chip></div>
          {Object.entries(progress.active_downloads).map(([key, download]) => (
            <div className="grid gap-1 border-b border-border pb-3 last:border-0 last:pb-0" key={key}>
              <p className="truncate text-sm font-medium" title={download.filename}>{download.filename}</p>
              <div className="flex justify-between gap-3 text-xs text-muted"><span>{download.creator_key}</span><span>{formatBytes(download.speed_bps, "/s")}</span></div>
            </div>
          ))}
          {!Object.keys(progress.active_downloads).length ? <p className="text-sm text-muted">{t("common.none")}</p> : null}
        </Surface>
        <Surface className="grid min-h-0 content-start gap-4 rounded-lg border border-border p-5">
          <div className="flex items-center justify-between gap-3">
            <h2 className="flex min-w-0 items-center gap-2 font-semibold">
              <Refresh aria-hidden="true" className="shrink-0 text-warning" size={18} />
              <span className="truncate">{t("tasks.waitingRetries")}</span>
            </h2>
            <Chip color={waitingRetries.length ? "warning" : "default"} size="sm" variant="soft">{waitingRetries.length}</Chip>
          </div>
          {waitingRetries.length ? (
            <div
              aria-label={t("tasks.waitingRetries")}
              className="max-h-64 min-h-0 overflow-y-auto overscroll-contain pe-1 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
              role="region"
              tabIndex={0}
            >
              {waitingRetries.map(([key, retry]) => (
                <div className="grid gap-2 border-b border-border py-3 first:pt-0 last:border-0 last:pb-0" key={key}>
                  <p className="truncate text-sm font-medium" title={retry.filename}>{retry.filename}</p>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="min-w-0 truncate text-xs text-muted" title={retry.creator_key}>{retry.creator_key}</span>
                    <div className="flex shrink-0 flex-wrap items-center gap-1.5">
                      <Chip size="sm" variant="soft">{t("tasks.retryCount", { count: retry.retry_count })}</Chip>
                      <Chip
                        color={retry.status_code !== null && retry.status_code >= 500 ? "danger" : retry.status_code !== null ? "warning" : "default"}
                        size="sm"
                        variant="soft"
                      >
                        {retry.status_code !== null ? `HTTP ${retry.status_code}` : "HTTP —"}
                      </Chip>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-muted">{t("common.none")}</p>}
        </Surface>
      </div>
      <Surface className="grid gap-4 rounded-lg border border-border p-5">
        <div className="flex items-center justify-between gap-3"><h2 className="font-semibold">{t("tasks.logs")}</h2><Chip size="sm" variant="soft">{events.length}</Chip></div>
        <div
          aria-label={t("tasks.logs")}
          className="max-h-80 overflow-y-auto rounded-lg bg-default p-3 font-mono text-xs leading-6 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
          role="region"
          tabIndex={0}
        >
          {events.length ? events.map((event) => (
            <div className="grid grid-cols-[auto_minmax(0,1fr)] gap-3 border-b border-border py-1 last:border-0" key={event.id}>
              <time className="text-muted">{formatDateTime(event.created_at, i18n.language)}</time>
              <span className="min-w-0 break-words">
                <strong>{eventLabel(t, event.event_type)}</strong>{" "}
                {eventMessage(t, event)}
              </span>
            </div>
          )) : <p className="text-muted">{t("tasks.noLogs")}</p>}
        </div>
      </Surface>
      <div className="flex flex-wrap justify-end gap-2">
        {editable.has(task.status) ? <Button variant="outline" onPress={() => handlers.edit(task)}><Pencil aria-hidden="true" size={17} />{t("common.edit")}</Button> : null}
        {deletable.has(task.status) ? <Button variant="danger" onPress={() => handlers.remove(task)}><Trash2 aria-hidden="true" size={17} />{t("common.delete")}</Button> : null}
      </div>
    </>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="min-w-0 rounded-lg bg-default p-4"><p className="text-xs text-muted">{label}</p><p className="mt-1 truncate font-semibold tabular-nums" title={value}>{value}</p></div>;
}

function TaskFailurePanel({
  report,
  fallback,
}: {
  report: TaskFailureReport | null | undefined;
  fallback: string | null;
}) {
  const { t } = useTranslation();
  const items = taskFailureItems(report);
  if (!report && !fallback) return null;

  const creatorItems = items.filter((item) => item.creator_id && !item.file_name);
  const fileItems = items.filter((item) => item.file_name);
  const otherItems = items.filter((item) => !item.creator_id && !item.file_name);
  const visibleFileItems = fileItems.slice(0, 20);
  const hiddenFileCount = fileItems.length - visibleFileItems.length;

  return (
    <Surface
      aria-labelledby="task-failure-title"
      className="overflow-hidden rounded-lg border border-danger/40"
    >
      <div className="flex items-start gap-3 border-b border-danger/20 bg-danger/5 p-4">
        <span className="grid size-9 shrink-0 place-items-center rounded-md bg-danger/10 text-danger">
          <AlertTriangle aria-hidden="true" size={19} />
        </span>
        <div className="min-w-0">
          <h2 className="font-semibold text-foreground" id="task-failure-title">
            {t("tasks.failures.title")}
          </h2>
          <p className="mt-1 text-sm leading-6 text-muted">
            {failureSummary(t, report, fallback)}
          </p>
          {report ? (
            <div className="mt-3 flex flex-wrap gap-2">
              <Chip color="danger" size="sm" variant="soft">
                {t("tasks.failures.creatorCount", { count: report.creator_failures })}
              </Chip>
              <Chip color="danger" size="sm" variant="soft">
                {t("tasks.failures.fileCount", { count: report.file_failures })}
              </Chip>
            </div>
          ) : null}
        </div>
      </div>
      {items.length ? (
        <div className="divide-y divide-border">
          <FailureGroup
            items={creatorItems}
            title={t("tasks.failures.creatorGroup")}
          />
          <FailureGroup
            items={visibleFileItems}
            title={t("tasks.failures.fileGroup")}
          />
          {hiddenFileCount > 0 ? (
            <p className="px-4 pb-4 text-sm text-muted">
              {t("tasks.failures.moreFiles", { count: hiddenFileCount })}
            </p>
          ) : null}
          <FailureGroup
            items={otherItems}
            title={t("tasks.failures.otherGroup")}
          />
        </div>
      ) : null}
    </Surface>
  );
}

function FailureGroup({ items, title }: { items: FailureItem[]; title: string }) {
  if (!items.length) return null;
  return (
    <section className="grid gap-3 p-4">
      <h3 className="text-xs font-semibold uppercase text-muted">{title}</h3>
      <div className="divide-y divide-border">
        {items.map((item, index) => (
          <FailureRow item={item} key={`${item.stage}-${failureSubject(item) ?? "general"}-${index}`} />
        ))}
      </div>
    </section>
  );
}

function FailureRow({ item }: { item: FailureItem }) {
  const { t } = useTranslation();
  const subject = failureSubject(item);
  return (
    <div className="grid gap-2 py-3 first:pt-0 last:pb-0 sm:grid-cols-[minmax(8rem,0.35fr)_minmax(0,1fr)] sm:gap-4">
      <div className="min-w-0">
        <Chip color="danger" size="sm" variant="soft">
          {failureStageLabel(t, item.stage)}
        </Chip>
        {subject ? (
          <p className="mt-2 truncate text-sm font-medium" title={subject}>{subject}</p>
        ) : null}
      </div>
      <div className="min-w-0">
        <p className="text-sm font-medium leading-6 text-foreground">{failureMessage(t, item)}</p>
        {item.fields?.length ? (
          <p className="mt-1 break-words font-mono text-xs text-muted">
            {t("tasks.failures.fields", { fields: item.fields.join(", ") })}
          </p>
        ) : null}
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <Chip color={item.retryable ? "warning" : "default"} size="sm" variant="soft">
            {item.retryable ? t("tasks.failures.retryable") : t("tasks.failures.notRetryable")}
          </Chip>
          <span className="text-xs leading-5 text-muted">{failureAdvice(t, item)}</span>
        </div>
      </div>
    </div>
  );
}

function taskSpeed(task: TaskRecord): number {
  return speedVisible.has(task.status) ? task.progress.speed_bps : 0;
}

function taskStatusFilter(value: string | null): TaskStatusFilter {
  const filters: TaskStatusFilter[] = [
    "active",
    "waiting",
    "paused",
    "completed",
    "failed",
    "stopped",
    "interrupted",
  ];
  return filters.includes(value as TaskStatusFilter) ? value as TaskStatusFilter : "all";
}

function matchesTaskStatus(status: TaskStatus, filter: TaskStatusFilter): boolean {
  if (filter === "all") return true;
  if (filter === "active") return ["running", "pause_requested", "stop_requested"].includes(status);
  if (filter === "waiting") return ["queued", "blocked"].includes(status);
  return status === filter;
}
