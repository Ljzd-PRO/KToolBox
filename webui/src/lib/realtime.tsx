import { useQueryClient, type QueryClient } from "@tanstack/react-query";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { api, ApiError } from "./api";
import { useAuth } from "./auth";
import type {
  Session,
  TaskEvent,
  TaskFailureReport,
  TaskProgress,
  TaskRecord,
  TaskStatus,
} from "../types";

export type RealtimeStatus =
  | "connecting"
  | "connected"
  | "reconnecting"
  | "fallback"
  | "offline";

type RealtimeContextValue = {
  status: RealtimeStatus;
  lastSignalAt: number | null;
  filesystemRevision: number;
  refreshNow: () => void;
  reconnect: () => void;
};

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

const eventTypes = [
  "task.created",
  "task.status",
  "task.updated",
  "task.reordered",
  "task.deleted",
  "task.progress",
  "task.log",
  "creator.started",
  "creator.finished",
  "job.queued",
  "download.started",
  "download.progress",
  "download.retrying",
  "download.finished",
  "creators.changed",
  "creator_profile.changed",
  "blockers.changed",
  "configuration.changed",
  "mcp.tokens.changed",
  "filesystem.changed",
] as const;

const localQueryRoots = new Set([
  "project",
  "tasks",
  "creators",
  "blockers",
  "config-schema",
  "config-document",
  "mcp",
  "task-attempts",
  "task-cleanup",
  "task-events",
]);

