import type {
  CreatorReference,
  CreatorRosterItem,
  DownloadTaskSpec,
  TaskRecord,
} from "../types";

function encodeTargetPart(value: string): string {
  return encodeURIComponent(value).replace(/[!'()*]/g, (character) =>
    `%${character.charCodeAt(0).toString(16).toUpperCase()}`,
  );
}

export function downloadTaskTargetKey(
  service: string,
  creatorId: string,
  postId: string,
  revisionId?: string | null,
): string {
  return `download/${[service.toLowerCase(), creatorId, postId, revisionId ?? ""]
    .map(encodeTargetPart)
    .join("/")}`;
}

export function taskTargetKey(spec: DownloadTaskSpec): string | null {
  if (!spec.service || !spec.creator_id || !spec.post_id) return null;
  return downloadTaskTargetKey(spec.service, spec.creator_id, spec.post_id, spec.revision_id);
}

export function creatorPresentationName(
  creator: CreatorReference,
  roster: readonly CreatorRosterItem[] = [],
): string {
  const profile = roster.find(
    (item) =>
      item.service.toLocaleLowerCase() === creator.service.toLocaleLowerCase()
      && item.creator_id === creator.creator_id,
  );
  return (
    profile?.name?.trim()
    || profile?.alias?.trim()
    || creator.alias?.trim()
    || creator.creator_id
  );
}

export function syncTaskCreatorNames(
  task: TaskRecord,
  roster: readonly CreatorRosterItem[] = [],
): string[] {
  if (task.spec.kind !== "sync") return [];
  return task.spec.creators.map((creator) => creatorPresentationName(creator, roster));
}
