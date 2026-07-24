import type { TFunction } from "i18next";

import type {
  FailureCode,
  FailureItem,
  FailureStage,
  TaskEvent,
  TaskFailureReport,
} from "../types";
import { formatBytes, formatDuration } from "./format";

const failureCodes = new Set<FailureCode>([
  "network",
  "timeout",
  "rate_limited",
  "http_error",
  "response_incompatible",
  "permission_denied",
  "disk_full",
  "download_failed",
  "resource_not_found",
  "unknown",
]);

const failureStages = new Set<FailureStage>([
  "creator_profile",
  "work_list",
  "work_detail",
  "revisions",
  "job_generation",
  "file_request",
  "file_write",
  "index_write",
]);

export function failureMessage(t: TFunction, item: FailureItem): string {
  const fallback = item.code === "unknown" && item.message.trim()
    ? item.message.trim()
    : t("tasks.failures.codes.unknown");
  return t(`tasks.failures.codes.${item.code}`, {
    status: item.http_status ?? "",
    defaultValue: fallback,
  });
}

export function failureStageLabel(t: TFunction, stage: FailureStage): string {
  return t(`tasks.failures.stages.${stage}`);
}

export function failureAdvice(t: TFunction, item: FailureItem): string {
  const specific = new Set<FailureCode>([
    "rate_limited",
    "response_incompatible",
    "permission_denied",
    "disk_full",
    "resource_not_found",
  ]);
  const key = specific.has(item.code)
    ? `tasks.failures.advice.${item.code}`
    : item.retryable
      ? "tasks.failures.advice.retry"
      : "tasks.failures.advice.check";
  return t(key);
}

export function failureSubject(item: FailureItem): string | null {
  if (item.file_name?.trim()) return item.file_name.trim();
  if (item.platform?.trim() && item.creator_id?.trim()) {
    return `${item.platform.trim()}:${item.creator_id.trim()}`;
  }
  return item.creator_id?.trim() || item.operation?.trim() || null;
}

export function taskFailureItems(report: TaskFailureReport | null | undefined): FailureItem[] {
  return report?.items ?? [];
}

export function failureSummary(
  t: TFunction,
  report: TaskFailureReport | null | undefined,
  fallback?: string | null,
): string {
  if (report) {
    return t("tasks.failures.summary", {
      creatorCount: report.creator_failures,
      fileCount: report.file_failures,
    });
  }
  return fallback?.trim() || t("tasks.failures.codes.unknown");
}

export function primaryFailure(
  report: TaskFailureReport | null | undefined,
): FailureItem | null {
  return taskFailureItems(report)[0] ?? null;
}

export function eventLabel(t: TFunction, eventType: string): string {
  return t(`tasks.events.${eventType}`, { defaultValue: eventType });
}

export function eventMessage(t: TFunction, event: TaskEvent): string {
  const report = parseFailureReport(event.data.failure_report);
  if (report) {
    return failureSummary(
      t,
      report,
      typeof event.data.message === "string" ? event.data.message : null,
    );
  }
  const failure = parseFailureItem(event.data.failure);
  const subject = failure ? failureSubject(failure) : null;
  if (failure) {
    return t("tasks.failures.event", {
      subject: subject ?? t("common.unknown"),
      reason: failureMessage(t, failure),
    });
  }
  if (event.event_type === "download.retrying" && typeof event.data.filename === "string") {
    const retryCount = typeof event.data.retry_count === "number" ? event.data.retry_count : 0;
    const status = typeof event.data.status_code === "number" ? `HTTP ${event.data.status_code}` : "HTTP —";
    return `${event.data.filename} · ${t("tasks.retryCount", { count: retryCount })} · ${status}`;
  }
  if (
    event.event_type === "creator.finished"
    && typeof event.data.creator === "string"
  ) {
    return t("tasks.eventDetails.creatorSummary", {
      creator: event.data.creator,
      queued: eventNumber(event.data.queued_files),
      completed: eventNumber(event.data.completed_files),
      existing: eventNumber(event.data.existing_files),
      failed: eventNumber(event.data.failed_files),
    });
  }
  if (
    event.event_type === "download.started"
    && typeof event.data.filename === "string"
  ) {
    return t("tasks.eventDetails.transferStarted", {
      file: event.data.filename,
      creator: eventString(event.data.creator),
      completed: formatBytes(eventNumber(event.data.completed)),
      total: formatBytes(eventOptionalNumber(event.data.total)),
    });
  }
  if (
    event.event_type === "download.finished"
    && typeof event.data.filename === "string"
  ) {
    const outcome = eventString(event.data.outcome || event.data.status);
    return t("tasks.eventDetails.transferFinished", {
      file: event.data.filename,
      creator: eventString(event.data.creator),
      outcome: t(`tasks.downloadOutcomes.${outcome}`, { defaultValue: outcome }),
      completed: formatBytes(eventNumber(event.data.completed_bytes)),
      total: formatBytes(eventOptionalNumber(event.data.total_bytes)),
      duration: formatDuration(eventOptionalNumber(event.data.elapsed_seconds)),
      speed: formatBytes(eventOptionalNumber(event.data.average_speed_bps), "/s"),
    });
  }
  if (typeof event.data.message === "string") return event.data.message;
  if (typeof event.data.creator === "string") return event.data.creator;
  if (typeof event.data.filename === "string") return event.data.filename;
  if (typeof event.data.status === "string") {
    return t(`tasks.statuses.${event.data.status}`, {
      defaultValue: event.data.status,
    });
  }
  return "";
}

export function parseFailureReport(value: unknown): TaskFailureReport | null {
  if (!isRecord(value)) return null;
  if (
    typeof value.summary !== "string"
    || !isNonNegativeInteger(value.creator_failures)
    || !isNonNegativeInteger(value.file_failures)
    || !Array.isArray(value.items)
  ) {
    return null;
  }
  const items = value.items
    .slice(0, 100)
    .map(parseFailureItem)
    .filter((item): item is FailureItem => item !== null);
  return {
    summary: value.summary,
    creator_failures: value.creator_failures,
    file_failures: value.file_failures,
    items,
  };
}

export function parseFailureItem(value: unknown): FailureItem | null {
  if (!isRecord(value)) return null;
  if (!failureCodes.has(value.code as FailureCode)) return null;
  if (!failureStages.has(value.stage as FailureStage)) return null;
  if (typeof value.message !== "string" || typeof value.retryable !== "boolean") return null;
  return {
    code: value.code as FailureCode,
    stage: value.stage as FailureStage,
    message: value.message,
    retryable: value.retryable,
    platform: optionalString(value.platform),
    creator_id: optionalString(value.creator_id),
    file_name: optionalString(value.file_name),
    http_status: typeof value.http_status === "number" ? value.http_status : null,
    operation: optionalString(value.operation),
    fields: Array.isArray(value.fields)
      ? value.fields.filter((field): field is string => typeof field === "string")
      : [],
  };
}

function optionalString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function eventNumber(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function eventOptionalNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function eventString(value: unknown): string {
  return typeof value === "string" && value.trim() ? value : "—";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonNegativeInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}
