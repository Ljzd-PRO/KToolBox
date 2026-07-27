from __future__ import annotations

from pathlib import Path
from typing import Annotated, cast
from zoneinfo import ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status

from ktoolbox.project_config import AutomaticSyncPlan, ProjectConfigError, ProjectConfigStore
from ktoolbox.webui.auth import require_csrf, require_session
from ktoolbox.webui.auto_sync_models import (
    AutomaticSyncPlanListResponse,
    AutomaticSyncRunNowResponse,
    AutomaticSyncRunRecord,
    AutomaticSyncUpdateRange,
    AutomaticSyncUpdateSummary,
)
from ktoolbox.webui.auto_sync_scheduler import AutomaticSyncConflictError, AutoSyncScheduler
from ktoolbox.webui.auto_sync_store import AutomaticSyncStore, update_range_start
from ktoolbox.webui.config_monitor import ConfigurationChangeMonitor
from ktoolbox.webui.config_store import content_revision
from ktoolbox.webui.database import WebUISession, utc_now
from ktoolbox.webui.event_store import WebUIEventStore

SessionDependency = Annotated[WebUISession, Depends(require_session)]
CsrfDependency = Annotated[WebUISession, Depends(require_csrf)]
IfMatch = Annotated[str | None, Header(alias="If-Match")]


