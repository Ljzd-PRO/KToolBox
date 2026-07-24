import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "./auth";
import { RealtimeProvider, useRealtime } from "./realtime";
import { api } from "./api";
import type { CreatorRosterItem, TaskEvent, TaskProgress, TaskRecord } from "../types";

class FakeEventSource {
  static instances: FakeEventSource[] = [];

  readonly url: string;
  onopen: ((event: Event) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  closed = false;
  private readonly listeners = new Map<string, Set<EventListener>>();

  constructor(url: string | URL) {
    this.url = String(url);
    FakeEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: EventListener) {
    const listeners = this.listeners.get(type) ?? new Set<EventListener>();
    listeners.add(listener);
    this.listeners.set(type, listeners);
  }

  close() {
    this.closed = true;
  }

  open() {
    this.onopen?.(new Event("open"));
  }

  emit(type: string, data: unknown) {
    const event = new MessageEvent(type, { data: JSON.stringify(data) });
    this.listeners.get(type)?.forEach((listener) => listener(event));
  }
}

const progress: TaskProgress = {
  queued_files: 1,
  processed_files: 0,
  completed_files: 0,
  existing_files: 0,
  failed_files: 0,
  transferred_bytes: 0,
  total_bytes: 100,
  speed_bps: 0,
  eta_seconds: null,
  active_creators: [],
  active_downloads: {},
  waiting_retries: {},
};

const task: TaskRecord = {
  id: "task-1",
  kind: "download",
  status: "running",
  spec: {
    kind: "download",
    service: "fanbox",
    creator_id: "creator",
    post_id: "work",
    output: "downloads",
    dump_post_data: true,
  },
  presentation: null,
  position: 1,
  revision: 1,
  progress,
  error: null,
  failure: null,
  blocked_by: null,
  created_at: "2026-07-23T00:00:00Z",
  updated_at: "2026-07-23T00:00:00Z",
};

function Authenticated({ children }: { children: ReactNode }) {
  const { session } = useAuth();
  return session ? <RealtimeProvider>{children}</RealtimeProvider> : null;
}

function Probe() {
  const realtime = useRealtime();
  const tasks = useQuery({ queryKey: ["tasks"], queryFn: () => api<TaskRecord[]>("/tasks") });
  const creators = useQuery({
    queryKey: ["creators"],
    queryFn: () => api<CreatorRosterItem[]>("/creators"),
  });
  const events = useQuery({
    queryKey: ["task-events", "task-1"],
    queryFn: () => api<TaskEvent[]>("/tasks/task-1/events"),
  });
  return (
    <>
      <output aria-label="connection">{realtime.status}</output>
      <output aria-label="bytes">{tasks.data?.[0]?.progress.transferred_bytes ?? -1}</output>
      <output aria-label="speed">{tasks.data?.[0]?.progress.speed_bps ?? -1}</output>
      <output aria-label="task-status">{tasks.data?.[0]?.status ?? "missing"}</output>
      <output aria-label="creators">{creators.data?.length ?? -1}</output>
      <output aria-label="events">{events.data?.length ?? -1}</output>
      <output aria-label="creator-revision">{realtime.revisions.creators}</output>
      <output aria-label="filesystem-revision">{realtime.filesystemRevision}</output>
      <output aria-label="task-revision">
        {realtime.taskDefinitionRevisions["task-1"] ?? 0}
      </output>
    </>
  );
}

describe("RealtimeProvider", () => {
  let client: QueryClient;
  let creatorRequests: number;

  beforeEach(() => {
    FakeEventSource.instances = [];
    creatorRequests = 0;
    client = new QueryClient({
      defaultOptions: { queries: { retry: false, staleTime: Number.POSITIVE_INFINITY } },
    });
    vi.stubGlobal("EventSource", FakeEventSource);
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const path = String(input);
      if (path.endsWith("/session")) {
        return json({
          username: "owner",
          csrf_token: "csrf",
          created_at: "2026-07-23T00:00:00Z",
        });
      }
      if (path.endsWith("/tasks")) return json([task]);
      if (path.endsWith("/creators")) {
        creatorRequests += 1;
        return json([]);
      }
      if (path.endsWith("/tasks/task-1/events")) return json([]);
      throw new Error(`Unexpected request: ${path}`);
    }));
  });

  afterEach(() => {
    client.clear();
    vi.unstubAllGlobals();
  });

  it("uses one stream to patch task progress and invalidate changed resources", async () => {
    const rendered = render(
      <QueryClientProvider client={client}>
        <AuthProvider>
          <Authenticated>
            <Probe />
          </Authenticated>
        </AuthProvider>
      </QueryClientProvider>,
    );

    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));
    const source = FakeEventSource.instances[0];
    act(() => source.open());
    expect(await screen.findByLabelText("connection")).toHaveTextContent("connected");
    await waitFor(() => expect(screen.getByLabelText("bytes")).toHaveTextContent("0"));
    const initialCreatorRequests = creatorRequests;

    act(() => {
      source.emit("download.progress", taskEvent(1, "download.progress", {
        progress: { ...progress, transferred_bytes: 75, speed_bps: 25 },
      }));
    });
    expect(screen.getByLabelText("bytes")).toHaveTextContent("75");
    expect(screen.getByLabelText("events")).toHaveTextContent("1");

    act(() => {
      source.emit("download.finished", taskEvent(2, "download.finished", {
        status: "completed",
        outcome: "completed",
        progress: { ...progress, transferred_bytes: 90, speed_bps: 20 },
      }));
    });
    expect(screen.getByLabelText("task-status")).toHaveTextContent("running");
    expect(screen.getByLabelText("speed")).toHaveTextContent("20");

    act(() => {
      source.emit("download.progress", taskEvent(1, "download.progress", {
        progress: { ...progress, transferred_bytes: 90 },
      }));
      source.emit("creator_profile.changed", {
        ...taskEvent(3, "creator_profile.changed", {}),
        task_id: null,
        resource: "creator_profile",
        resource_id: "fanbox:creator",
      });
      source.emit("creators.changed", {
        ...taskEvent(4, "creators.changed", {}),
        task_id: null,
        resource: "creator",
        resource_id: "fanbox:creator",
      });
      source.emit("task.updated", taskEvent(5, "task.updated", {}));
      source.emit("filesystem.changed", {
        ...taskEvent(6, "filesystem.changed", {}),
        task_id: null,
        resource: "filesystem",
        resource_id: "downloads",
      });
    });
    expect(screen.getByLabelText("events")).toHaveTextContent("3");
    expect(screen.getByLabelText("creator-revision")).toHaveTextContent("1");
    expect(screen.getByLabelText("task-revision")).toHaveTextContent("1");
    expect(screen.getByLabelText("filesystem-revision")).toHaveTextContent("2");
    await waitFor(() => expect(creatorRequests).toBeGreaterThan(initialCreatorRequests));

    rendered.unmount();
    expect(source.closed).toBe(true);
  });

  it("enters fallback after a sustained disconnect and recovers on the same stream", async () => {
    render(
      <QueryClientProvider client={client}>
        <AuthProvider>
          <Authenticated>
            <Probe />
          </Authenticated>
        </AuthProvider>
      </QueryClientProvider>,
    );

    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));
    const source = FakeEventSource.instances[0];
    act(() => source.open());
    expect(await screen.findByLabelText("connection")).toHaveTextContent("connected");

    vi.useFakeTimers();
    act(() => source.onerror?.(new Event("error")));
    expect(screen.getByLabelText("connection")).toHaveTextContent("reconnecting");
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });
    expect(screen.getByLabelText("connection")).toHaveTextContent("fallback");

    act(() => source.open());
    expect(screen.getByLabelText("connection")).toHaveTextContent("connected");
    vi.useRealTimers();
  });
});

function taskEvent(id: number, eventType: string, data: Record<string, unknown>): TaskEvent {
  return {
    id,
    task_id: "task-1",
    event_type: eventType,
    resource: "task",
    resource_id: "task-1",
    data,
    created_at: "2026-07-23T00:00:01Z",
  };
}

function json(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
