from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest

from ktoolbox.configuration import Configuration, RuntimeContext
from ktoolbox.reporting import ProgressReporter
from ktoolbox.webui.app import create_app
from ktoolbox.webui.auth import CSRF_HEADER
from ktoolbox.webui.database import WebUIDatabase
from ktoolbox.webui.project_lock import ProjectAlreadyRunningError
from ktoolbox.webui.task_executor import TaskExecutionSnapshot
from ktoolbox.webui.task_models import DownloadTaskSpec, TaskRecord, TaskStatus
from ktoolbox.webui.task_reporter import WebTaskReporter
from ktoolbox.webui.task_store import TaskStore


class ControlledExecutor:
    def __init__(self) -> None:
        self.started: asyncio.Queue[str] = asyncio.Queue()
        self.release: dict[str, asyncio.Event] = {}
        self.active = 0
        self.peak = 0

    async def __call__(
        self,
        task: TaskRecord,
        snapshot: TaskExecutionSnapshot,
        reporter: ProgressReporter,
    ) -> None:
        assert snapshot.runtime.project_root.exists()
        self.active += 1
        self.peak = max(self.peak, self.active)
        gate = self.release.setdefault(task.id, asyncio.Event())
        reporter.start()
        reporter.job_queued("direct")
        reporter.download_started("file", "direct", "sample.bin", 100, 0)
        reporter.download_advanced("file", 40)
        await self.started.put(task.id)
        try:
            await gate.wait()
            reporter.download_advanced("file", 60)
            reporter.download_finished("file", "completed")
            reporter.stop()
        finally:
            self.active -= 1


@asynccontextmanager
async def task_client(
    tmp_path: Path,
    executor: ControlledExecutor,
    *,
    concurrency: int = 2,
) -> AsyncIterator[tuple[httpx.AsyncClient, dict[str, str]]]:
    (tmp_path / "ktoolbox.toml").write_text("schema_version = 1\n", encoding="utf-8")
    configuration = Configuration(
        _env_file=None,
        webui={
            "username": "owner",
            "password": "secret",
            "max_active_tasks": concurrency,
        },
    )
    app = create_app(RuntimeContext(tmp_path, configuration), task_executor=executor)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 1234))
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            login = await client.post(
                "/api/v1/session/login",
                json={"username": "owner", "password": "secret"},
            )
            yield client, {CSRF_HEADER: login.json()["csrf_token"]}


def task_payload(creator: str, *, output: str = "downloads") -> dict[str, object]:
    return {
        "kind": "download",
        "service": "fanbox",
        "creator_id": creator,
        "post_id": "42",
        "output": output,
    }


async def wait_for_status(client: httpx.AsyncClient, task_id: str, expected: TaskStatus) -> dict[str, object]:
    for _ in range(100):
        response = await client.get(f"/api/v1/tasks/{task_id}")
        body = response.json()
        if body["status"] == expected.value:
            return body
        await asyncio.sleep(0.02)
    raise AssertionError(f"task {task_id} did not reach {expected.value}")


@pytest.mark.asyncio
async def test_task_concurrency_duplicate_blocking_and_resume(tmp_path: Path) -> None:
    executor = ControlledExecutor()
    async with task_client(tmp_path, executor) as (client, headers):
        first_response = await client.post("/api/v1/tasks", json=task_payload("one"), headers=headers)
        first = first_response.json()
        duplicate = await client.post("/api/v1/tasks", json=task_payload("one"), headers=headers)
        second = (await client.post("/api/v1/tasks", json=task_payload("two"), headers=headers)).json()
        blocked = (
            await client.post(
                "/api/v1/tasks",
                json={**task_payload("one"), "post_id": "99"},
                headers=headers,
            )
        ).json()

        assert first_response.status_code == 201
        assert duplicate.status_code == 409
        assert duplicate.json()["detail"]["existing_task_id"] == first["id"]
        await wait_for_status(client, first["id"], TaskStatus.running)
        await wait_for_status(client, second["id"], TaskStatus.running)
        blocked_record = await wait_for_status(client, blocked["id"], TaskStatus.blocked)
        assert blocked_record["blocked_by"] == first["id"]
        assert executor.peak == 2

        paused = await client.post(f"/api/v1/tasks/{first['id']}/pause", headers=headers)
        assert paused.status_code == 200
        await wait_for_status(client, first["id"], TaskStatus.paused)
        await wait_for_status(client, blocked["id"], TaskStatus.running)

        resumed = await client.post(f"/api/v1/tasks/{first['id']}/resume", headers=headers)
        assert resumed.status_code == 200
        assert resumed.json()["status"] == "queued"
        executor.release[blocked["id"]].set()
        await wait_for_status(client, blocked["id"], TaskStatus.completed)
        await wait_for_status(client, first["id"], TaskStatus.running)
        executor.release[first["id"]].set()
        executor.release[second["id"]].set()
        await wait_for_status(client, first["id"], TaskStatus.completed)
        await wait_for_status(client, second["id"], TaskStatus.completed)

        attempts = await client.get(f"/api/v1/tasks/{first['id']}/attempts")
        assert [item["status"] for item in attempts.json()] == ["completed", "paused"]
        events = await client.get(f"/api/v1/tasks/{first['id']}/events", params={"after": 0})
        assert any(item["data"].get("progress", {}).get("transferred_bytes") == 100 for item in events.json())


