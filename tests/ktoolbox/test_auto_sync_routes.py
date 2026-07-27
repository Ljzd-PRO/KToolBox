from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx

from ktoolbox.configuration import Configuration, RuntimeContext
from ktoolbox.project_config import CreatorReference, ProjectConfigStore, ProjectConfiguration
from ktoolbox.reporting import ProgressReporter
from ktoolbox.webui.app import create_app
from ktoolbox.webui.auth import CSRF_HEADER
from ktoolbox.webui.task_executor import TaskExecutionSnapshot
from ktoolbox.webui.task_models import TaskRecord


class HoldingExecutor:
    def __init__(self) -> None:
        self.release = asyncio.Event()

    async def __call__(
        self,
        task: TaskRecord,
        snapshot: TaskExecutionSnapshot,
        reporter: ProgressReporter,
    ) -> None:
        await self.release.wait()


@asynccontextmanager
async def automatic_client(tmp_path: Path) -> AsyncIterator[tuple[httpx.AsyncClient, dict[str, str]]]:
    ProjectConfigStore(tmp_path / "ktoolbox.toml").save(
        ProjectConfiguration(
            creators=[CreatorReference(service="fanbox", creator_id="creator")],
        )
    )
    configuration = Configuration(
        _env_file=None,
        webui={
            "username": "owner",
            "password": "secret",
            "max_active_tasks": 1,
        },
    )
    executor = HoldingExecutor()
    app = create_app(RuntimeContext(tmp_path, configuration), task_executor=executor)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 1234))
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            login = await client.post(
                "/api/v1/session/login",
                json={"username": "owner", "password": "secret"},
            )
            yield client, {CSRF_HEADER: login.json()["csrf_token"]}


def plan_payload() -> dict[str, object]:
    return {
        "id": "daily",
        "name": "Daily sync",
        "enabled": True,
        "creators": ["fanbox:creator"],
        "schedule": {
            "kind": "cron",
            "expression": "0 3 * * *",
            "timezone": "Asia/Shanghai",
        },
        "initial_start_date": "2026-07-01",
        "options": {
            "output": "downloads",
            "save_creator_indices": True,
            "mix_posts": None,
            "keywords": [],
            "keywords_exclude": [],
        },
    }


async def test_automatic_sync_plan_crud_run_conflict_and_history(tmp_path: Path) -> None:
    async with automatic_client(tmp_path) as (client, csrf):
        listed = await client.get("/api/v1/auto-sync/plans")
        assert listed.status_code == 200
        assert listed.json()["plans"] == []
        etag = listed.headers["etag"]

        missing_precondition = await client.post(
            "/api/v1/auto-sync/plans",
            headers=csrf,
            json=plan_payload(),
        )
        assert missing_precondition.status_code == 428

        created = await client.post(
            "/api/v1/auto-sync/plans",
            headers={**csrf, "If-Match": etag},
            json=plan_payload(),
        )
        assert created.status_code == 201
        assert created.json()["plans"][0]["name"] == "Daily sync"
        assert created.json()["next_runs"]["daily"] is not None
        etag = created.headers["etag"]

        stale = await client.post(
            "/api/v1/auto-sync/plans/daily/pause",
            headers={**csrf, "If-Match": '"stale"'},
        )
        assert stale.status_code == 409

        paused = await client.post(
            "/api/v1/auto-sync/plans/daily/pause",
            headers={**csrf, "If-Match": etag},
        )
        assert paused.status_code == 200
        assert paused.json()["plans"][0]["enabled"] is False
        etag = paused.headers["etag"]

        resumed = await client.post(
            "/api/v1/auto-sync/plans/daily/resume",
            headers={**csrf, "If-Match": etag},
        )
        assert resumed.status_code == 200
        assert resumed.json()["plans"][0]["enabled"] is True

        run = await client.post("/api/v1/auto-sync/plans/daily/run", headers=csrf)
        assert run.status_code == 200
        task_id = run.json()["task_id"]
        duplicate = await client.post("/api/v1/auto-sync/plans/daily/run", headers=csrf)
        assert duplicate.status_code == 409
        assert duplicate.json()["detail"]["current_task_id"] == task_id

        task = await client.get(f"/api/v1/tasks/{task_id}")
        assert task.json()["automatic_origin"]["plan_id"] == "daily"
        edit = await client.patch(
            f"/api/v1/tasks/{task_id}",
            headers=csrf,
            json={"spec": task.json()["spec"]},
        )
        assert edit.status_code == 409

        runs = await client.get("/api/v1/auto-sync/runs")
        assert runs.status_code == 200
        assert runs.json()[0]["task_id"] == task_id
        updates = await client.get(
            "/api/v1/auto-sync/updates",
            params={"period": "today", "timezone": "Asia/Shanghai"},
        )
        assert updates.status_code == 200
        assert updates.json() == []
        invalid_timezone = await client.get(
            "/api/v1/auto-sync/updates",
            params={"period": "today", "timezone": "Not/AZone"},
        )
        assert invalid_timezone.status_code == 422
        invalid_period = await client.get(
            "/api/v1/auto-sync/updates",
            params={"period": "90d", "timezone": "UTC"},
        )
        assert invalid_period.status_code == 422

        creator_delete = await client.delete("/api/v1/creators/fanbox/creator", headers=csrf)
        assert creator_delete.status_code == 409


async def test_automatic_sync_mcp_surface_is_curated(tmp_path: Path) -> None:
    async with automatic_client(tmp_path) as (client, _):
        tools = (await client.get("/api/v1/mcp/tools")).json()
        operation_ids = {tool["operation_id"] for tool in tools}

    assert {
        "list_automatic_sync_plans",
        "get_automatic_sync_plan",
        "list_automatic_sync_runs",
        "list_automatic_sync_updates",
        "pause_automatic_sync_plan",
        "resume_automatic_sync_plan",
        "run_automatic_sync_plan",
    } <= operation_ids
    assert {
        "create_automatic_sync_plan",
        "update_automatic_sync_plan",
        "delete_automatic_sync_plan",
    }.isdisjoint(operation_ids)