const taskStatuses = new Set<TaskStatus>([
  "queued",
  "blocked",
  "running",
  "pause_requested",
  "paused",
  "stop_requested",
  "stopped",
  "completed",
  "failed",
  "interrupted",
]);

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const { invalidateSession } = useAuth();
  const [status, setStatus] = useState<RealtimeStatus>("connecting");
  const [lastSignalAt, setLastSignalAt] = useState<number | null>(null);
  const [filesystemRevision, setFilesystemRevision] = useState(0);
  const [generation, setGeneration] = useState(0);
  const statusRef = useRef(status);
  const lastSignalRef = useRef<number | null>(null);
  const latestEventIdRef = useRef(0);
  const pendingRootsRef = useRef(new Set<string>());
  const pendingTimerRef = useRef<number | null>(null);
  const hiddenDirtyRef = useRef(false);

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  const flushPending = useCallback(() => {
    if (pendingTimerRef.current !== null) {
      window.clearTimeout(pendingTimerRef.current);
      pendingTimerRef.current = null;
    }
    const roots = [...pendingRootsRef.current];
    pendingRootsRef.current.clear();
    if (!roots.length) return;
    const hidden = document.visibilityState === "hidden";
    if (hidden) hiddenDirtyRef.current = true;
    for (const root of roots) {
      void queryClient.invalidateQueries({
        predicate: (query) => query.queryKey[0] === root,
        refetchType: hidden ? "none" : "active",
      });
    }
  }, [queryClient]);

  const queueRefresh = useCallback((...roots: string[]) => {
    roots.forEach((root) => pendingRootsRef.current.add(root));
    if (pendingTimerRef.current !== null) return;
    pendingTimerRef.current = window.setTimeout(flushPending, 250);
  }, [flushPending]);

  const refreshNow = useCallback(() => {
    pendingRootsRef.current.clear();
    for (const root of localQueryRoots) {
      void queryClient.invalidateQueries({
        predicate: (query) => query.queryKey[0] === root,
        refetchType: document.visibilityState === "hidden" ? "none" : "active",
      });
    }
    hiddenDirtyRef.current = document.visibilityState === "hidden";
    setFilesystemRevision((current) => current + 1);
  }, [queryClient]);

  const reconnect = useCallback(() => {
    setStatus(navigator.onLine ? "connecting" : "offline");
    setGeneration((current) => current + 1);
  }, []);

  useEffect(() => {
    if (typeof EventSource === "undefined") {
      const timer = window.setTimeout(() => {
        setStatus("fallback");
        refreshNow();
      });
      return () => window.clearTimeout(timer);
    }

    let active = true;
    let source: EventSource | null = null;
    let fallbackTimer: number | null = null;
    let sessionCheckPending = false;

    const clearFallbackTimer = () => {
      if (fallbackTimer !== null) {
        window.clearTimeout(fallbackTimer);
        fallbackTimer = null;
      }
    };
    const markSignal = () => {
      const now = Date.now();
      lastSignalRef.current = now;
      setLastSignalAt(now);
    };
    const enterReconnect = () => {
      if (!navigator.onLine) {
        setStatus("offline");
        return;
      }
      setStatus("reconnecting");
      clearFallbackTimer();
      fallbackTimer = window.setTimeout(() => {
        if (active && statusRef.current !== "connected") setStatus("fallback");
      }, 5000);
    };
    const checkSession = async () => {
      if (sessionCheckPending) return;
      sessionCheckPending = true;
      try {
        await api<Session>("/session");
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          source?.close();
          invalidateSession();
        }
      } finally {
        sessionCheckPending = false;
      }
    };
    const receive = (message: MessageEvent<string>) => {
      markSignal();
      const event = parseEvent(message.data);
      if (!event || event.id <= latestEventIdRef.current) return;
      latestEventIdRef.current = event.id;
      applyRealtimeEvent(queryClient, event, queueRefresh, () => {
        setFilesystemRevision((current) => current + 1);
      });
    };
    const connect = () => {
      if (!active || !navigator.onLine) {
        setStatus("offline");
        return;
      }
      source = new EventSource("/api/v1/events");
      source.onopen = () => {
        if (!active) return;
        clearFallbackTimer();
        markSignal();
        setStatus("connected");
        refreshNow();
      };
      source.onerror = () => {
        if (!active) return;
        enterReconnect();
        void checkSession();
      };
      source.addEventListener("heartbeat", markSignal);
      for (const type of eventTypes) source.addEventListener(type, receive as EventListener);
    };

    connect();
    const watchdog = window.setInterval(() => {
      const lastSignal = lastSignalRef.current;
      if (
        active &&
        navigator.onLine &&
        lastSignal !== null &&
        Date.now() - lastSignal > 40_000
      ) {
        source?.close();
        enterReconnect();
        connect();
      }
    }, 5000);
    const handleOffline = () => {
      source?.close();
      setStatus("offline");
    };
    const handleOnline = () => {
      source?.close();
      setStatus("connecting");
      connect();
    };
    window.addEventListener("offline", handleOffline);
    window.addEventListener("online", handleOnline);

    return () => {
      active = false;
      clearFallbackTimer();
      window.clearInterval(watchdog);
      source?.close();
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("online", handleOnline);
    };
  }, [generation, invalidateSession, queryClient, queueRefresh, refreshNow]);

  useEffect(() => {
    if (status === "connected" || status === "connecting") return undefined;
    const refresh = () => {
      if (navigator.onLine && document.visibilityState !== "hidden") refreshNow();
    };
    const timer = window.setInterval(refresh, 10_000);
    return () => window.clearInterval(timer);
  }, [refreshNow, status]);

  useEffect(() => {
    const reveal = () => {
      if (document.visibilityState !== "visible") return;
      if (hiddenDirtyRef.current) {
        hiddenDirtyRef.current = false;
        refreshNow();
      }
    };
    document.addEventListener("visibilitychange", reveal);
    window.addEventListener("focus", reveal);
    return () => {
      document.removeEventListener("visibilitychange", reveal);
      window.removeEventListener("focus", reveal);
      if (pendingTimerRef.current !== null) window.clearTimeout(pendingTimerRef.current);
    };
  }, [refreshNow]);

  const value = useMemo<RealtimeContextValue>(
    () => ({ status, lastSignalAt, filesystemRevision, refreshNow, reconnect }),
    [filesystemRevision, lastSignalAt, reconnect, refreshNow, status],
  );
  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}

export function useRealtime(required?: true): RealtimeContextValue;
export function useRealtime(required: false): RealtimeContextValue | null;
// eslint-disable-next-line react-refresh/only-export-components
export function useRealtime(required = true): RealtimeContextValue | null {
  const value = useContext(RealtimeContext);
  if (!value && required) throw new Error("useRealtime must be used inside RealtimeProvider");
  return value;
}

