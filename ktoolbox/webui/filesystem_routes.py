from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ktoolbox.webui.auth import require_csrf, require_session
from ktoolbox.webui.database import WebUISession
from ktoolbox.webui.event_store import WebUIEventStore
from ktoolbox.webui.filesystem import (
    FilesystemBrowser,
    FilesystemBrowserError,
    FilesystemConflictError,
    FilesystemForbiddenError,
    FilesystemInvalidError,
    FilesystemMode,
    FilesystemNotFoundError,
    FilesystemScope,
)
from ktoolbox.webui.models import (
    FilesystemBrowseResponse,
    FilesystemCreateDirectoryRequest,
    FilesystemDeleteDirectoryRequest,
    FilesystemEntryResponse,
)

SessionDependency = Annotated[WebUISession, Depends(require_session)]
CsrfDependency = Annotated[WebUISession, Depends(require_csrf)]


def create_filesystem_router(browser: FilesystemBrowser, events: WebUIEventStore) -> APIRouter:
    router = APIRouter(prefix="/api/v1/filesystem", tags=["filesystem"])

    @router.get("", response_model=FilesystemBrowseResponse)
    async def browse_filesystem(
        _: SessionDependency,
        scope: FilesystemScope = "project",
        mode: FilesystemMode = "directory",
        path: str | None = None,
        search: str = Query(default="", max_length=256),
        include_hidden: bool = False,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=200),
    ) -> FilesystemBrowseResponse:
        try:
            return await browser.browse(
                scope=scope,
                mode=mode,
                path=path,
                search=search,
                include_hidden=include_hidden,
                offset=offset,
                limit=limit,
            )
        except FilesystemBrowserError as error:
            raise _http_error(error) from error

    @router.post("/directories", response_model=FilesystemEntryResponse, status_code=status.HTTP_201_CREATED)
    async def create_directory(
        payload: FilesystemCreateDirectoryRequest,
        _: CsrfDependency,
    ) -> FilesystemEntryResponse:
        try:
            entry = await browser.create_directory(scope=payload.scope, parent=payload.parent, name=payload.name)
        except FilesystemBrowserError as error:
            raise _http_error(error) from error
        await events.publish(
            "filesystem.changed",
            {"action": "created", "scope": payload.scope, "parent": payload.parent},
            resource="filesystem",
            resource_id=entry.path,
        )
        return entry

    @router.delete("/directories", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_directory(
        payload: FilesystemDeleteDirectoryRequest,
        _: CsrfDependency,
    ) -> None:
        try:
            await browser.delete_directory(scope=payload.scope, path=payload.path)
        except FilesystemBrowserError as error:
            raise _http_error(error) from error
        await events.publish(
            "filesystem.changed",
            {"action": "deleted", "scope": payload.scope},
            resource="filesystem",
            resource_id=payload.path,
        )

    return router


def _http_error(error: FilesystemBrowserError) -> HTTPException:
    if isinstance(error, FilesystemForbiddenError):
        code = status.HTTP_403_FORBIDDEN
    elif isinstance(error, FilesystemNotFoundError):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(error, FilesystemConflictError):
        code = status.HTTP_409_CONFLICT
    elif isinstance(error, FilesystemInvalidError):
        code = status.HTTP_422_UNPROCESSABLE_CONTENT
    else:
        code = status.HTTP_422_UNPROCESSABLE_CONTENT
    return HTTPException(status_code=code, detail={"code": error.code, "message": str(error)})
