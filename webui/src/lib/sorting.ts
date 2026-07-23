import type { SortDescriptor } from "@heroui/react";

import { syncTaskCreatorNames } from "./taskPresentation";
import type { CreatorRosterItem, TaskRecord, TaskStatus } from "../types";

export type SortValue = boolean | number | string | null | undefined;

const taskStatusOrder: Record<TaskStatus, number> = {
  running: 0,
  pause_requested: 1,
  stop_requested: 2,
  queued: 3,
  blocked: 4,
  paused: 5,
  interrupted: 6,
  failed: 7,
  stopped: 8,
  completed: 9,
};

export function stableSort<T>(
  items: readonly T[],
  descriptor: SortDescriptor,
  valueFor: (item: T, column: string) => SortValue,
  locale: string,
): T[] {
  const collator = new Intl.Collator(locale, { numeric: true, sensitivity: "base" });
  const column = String(descriptor.column);
  return items
    .map((item, index) => ({ item, index }))
    .sort((left, right) => {
      const leftValue = valueFor(left.item, column);
      const rightValue = valueFor(right.item, column);
      const leftEmpty = isEmpty(leftValue);
      const rightEmpty = isEmpty(rightValue);
      if (leftEmpty !== rightEmpty) return leftEmpty ? 1 : -1;
      if (leftEmpty && rightEmpty) return left.index - right.index;

      let result: number;
      if (typeof leftValue === "number" && typeof rightValue === "number") {
        result = leftValue - rightValue;
      } else if (typeof leftValue === "boolean" && typeof rightValue === "boolean") {
        result = Number(leftValue) - Number(rightValue);
      } else {
        result = collator.compare(String(leftValue), String(rightValue));
      }
      if (result === 0) return left.index - right.index;
      return descriptor.direction === "descending" ? -result : result;
    })
    .map(({ item }) => item);
}

export function nextSortDescriptor(
  current: SortDescriptor | null,
  column: string,
  descendingByDefault: ReadonlySet<string> = new Set(),
): SortDescriptor {
  if (String(current?.column) === column) {
    return {
      column,
      direction: current?.direction === "ascending" ? "descending" : "ascending",
    };
  }
  return {
    column,
    direction: descendingByDefault.has(column) ? "descending" : "ascending",
  };
}

export function normalizeTableSort(
  current: SortDescriptor | null,
  next: SortDescriptor,
  descendingByDefault: ReadonlySet<string> = new Set(),
): SortDescriptor {
  const column = String(next.column);
  if (String(current?.column) !== column) {
    return {
      column,
      direction: descendingByDefault.has(column) ? "descending" : "ascending",
    };
  }
  return next;
}

export function taskStatusRank(status: TaskStatus): number {
  return taskStatusOrder[status];
}

export function taskTargetSortText(
  task: TaskRecord,
  creators: readonly CreatorRosterItem[] = [],
): string {
  if (task.spec.kind === "sync") {
    return syncTaskCreatorNames(task, creators).join(" ");
  }
  return [
    task.presentation?.title?.trim(),
    task.presentation?.creator_name?.trim(),
    task.spec.service,
    task.spec.creator_id,
    task.spec.post_id,
    task.spec.post,
  ]
    .filter(Boolean)
    .join(" ");
}

function isEmpty(value: SortValue): value is null | undefined | "" {
  return value === null || value === undefined || value === "";
}