@pytest.mark.asyncio
async def test_task_output_safety_stop_and_cleanup(tmp_path: Path) -> None:
    executor = ControlledExecutor()
    async with task_client(tmp_path, executor, concurrency=1) as (client, headers):
        outside = await client.post(
            "/api/v1/tasks",
            json=task_payload("outside", output="../outside"),
            headers=headers,
        )
        assert outside.status_code == 422

        task = (await client.post("/api/v1/tasks", json=task_payload("stop"), headers=headers)).json()
        await wait_for_status(client, task["id"], TaskStatus.running)
        stopped = await client.post(f"/api/v1/tasks/{task['id']}/stop", headers=headers)
        assert stopped.json()["status"] == "stop_requested"
        await wait_for_status(client, task["id"], TaskStatus.stopped)

        output = tmp_path / "downloads" / "owned.bin"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"owned")
        store: TaskStore = client._transport.app.state.task_store
        await store.add_artifact(task["id"], output)
        preview = await client.get(f"/api/v1/tasks/{task['id']}/cleanup-preview")
        assert preview.json()["removable_files"] == 1

        missing_confirmation = await client.delete(
            f"/api/v1/tasks/{task['id']}",
            params={"delete_output": True},
            headers=headers,
        )
        assert missing_confirmation.status_code == 422
        deleted = await client.delete(
            f"/api/v1/tasks/{task['id']}",
            params={"delete_output": True, "confirmation": task["id"]},
            headers=headers,
        )
        assert deleted.status_code == 200
        assert not output.exists()


@pytest.mark.asyncio
async def test_recovery_marks_unfinished_attempt_interrupted(tmp_path: Path) -> None:
    database = WebUIDatabase(tmp_path / "webui.sqlite3")
    await database.initialize()
    store = TaskStore(database)
    task = await store.create(DownloadTaskSpec(service="fanbox", creator_id="one", post_id="42", output=tmp_path))
    await store.start_attempt(task, {"environment": {}})
    await store.set_status(task.id, TaskStatus.running)

    assert await store.recover_interrupted() == 1
    assert (await store.get(task.id)).status is TaskStatus.interrupted
    assert (await store.attempts(task.id))[0].status is TaskStatus.interrupted


@pytest.mark.asyncio
async def test_web_reporter_persists_throttled_speed_progress(tmp_path: Path) -> None:
    database = WebUIDatabase(tmp_path / "webui.sqlite3")
    await database.initialize()
    store = TaskStore(database)
    task = await store.create(DownloadTaskSpec(service="fanbox", creator_id="one", post_id="42", output=tmp_path))
    reporter = WebTaskReporter(task.id, store, flush_interval=0.01)
    reporter.download_started("one", "fanbox:one", "sample.bin", 100, 0)
    reporter.download_advanced("one", 25)
    await asyncio.sleep(0.03)

    events = await store.events(task_id=task.id)
    assert any(event.event_type == "download.progress" for event in events)
    progress = (await store.get(task.id)).progress
    assert progress.transferred_bytes == 25
    assert progress.speed_bps > 0
    assert progress.eta_seconds is not None

    reporter.download_finished("one", "completed")
    await reporter.close()
    settled = (await store.get(task.id)).progress
    assert settled.speed_bps == 0
    assert settled.eta_seconds == 0


@pytest.mark.asyncio
async def test_project_lock_rejects_a_second_scheduler(tmp_path: Path) -> None:
    configuration = Configuration(
        _env_file=None,
        webui={"username": "owner", "password": "secret"},
    )
    context = RuntimeContext(tmp_path, configuration)
    first = create_app(context, task_executor=ControlledExecutor())
    second = create_app(context, task_executor=ControlledExecutor())

    async with first.router.lifespan_context(first):
        with pytest.raises(ProjectAlreadyRunningError):
            async with second.router.lifespan_context(second):
                pass
