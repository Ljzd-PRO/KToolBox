from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Coroutine
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Literal, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from ktoolbox.project_config import ProjectConfigError, ProjectConfigStore
from ktoolbox.utils import parse_webpage_url
from ktoolbox.webui.auth import require_csrf, require_session
from ktoolbox.webui.database import WebUISession
from ktoolbox.webui.event_store import WebUIEventStore
from ktoolbox.webui.task_models import (
    DownloadTaskSpec,
    SyncTaskSpec,
    TaskAttempt,
    TaskCleanupPreview,
    TaskCreateRequest,
    TaskEvent,
    TaskPresentationSnapshot,
    TaskRecord,
    TaskSpec,
    TaskUpdateRequest,
    task_target_key,
    validate_task_presentation,
)
from ktoolbox.webui.task_scheduler import TaskScheduler
from ktoolbox.webui.task_store import (
    DuplicateTaskError,
    InvalidTaskStateError,
    TaskNotFoundError,
    TaskStore,
)


def task_store(request: Request) -> TaskStore:
    return cast(TaskStore, request.app.state.task_store)


def task_scheduler(request: Request) -> TaskScheduler:
    return cast(TaskScheduler, request.app.state.task_scheduler)


def event_store(request: Request) -> WebUIEventStore:
    return cast(WebUIEventStore, request.app.state.event_store)


def create_task_router(project_root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["tasks"])

    @router.get("/tasks", response_model=list[TaskRecord])
    async def list_tasks(
        _: Annotated[WebUISession, Depends(require_session)],
        store: Annotated[TaskStore, Depends(task_store)],
    ) -> list[TaskRecord]:
        return await store.list_tasks()

    @router.post("/tasks", response_model=TaskRecord, status_code=status.HTTP_201_CREATED)
    async def create_task(
        payload: TaskCreateRequest,
        _: Annotated[WebUISession, Depends(require_csrf)],
        scheduler: Annotated[TaskScheduler, Depends(task_scheduler)],
    ) -> TaskRecord:
        spec = await asyncio.to_thread(_normalize_spec, payload.spec, project_root)
        presentation = validate_task_presentation(spec, payload.presentation)
        try:
            return await scheduler.create(spec, presentation)
        except DuplicateTaskError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": str(error), "existing_task_id": error.task_id},
            ) from error

    @router.get("/tasks/{task_id}", response_model=TaskRecord)
    async def get_task(
        task_id: str,
        _: Annotated[WebUISession, Depends(require_session)],
        store: Annotated[TaskStore, Depends(task_store)],
    ) -> TaskRecord:
        return await _task_or_404(store, task_id)

    @router.patch("/tasks/{task_id}", response_model=TaskRecord)
    async def update_task(
        task_id: str,
        payload: TaskUpdateRequest,
        _: Annotated[WebUISession, Depends(require_csrf)],
        scheduler: Annotated[TaskScheduler, Depends(task_scheduler)],
        store: Annotated[TaskStore, Depends(task_store)],
    ) -> TaskRecord:
        spec = await asyncio.to_thread(_normalize_spec, payload.spec, project_root)
        current = await _task_or_404(store, task_id)
        presentation = _updated_presentation(current, spec, payload)
        return await _state_action(scheduler.update(task_id, spec, presentation))

    @router.post("/tasks/{task_id}/pause", response_model=TaskRecord)
    async def pause_task(
        task_id: str,
        _: Annotated[WebUISession, Depends(require_csrf)],
        scheduler: Annotated[TaskScheduler, Depends(task_scheduler)],
    ) -> TaskRecord:
        return await _state_action(scheduler.pause(task_id))

    @router.post("/tasks/{task_id}/stop", response_model=TaskRecord)
    async def stop_task(
        task_id: str,
        _: Annotated[WebUISession, Depends(require_csrf)],
        scheduler: Annotated[TaskScheduler, Depends(task_scheduler)],
    ) -> TaskRecord:
        return await _state_action(scheduler.stop_task(task_id))

    @router.post("/tasks/{task_id}/resume", response_model=TaskRecord)
    async def resume_task(
        task_id: str,
        _: Annotated[WebUISession, Depends(require_csrf)],
        scheduler: Annotated[TaskScheduler, Depends(task_scheduler)],
    ) -> TaskRecord:
        return await _state_action(scheduler.resume(task_id))

    @router.get("/tasks/{task_id}/attempts", response_model=list[TaskAttempt])
    async def task_attempts(
        task_id: str,
        _: Annotated[WebUISession, Depends(require_session)],
        store: Annotated[TaskStore, Depends(task_store)],
    ) -> list[TaskAttempt]:
        try:
            return await store.attempts(task_id)
        except TaskNotFoundError as error:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found") from error

    @router.get("/tasks/{task_id}/events", response_model=list[TaskEvent])
    async def task_events(
        task_id: str,
        _: Annotated[WebUISession, Depends(require_session)],
        store: Annotated[TaskStore, Depends(task_store)],
        after: Annotated[int, Query(ge=0)] = 0,
        view: Annotated[Literal["activity", "transfers", "all"], Query()] = "all",
        limit: Annotated[int, Query(ge=1, le=200)] = 200,
    ) -> list[TaskEvent]:
        await _task_or_404(store, task_id)
        return await store.events(
            after=after,
            task_id=task_id,
            view=view,
            limit=limit,
        )

    @router.get("/tasks/{task_id}/cleanup-preview", response_model=TaskCleanupPreview)
    async def cleanup_preview(
        task_id: str,
        _: Annotated[WebUISession, Depends(require_session)],
        store: Annotated[TaskStore, Depends(task_store)],
    ) -> TaskCleanupPreview:
        try:
            return await store.cleanup_preview(task_id)
        except TaskNotFoundError as error:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found") from error

    @router.delete("/tasks/{task_id}", response_model=TaskCleanupPreview)
    async def delete_task(
        task_id: str,
        _: Annotated[WebUISession, Depends(require_csrf)],
        store: Annotated[TaskStore, Depends(task_store)],
        delete_output: bool = False,
        confirmation: str | None = None,
    ) -> TaskCleanupPreview:
        if delete_output and confirmation != task_id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "confirm output deletion with the exact task ID",
            )
        try:
            return await store.delete(task_id, delete_output=delete_output)
        except TaskNotFoundError as error:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found") from error
        except InvalidTaskStateError as error:
            raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error

    @router.get("/events")
    async def event_stream(
        request: Request,
        _: Annotated[WebUISession, Depends(require_session)],
        events_store: Annotated[WebUIEventStore, Depends(event_store)],
        last_event_id: Annotated[str | None, Header()] = None,
        after: Annotated[int | None, Query(ge=0)] = None,
    ) -> StreamingResponse:
        try:
            if last_event_id is not None:
                cursor = max(after or 0, int(last_event_id))
            elif after is not None:
                cursor = after
            else:
                cursor = await events_store.latest_id()
        except ValueError as error:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid Last-Event-ID") from error

        async def events() -> AsyncIterator[str]:
            nonlocal cursor
            yield "retry: 3000\n\n"
            while not await request.is_disconnected():
                records = await events_store.wait_for_events(after=cursor, timeout=15.0)
                if records:
                    for record in records:
                        cursor = record.id
                        payload = record.model_dump_json()
                        yield f"id: {record.id}\nevent: {record.event_type}\ndata: {payload}\n\n"
                else:
                    payload = json.dumps(
                        {"timestamp": datetime.now(timezone.utc).isoformat()},
                        separators=(",", ":"),
                    )
                    yield f"event: heartbeat\ndata: {payload}\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")

    return router