function applyRealtimeEvent(
  queryClient: QueryClient,
  event: TaskEvent,
  queueRefresh: (...roots: string[]) => void,
  notifyFilesystem: () => void,
) {
  if (event.task_id) appendTaskEvent(queryClient, event);
  if (event.resource === "task" || event.task_id || event.event_type.startsWith("task.")) {
    applyTaskEvent(queryClient, event, queueRefresh);
    return;
  }
  if (event.event_type === "creators.changed" || event.event_type === "creator_profile.changed") {
    queueRefresh("creators", "config-document");
  } else if (event.event_type === "blockers.changed") {
    queueRefresh("blockers", "config-document");
  } else if (event.event_type === "configuration.changed") {
    queueRefresh("config-schema", "config-document", "project", "creators", "blockers");
  } else if (event.event_type === "mcp.tokens.changed") {
    queueRefresh("mcp");
  } else if (event.event_type === "filesystem.changed") {
    notifyFilesystem();
  }
}

function applyTaskEvent(
  queryClient: QueryClient,
  event: TaskEvent,
  queueRefresh: (...roots: string[]) => void,
) {
  const taskId = event.task_id ?? event.resource_id;
  if (event.event_type === "task.deleted" && taskId) {
    queryClient.setQueryData<TaskRecord[]>(["tasks"], (tasks) =>
      tasks?.filter((task) => task.id !== taskId),
    );
    queryClient.removeQueries({ queryKey: ["task-events", taskId] });
    queryClient.removeQueries({ queryKey: ["task-attempts", taskId] });
    return;
  }
  if (!taskId) {
    queueRefresh("tasks");
    return;
  }
  const progress = taskProgress(event.data.progress);
  const status = taskStatus(event.data.status);
  if (progress || status) {
    queryClient.setQueryData<TaskRecord[]>(["tasks"], (tasks) =>
      tasks?.map((task) => {
        if (task.id !== taskId) return task;
        return {
          ...task,
          ...(progress ? { progress } : {}),
          ...(status ? { status } : {}),
          ...(event.event_type === "task.status"
            ? {
                error: typeof event.data.error === "string" ? event.data.error : null,
                failure: (event.data.failure as TaskFailureReport | null | undefined) ?? null,
                blocked_by: typeof event.data.blocked_by === "string" ? event.data.blocked_by : null,
              }
            : {}),
          updated_at: event.created_at,
        };
      }),
    );
  }
  if (["task.created", "task.updated", "task.reordered"].includes(event.event_type)) {
    queueRefresh("tasks");
  }
  if (event.event_type === "task.status") queueRefresh("task-attempts");
}

function appendTaskEvent(queryClient: QueryClient, event: TaskEvent) {
  if (!event.task_id) return;
  queryClient.setQueryData<TaskEvent[]>(["task-events", event.task_id], (events) => {
    if (!events || events.some((item) => item.id === event.id)) return events;
    return [...events, event].sort((left, right) => left.id - right.id).slice(-200);
  });
}

function parseEvent(value: string): TaskEvent | null {
  try {
    const event = JSON.parse(value) as Partial<TaskEvent>;
    if (
      typeof event.id !== "number" ||
      typeof event.event_type !== "string" ||
      typeof event.created_at !== "string" ||
      !isRecord(event.data)
    ) {
      return null;
    }
    return {
      id: event.id,
      task_id: typeof event.task_id === "string" ? event.task_id : null,
      event_type: event.event_type,
      resource: typeof event.resource === "string" ? event.resource : null,
      resource_id: typeof event.resource_id === "string" ? event.resource_id : null,
      data: event.data,
      created_at: event.created_at,
    };
  } catch {
    return null;
  }
}

function taskProgress(value: unknown): TaskProgress | null {
  return isRecord(value) ? value as TaskProgress : null;
}

function taskStatus(value: unknown): TaskStatus | null {
  return typeof value === "string" && taskStatuses.has(value as TaskStatus)
    ? value as TaskStatus
    : null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
