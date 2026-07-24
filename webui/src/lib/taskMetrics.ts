import type { TaskRecord, TaskStatus } from "../types";

const speedStatuses = new Set<TaskStatus>([
  "running",
  "pause_requested",
  "stop_requested",
]);

export function taskDownloadSpeed(task: TaskRecord): number {
  const speed = task.progress.speed_bps;
  return speedStatuses.has(task.status) && Number.isFinite(speed) && speed > 0
    ? speed
    : 0;
}

export function totalDownloadSpeed(tasks: readonly TaskRecord[]): number {
  return tasks.reduce((total, task) => total + taskDownloadSpeed(task), 0);
}
