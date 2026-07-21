import type { DownloadTaskSpec } from "../types";

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