def create_auto_sync_router(project_root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/auto-sync", tags=["automatic-sync"])
    project_store = ProjectConfigStore(project_root / "ktoolbox.toml")

    def scheduler(request: Request) -> AutoSyncScheduler:
        return cast(AutoSyncScheduler, request.app.state.automatic_sync_scheduler)

    def automatic_store(request: Request) -> AutomaticSyncStore:
        return cast(AutomaticSyncStore, request.app.state.automatic_sync_store)

    def events(request: Request) -> WebUIEventStore:
        return cast(WebUIEventStore, request.app.state.event_store)

    def config_monitor(request: Request) -> ConfigurationChangeMonitor:
        return cast(ConfigurationChangeMonitor, request.app.state.config_monitor)

    def require_revision(value: str | None) -> str:
        if value is None:
            raise HTTPException(status_code=status.HTTP_428_PRECONDITION_REQUIRED, detail="If-Match is required")
        return value.strip().strip('"')

    def assert_revision(value: str | None) -> None:
        if content_revision(project_store.load_text()) != require_revision(value):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="ktoolbox.toml changed since the automatic sync plans were loaded",
            )

    async def publish_change(
        request: Request,
        *,
        action: str,
        plan_id: str,
    ) -> str:
        revision = content_revision(project_store.load_text())
        monitor = config_monitor(request)
        monitor.acknowledge("project", revision)
        await monitor.publish_change("project", revision, source="webui")
        await events(request).publish(
            "auto_sync.plans.changed",
            {"action": action, "revision": revision},
            resource="auto_sync",
            resource_id=plan_id,
        )
        await scheduler(request).reload()
        return revision

    def response(
        request: Request,
        response_value: Response,
    ) -> AutomaticSyncPlanListResponse:
        configuration = project_store.load()
        revision = content_revision(project_store.load_text())
        response_value.headers["ETag"] = f'"{revision}"'
        active_scheduler = scheduler(request)
        return AutomaticSyncPlanListResponse(
            plans=configuration.automatic_sync,
            revision=revision,
            next_runs={plan.id: active_scheduler.next_run_at(plan.id) for plan in configuration.automatic_sync},
        )

    @router.get("/plans", response_model=AutomaticSyncPlanListResponse)
    async def list_automatic_sync_plans(
        request: Request,
        response_value: Response,
        _: SessionDependency,
    ) -> AutomaticSyncPlanListResponse:
        return response(request, response_value)

    @router.post("/plans", response_model=AutomaticSyncPlanListResponse, status_code=status.HTTP_201_CREATED)
    async def create_automatic_sync_plan(
        plan: AutomaticSyncPlan,
        request: Request,
        response_value: Response,
        _: CsrfDependency,
        if_match: IfMatch = None,
    ) -> AutomaticSyncPlanListResponse:
        assert_revision(if_match)
        try:
            project_store.add_automatic_sync_plan(plan)
        except ProjectConfigError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
        await publish_change(request, action="created", plan_id=plan.id)
        return response(request, response_value)

    @router.get("/plans/{plan_id}", response_model=AutomaticSyncPlan)
    async def get_automatic_sync_plan(plan_id: str, _: SessionDependency) -> AutomaticSyncPlan:
        return _find_plan(project_store, plan_id)

    @router.put("/plans/{plan_id}", response_model=AutomaticSyncPlanListResponse)
    async def update_automatic_sync_plan(
        plan_id: str,
        plan: AutomaticSyncPlan,
        request: Request,
        response_value: Response,
        _: CsrfDependency,
        if_match: IfMatch = None,
    ) -> AutomaticSyncPlanListResponse:
        assert_revision(if_match)
        try:
            project_store.update_automatic_sync_plan(plan_id, plan)
        except ProjectConfigError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
        await publish_change(request, action="updated", plan_id=plan_id)
        return response(request, response_value)

    @router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_automatic_sync_plan(
        plan_id: str,
        request: Request,
        _: CsrfDependency,
        if_match: IfMatch = None,
    ) -> Response:
        assert_revision(if_match)
        try:
            project_store.remove_automatic_sync_plan(plan_id)
        except ProjectConfigError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        await automatic_store(request).delete_plan_state(plan_id)
        await publish_change(request, action="deleted", plan_id=plan_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.post("/plans/{plan_id}/pause", response_model=AutomaticSyncPlanListResponse)
    async def pause_automatic_sync_plan(
        plan_id: str,
        request: Request,
        response_value: Response,
        _: CsrfDependency,
        if_match: IfMatch = None,
    ) -> AutomaticSyncPlanListResponse:
        assert_revision(if_match)
        try:
            project_store.set_automatic_sync_plan_enabled(plan_id, False)
        except ProjectConfigError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        await publish_change(request, action="paused", plan_id=plan_id)
        return response(request, response_value)

    @router.post("/plans/{plan_id}/resume", response_model=AutomaticSyncPlanListResponse)
    async def resume_automatic_sync_plan(
        plan_id: str,
        request: Request,
        response_value: Response,
        _: CsrfDependency,
        if_match: IfMatch = None,
    ) -> AutomaticSyncPlanListResponse:
        assert_revision(if_match)
        try:
            project_store.set_automatic_sync_plan_enabled(plan_id, True)
        except ProjectConfigError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        await publish_change(request, action="resumed", plan_id=plan_id)
        return response(request, response_value)

    @router.post("/plans/{plan_id}/run", response_model=AutomaticSyncRunNowResponse)
    async def run_automatic_sync_plan(
        plan_id: str,
        request: Request,
        _: CsrfDependency,
    ) -> AutomaticSyncRunNowResponse:
        try:
            task_id = await scheduler(request).run_now(plan_id)
        except AutomaticSyncConflictError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": str(error), "current_task_id": error.task_id},
            ) from error
        except LookupError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        return AutomaticSyncRunNowResponse(task_id=task_id)

    @router.get("/runs", response_model=list[AutomaticSyncRunRecord])
    async def list_automatic_sync_runs(
        request: Request,
        _: SessionDependency,
        limit: Annotated[int, Query(ge=1, le=200)] = 100,
    ) -> list[AutomaticSyncRunRecord]:
        return await automatic_store(request).list_runs(limit=limit)

    @router.get("/updates", response_model=list[AutomaticSyncUpdateSummary])
    async def list_automatic_sync_updates(
        request: Request,
        _: SessionDependency,
        period: AutomaticSyncUpdateRange = "30d",
        timezone: Annotated[str, Query(min_length=1, max_length=128)] = "UTC",
    ) -> list[AutomaticSyncUpdateSummary]:
        try:
            since = update_range_start(period, now=utc_now(), timezone_name=timezone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="invalid IANA time zone",
            ) from error
        return await automatic_store(request).recent_updates(since=since)

    return router


def _find_plan(store: ProjectConfigStore, plan_id: str) -> AutomaticSyncPlan:
    normalized = plan_id.casefold()
    for plan in store.load().automatic_sync:
        if plan.id.casefold() == normalized:
            return plan
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="automatic sync plan not found")
