import { Button, Chip, Tooltip } from "@heroui/react";
import {
  IconAlertTriangle as AlertTriangle,
  IconDownload as Download,
  IconRefresh as RefreshCw,
} from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

import { failureMessage, primaryFailure } from "../lib/taskFailures";
import { syncTaskCreatorNames } from "../lib/taskPresentation";
import type { CreatorRosterItem, TaskRecord, TaskSpec } from "../types";

export function TaskTarget({
  task,
  creators = [],
}: {
  task: TaskRecord;
  creators?: readonly CreatorRosterItem[];
}) {
  const { t } = useTranslation();
  const failure = primaryFailure(task.failure);
  const failureText = failure
    ? failureMessage(t, failure)
    : task.status === "failed"
      ? task.error?.trim()
      : null;
  if (task.spec.kind === "sync") {
    const names = syncTaskCreatorNames(task, creators);
    const visibleNames = names.slice(0, 2);
    const hiddenCount = names.length - visibleNames.length;
    const summary = names.length
      ? `${visibleNames.join(" · ")}${hiddenCount ? ` · ${t("tasks.moreCreators", { count: hiddenCount })}` : ""}`
      : t("tasks.noFrozenCreators");
    const roster = task.spec.creators
      .map((creator) => `${creator.alias?.trim() || creator.creator_id} (${creator.service}:${creator.creator_id})`)
      .join("\n");
    return (
      <div className="task-target flex min-w-0 flex-1 items-start gap-3">
        <span className="task-kind-icon" data-kind="sync"><RefreshCw aria-hidden="true" size={18} /></span>
        <div className="min-w-0 flex-1">
          <SyncTaskTitle names={names} />
          <div className="mt-1 flex min-w-0 items-center gap-2">
            <Chip className="shrink-0" size="sm" variant="soft">{t("common.sync")}</Chip>
            {roster ? (
              <Tooltip>
                <Button className="h-auto min-h-0 w-full min-w-0 justify-start p-0 text-left text-xs font-normal text-muted" size="sm" variant="ghost">
                  <span className="min-w-0 truncate">{summary}</span>
                </Button>
                <Tooltip.Content className="max-w-sm whitespace-pre-line">{roster}</Tooltip.Content>
              </Tooltip>
            ) : <p className="truncate text-xs text-muted">{summary}</p>}
          </div>
          {failureText ? <FailureLine text={failureText} /> : null}
        </div>
      </div>
    );
  }

  const identity = downloadIdentity(task.spec);
  const title = task.presentation?.title?.trim() || (identity.postId ? t("tasks.postNumber", { id: identity.postId }) : t("tasks.unknownPost"));
  const creatorName = task.presentation?.creator_name?.trim();
  const metadata = [
    creatorName,
    identity.service && identity.creatorId ? `${identity.service}:${identity.creatorId}` : identity.creatorId,
    identity.postId ? `#${identity.postId}` : null,
    identity.revisionId ? t("tasks.revisionShort", { id: identity.revisionId }) : null,
  ].filter(Boolean).join(" · ") || task.spec.post || t("common.unknown");
  return (
    <div className="task-target flex min-w-0 flex-1 items-start gap-3">
      <span className="task-kind-icon" data-kind="download"><Download aria-hidden="true" size={18} /></span>
      <div className="min-w-0 flex-1">
        <p className="task-target-title truncate text-sm font-semibold" title={title}>{title}</p>
        <div className="mt-1 flex min-w-0 items-center gap-2">
          <Chip className="shrink-0" color="accent" size="sm" variant="soft">{t("common.download")}</Chip>
          <p className="truncate text-xs text-muted" title={metadata}>{metadata}</p>
        </div>
        {failureText ? <FailureLine text={failureText} /> : null}
      </div>
    </div>
  );
}

function SyncTaskTitle({ names }: { names: string[] }) {
  const { t } = useTranslation();
  if (!names.length) {
    return (
      <p className="task-target-title truncate text-sm font-semibold" title={t("tasks.noFrozenCreators")}>
        {t("tasks.noFrozenCreators")}
      </p>
    );
  }
  if (names.length === 1) {
    return (
      <p className="task-target-title truncate text-sm font-semibold" title={names[0]}>
        {names[0]}
      </p>
    );
  }
  const suffix = t("tasks.creatorGroupSuffix", { count: names.length });
  return (
    <p
      className="task-target-title task-target-title-group flex min-w-0 items-baseline text-sm font-semibold"
      title={`${names[0]} ${suffix}`}
    >
      <span className="min-w-0 truncate">{names[0]}</span>
      <span className="shrink-0 whitespace-pre"> {suffix}</span>
    </p>
  );
}

function FailureLine({ text }: { text: string }) {
  return (
    <p className="mt-1.5 flex min-w-0 items-start gap-1.5 text-xs leading-5 text-danger" title={text}>
      <AlertTriangle aria-hidden="true" className="mt-0.5 shrink-0" size={14} />
      <span className="line-clamp-2">{text}</span>
    </p>
  );
}

function downloadIdentity(spec: Extract<TaskSpec, { kind: "download" }>) {
  if (spec.service && spec.creator_id && spec.post_id) {
    return { service: spec.service, creatorId: spec.creator_id, postId: spec.post_id, revisionId: spec.revision_id };
  }
  try {
    const parts = new URL(spec.post ?? "", "https://pawchive.invalid").pathname.split("/").filter(Boolean).map(decodeURIComponent);
    return {
      service: parts[0] ?? null,
      creatorId: parts[1] === "user" ? parts[2] ?? null : null,
      postId: parts[3] === "post" ? parts[4] ?? null : null,
      revisionId: parts[5] === "revision" ? parts[6] ?? spec.revision_id : spec.revision_id,
    };
  } catch {
    return { service: null, creatorId: null, postId: null, revisionId: spec.revision_id };
  }
}
