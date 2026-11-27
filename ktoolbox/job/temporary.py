from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from ktoolbox.api.client import PawchiveClient
from ktoolbox.api.errors import PawchiveError, PawchiveHTTPError
from ktoolbox.api.generated import FileReference, Post, Revision
from ktoolbox.api.temporary_files import active_temporary_url
from ktoolbox.api.utils import pawchive_client_scope


class TemporaryFileUnavailable(Exception):
    def __init__(self, status: int | None = None) -> None:
        super().__init__("The temporary Pawchive file is no longer available or has no usable download link")
        self.status = status


@dataclass(frozen=True, slots=True)
class TemporaryFile:
    source: TemporaryFileSource
    reference: FileReference
    primary: bool
    output_conflict: bool = False


class TemporaryFileSource:
    """Share a lazy detail lookup (and at most one refresh) between a work's files."""

    def __init__(self, post: Post, *, detail: Post | None = None) -> None:
        self._post = post
        self._detail = detail
        self._loaded = detail is not None
        self._refreshed = False
        self._error_status: int | None = None
        self._lock = asyncio.Lock()

    async def resolve(
        self,
        file: TemporaryFile,
        client: PawchiveClient | None,
        *,
        rejected_url: str | None = None,
        status: int | None = None,
    ) -> str:
        async with self._lock:
            reference = (
                _matching_file(self._detail, file)
                if self._detail is not None
                else file.reference
                if not self._loaded
                else None
            )
            now = datetime.now(timezone.utc)
            url = active_temporary_url(reference, now) if reference is not None else None
            if url and url != rejected_url:
                return url
            has_link = reference is not None and reference.temp_download_url is not None
            if not self._loaded or (has_link and not self._refreshed):
                self._refreshed = self._loaded or has_link or rejected_url is not None
                self._loaded = True
                self._detail = await self._fetch(client)
                reference = _matching_file(self._detail, file) if self._detail is not None else None
                url = active_temporary_url(reference, now) if reference is not None else None
                if url and url != rejected_url:
                    return url
            raise TemporaryFileUnavailable(status if status is not None else self._error_status)

    async def _fetch(self, client: PawchiveClient | None) -> Post | None:
        post = self._post
        detail: Post | None
        try:
            async with pawchive_client_scope(client) as api:
                if isinstance(post, Revision):
                    revisions = await api.list_post_revisions(post.service, post.user, post.id)
                    detail = next(
                        (revision for revision in revisions if revision.revision_id == post.revision_id), None
                    )
                else:
                    detail = await api.get_post(post.service, post.user, post.id)
        except PawchiveError as error:
            self._error_status = error.status_code if isinstance(error, PawchiveHTTPError) else None
            return None
        if detail is None or (detail.service, detail.user, detail.id) != (post.service, post.user, post.id):
            return None
        return detail


def _matching_file(post: Post, file: TemporaryFile) -> FileReference | None:
    candidates = ([post.file] if post.file else []) if file.primary else (post.attachments or [])
    original = file.reference
    if original.id:
        matches = [item for item in candidates if item.id == original.id]
    elif original.name:
        matches = [item for item in candidates if item.name == original.name]
    else:
        return None
    return matches[0] if len(matches) == 1 else None
