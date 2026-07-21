import {
  Button,
  Chip,
  Surface,
  Table,
  toast,
} from "@heroui/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  Eye,
  Pause,
  Pencil,
  Play,
  Plus,
  Square,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";

import { TaskEditor } from "../components/TaskEditor";
import { TaskTarget } from "../components/TaskTarget";
import {
  ConfirmModal,
  DataTableFrame,
  EmptyPanel,
  FormCheckbox,
  IconButton,
  PageHeader,
  PageLoading,
  ProgressMeter,
  TaskStatusChip,
} from "../components/ui";
import { api, errorText } from "../lib/api";
import { useAuth } from "../lib/auth";
import { formatBytes, formatDateTime, formatDuration, taskPercent } from "../lib/format";
import type {
  CreatorReference,
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

export function TasksPage() {
  const { t } = useTranslation();
  const { taskId } = useParams();
  const navigate = useNavigate();
  const { session } = useAuth();
  const queryClient = useQueryClient();
  const tasksQuery = useQuery({ queryKey: ["tasks"], queryFn: () => api<TaskRecord[]>("/tasks") });
  const creatorsQuery = useQuery({ queryKey: ["creators"], queryFn: () => api<CreatorReference[]>("/creators") });
  const [editor, setEditor] = useState<TaskRecord | "new" | null>(null);
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState<TaskRecord | null>(null);
  const [deleteOutput, setDeleteOutput] = useState(false);
  useTaskStream(queryClient);

  const cleanupQuery = useQuery({
    queryKey: ["task-cleanup", removing?.id],
    queryFn: () => api<TaskCleanupPreview>(`/tasks/${removing?.id}/cleanup-preview`),
    enabled: Boolean(removing),
  });
  const eventsQuery = useQuery({
    queryKey: ["task-events", taskId],
    queryFn: () => api<TaskEvent[]>(`/tasks/${taskId}/events?limit=300`),
    enabled: Boolean(taskId),
    refetchInterval: taskId ? 1500 : false,
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

  return (
    <div className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-6">
      {taskId && selected ? (
        <TaskDetails
          attempts={attemptsQuery.data ?? []}
          events={eventsQuery.data ?? []}
          task={selected}
          handlers={handlers}
          onBack={() => navigate("/tasks")}
        />
      ) : (
        <TaskList tasks={tasks} handlers={handlers} onCreate={() => setEditor("new")} />
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

function TaskList({ tasks, handlers, onCreate }: { tasks: TaskRecord[]; handlers: TaskHandlers; onCreate: () => void }) {
  const { t, i18n } = useTranslation();
  return (
    <>
      <PageHeader
        description={t("tasks.description")}
        title={t("tasks.title")}
        actions={<Button variant="primary" onPress={onCreate}><Plus aria-hidden="true" size={18} />{t("tasks.create")}</Button>}
      />
      {!tasks.length ? <EmptyPanel title={t("tasks.empty")} /> : (
        <>
          <DataTableFrame className="hidden min-[1360px]:block">
            <Table.Content aria-label={t("tasks.title")} className="task-table-content min-w-[1100px]">
              <Table.Header>
                <Table.Column isRowHeader>{t("tasks.target")}</Table.Column>
                <Table.Column>{t("common.status")}</Table.Column>
                <Table.Column>{t("tasks.progress")}</Table.Column>
                <Table.Column>{t("tasks.totalSpeed")}</Table.Column>
                <Table.Column>{t("tasks.output")}</Table.Column>
                <Table.Column>{t("common.created")}</Table.Column>
                <Table.Column>{t("common.actions")}</Table.Column>
              </Table.Header>
              <Table.Body>
                {tasks.map((task, index) => (
                  <Table.Row className="task-table-row" id={task.id} key={task.id}>
                    <Table.Cell className="w-60 min-w-60 max-w-60"><TaskTarget task={task} /></Table.Cell>
                    <Table.Cell className="min-w-24"><TaskStatusChip status={task.status} /></Table.Cell>
                    <Table.Cell className="min-w-28"><TaskProgressSummary task={task} /></Table.Cell>
                    <Table.Cell className="min-w-20 whitespace-nowrap text-sm font-medium tabular-nums">{formatBytes(task.progress.speed_bps, "/s")}</Table.Cell>
                    <Table.Cell><code className="block max-w-32 truncate text-xs text-muted" title={task.spec.output}>{task.spec.output}</code></Table.Cell>
                    <Table.Cell className="w-24 max-w-24 text-xs leading-relaxed text-muted"><TaskCreatedTime locale={i18n.language} value={task.created_at} /></Table.Cell>
                    <Table.Cell className="min-w-[332px]"><TaskActions canMoveDown={index < tasks.length - 1} canMoveUp={index > 0} task={task} handlers={handlers} /></Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table.Content>
          </DataTableFrame>
          <div className="grid gap-3 min-[1360px]:hidden">
            {tasks.map((task, index) => (
              <Surface className="task-mobile-card grid gap-4 rounded-lg border border-border p-4" key={task.id}>
                <div className="flex min-w-0 items-start justify-between gap-3">
                  <TaskTarget task={task} />
                  <TaskStatusChip status={task.status} />
                </div>
                <div className="grid grid-cols-[minmax(0,1fr)_auto] items-end gap-4">
                  <TaskProgressSummary task={task} />
                  <div className="text-right">
                    <p className="text-xs text-muted">{t("tasks.totalSpeed")}</p>
                    <strong className="text-sm tabular-nums text-foreground">{formatBytes(task.progress.speed_bps, "/s")}</strong>
                  </div>
                </div>
                <div className="grid gap-1 border-t border-border pt-3 text-xs text-muted">
                  <code className="truncate" title={task.spec.output}>{task.spec.output}</code>
                  <span>{formatDateTime(task.created_at, i18n.language)}</span>
                </div>
                <TaskActions mobile canMoveDown={index < tasks.length - 1} canMoveUp={index > 0} task={task} handlers={handlers} />
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
  mobile = false,
}: {
  task: TaskRecord;
  handlers: TaskHandlers;
  canMoveUp: boolean;
  canMoveDown: boolean;
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
    <div className={mobile ? "task-action-grid grid grid-cols-4 justify-items-center gap-1 border-t border-border pt-3" : "task-action-grid flex items-center justify-end gap-1"}>
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
      <IconButton icon={ArrowUp} isDisabled={!canMoveUp} label={t("tasks.moveUp")} tooltip={canMoveUp ? t("tasks.moveUp") : t("tasks.firstInQueue")} onPress={() => handlers.reorder(task, Math.max(1, task.position - 1))} />
      <IconButton icon={ArrowDown} isDisabled={!canMoveDown} label={t("tasks.moveDown")} tooltip={canMoveDown ? t("tasks.moveDown") : t("tasks.lastInQueue")} onPress={() => handlers.reorder(task, task.position + 1)} />
      <IconButton className="text-danger" icon={Trash2} isDisabled={!canDelete} label={t("common.delete")} tooltip={canDelete ? t("common.delete") : unavailable(t("common.delete"))} onPress={() => handlers.remove(task)} />
    </div>
  );
}

function TaskDetails({
  task,
  events,
  attempts,
  handlers,
  onBack,
}: {
  task: TaskRecord;
  events: TaskEvent[];
  attempts: TaskAttempt[];
  handlers: TaskHandlers;
  onBack: () => void;
}) {
  const { t, i18n } = useTranslation();
  const progress = task.progress;
  const percent = taskPercent(progress.processed_files, progress.queued_files, progress.transferred_bytes, progress.total_bytes);
  return (
    <>
      <PageHeader
        description={`${t(`common.${task.kind}`)} · ${task.id}`}
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
        <TaskTarget task={task} />
        <div className="flex shrink-0 flex-wrap items-center gap-2"><TaskStatusChip status={task.status} /><Chip size="sm" variant="soft">{t("tasks.attempts", { count: attempts.length })}</Chip></div>
      </Surface>
      {task.error ? <Surface className="rounded-lg border border-danger/40 p-4 text-sm text-danger">{task.error}</Surface> : null}
      <Surface className="grid gap-5 rounded-lg border border-border p-5">
        <ProgressMeter isIndeterminate={task.status === "running" && !progress.total_bytes && !progress.queued_files} label={t("tasks.progress")} value={percent} />
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label={t("tasks.totalSpeed")} value={formatBytes(progress.speed_bps, "/s")} />
          <Metric label={t("tasks.transferred")} value={`${formatBytes(progress.transferred_bytes)} / ${formatBytes(progress.total_bytes)}`} />
          <Metric label={t("tasks.files")} value={`${progress.processed_files} / ${progress.queued_files}`} />
          <Metric label="ETA" value={formatDuration(progress.eta_seconds)} />
        </div>
      </Surface>
      <div className="grid gap-5 xl:grid-cols-2">
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
      </div>
      <Surface className="grid gap-4 rounded-lg border border-border p-5">
        <div className="flex items-center justify-between gap-3"><h2 className="font-semibold">{t("tasks.logs")}</h2><Chip size="sm" variant="soft">{events.length}</Chip></div>
        <div className="max-h-80 overflow-y-auto rounded-lg bg-default p-3 font-mono text-xs leading-6">
          {events.length ? events.map((event) => (
            <div className="grid grid-cols-[auto_minmax(0,1fr)] gap-3 border-b border-border py-1 last:border-0" key={event.id}>
              <time className="text-muted">{formatDateTime(event.created_at, i18n.language)}</time>
              <span className="min-w-0 break-words"><strong>{event.event_type}</strong> {eventMessage(event)}</span>
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

function eventMessage(event: TaskEvent): string {
  if (typeof event.data.message === "string") return event.data.message;
  if (typeof event.data.creator === "string") return event.data.creator;
  if (typeof event.data.filename === "string") return event.data.filename;
  if (typeof event.data.status === "string") return event.data.status;
  return "";
}

function useTaskStream(queryClient: ReturnType<typeof useQueryClient>) {
  const refreshTimer = useRef<number | null>(null);
  useEffect(() => {
    if (typeof EventSource === "undefined") return undefined;
    const source = new EventSource("/api/v1/events");
    const refresh = () => {
      if (refreshTimer.current !== null) return;
      refreshTimer.current = window.setTimeout(() => {
        refreshTimer.current = null;
        void queryClient.invalidateQueries({ queryKey: ["tasks"] });
      }, 150);
    };
    const eventTypes = ["task.created", "task.status", "task.updated", "task.reordered", "task.progress", "task.log", "creator.started", "creator.finished", "job.queued", "download.started", "download.progress", "download.finished"];
    for (const type of eventTypes) source.addEventListener(type, refresh);
    return () => {
      source.close();
      if (refreshTimer.current !== null) window.clearTimeout(refreshTimer.current);
    };
  }, [queryClient]);
}