async def _task_or_404(store: TaskStore, task_id: str) -> TaskRecord:
    try:
        return await store.get(task_id)
    except TaskNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found") from error


async def _state_action(operation: Coroutine[Any, Any, TaskRecord]) -> TaskRecord:
    try:
        return await operation
    except TaskNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found") from error
    except DuplicateTaskError as error:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"message": str(error), "existing_task_id": error.task_id},
        ) from error
    except InvalidTaskStateError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


def _updated_presentation(
    current: TaskRecord,
    spec: TaskSpec,
    payload: TaskUpdateRequest,
) -> TaskPresentationSnapshot | None:
    if "presentation" in payload.model_fields_set:
        return validate_task_presentation(spec, payload.presentation)
    if task_target_key(current.spec) == task_target_key(spec):
        return current.presentation
    return None


def _normalize_spec(spec: TaskSpec, project_root: Path) -> TaskSpec:
    output = spec.output.expanduser()
    if not output.is_absolute():
        output = project_root / output
    output = output.resolve()
    root = project_root.resolve()
    if output != root and root not in output.parents:
        raise ValueError("task output must stay inside the project directory")
    normalized = spec.model_copy(update={"output": output})
    if isinstance(normalized, SyncTaskSpec) and not normalized.creators:
        try:
            project = ProjectConfigStore(root / "ktoolbox.toml").load()
        except ProjectConfigError:
            raise
        creators = [creator.model_copy(deep=True) for creator in project.creators if creator.enabled]
        if not creators:
            raise ValueError("no enabled creators are configured")
        normalized = normalized.model_copy(update={"creators": creators})
    if isinstance(normalized, DownloadTaskSpec) and normalized.post:
        service, creator_id, post_id, _ = parse_webpage_url(normalized.post)
        if not service or not creator_id or not post_id:
            raise ValueError("the post URL does not contain a service, creator, and post ID")
    return normalized
