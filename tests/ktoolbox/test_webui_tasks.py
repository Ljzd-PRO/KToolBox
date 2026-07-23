from __future__ import annotations

import asyncio
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest

from ktoolbox.configuration import Configuration, RuntimeContext
from ktoolbox.failures import FailureCode, FailureStage, generic_failure
from ktoolbox.project_config import CreatorReference
from ktoolbox.reporting import ProgressReporter
from ktoolbox.webui.app import create_app
from ktoolbox.webui.auth import CSRF_HEADER
from ktoolbox.webui.database import WebUIDatabase
from ktoolbox.webui.project_lock import ProjectAlreadyRunningError
from ktoolbox.webui.task_executor import TaskExecutionSnapshot
from ktoolbox.webui.task_models import (
    DownloadTaskSpec,
    SyncTaskSpec,
    TaskPresentationSnapshot,
    TaskRecord,
    TaskStatus,
    task_target_key,
)
from ktoolbox.webui.task_reporter import WebTaskReporter
from ktoolbox.webui.task_scheduler import (
    TaskResources,
    TaskScheduler,
    _error_text,
    _load_snapshot,
    task_resources,
)
from ktoolbox.webui.task_store import InvalidTaskStateError, TaskStore


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


def task_payload(
    creator: str,
    *,
    output: str = "downloads",
    post_id: str = "42",
    presentation: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "spec": {
            "kind": "download",
            "service": "fanbox",
            "creator_id": creator,
            "post_id": post_id,
            "output": output,
        }
    }
    if presentation is not None:
        payload["presentation"] = presentation
    return payload


async def wait_for_status(client: httpx.AsyncClient, task_id: str, expected: TaskStatus) -> dict[str, object]:
    for _ in range(100):
        response = await client.get(f"/api/v1/tasks/{task_id}")
        body = response.json()
        if body["status"] == expected.value:
            return body
        await asyncio.sleep(0.02)
    raise AssertionError(f"task {task_id} did not reach {expected.value}")


async def scheduler_parts(
    tmp_path: Path,
    executor,
    *,
    concurrency: int = 1,
) -> tuple[TaskScheduler, TaskStore]:
    (tmp_path / "ktoolbox.toml").write_text("schema_version = 1\n", encoding="utf-8")
    database = WebUIDatabase(tmp_path / "scheduler.sqlite3")
    await database.initialize()
    store = TaskStore(database)
    context = RuntimeContext(
        tmp_path,
        Configuration(_env_file=None, webui={"username": "owner", "password": "secret"}),
    )
    return TaskScheduler(context, store, max_concurrency=concurrency, executor=executor), store


async def wait_for_store_status(
    scheduler: TaskScheduler,
    store: TaskStore,
    task_id: str,
    status: TaskStatus,
) -> TaskRecord:
    for _ in range(100):
        record = await store.get(task_id)
        if record.status is status and task_id not in scheduler._running:
            return record
        await asyncio.sleep(0.01)
    raise AssertionError(f"task {task_id} did not settle as {status.value}")


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
                json=task_payload("one", post_id="99"),
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
async def test_task_presentation_round_trip_validation_and_update_semantics(tmp_path: Path) -> None:
    executor = ControlledExecutor()
    target_key = "download/fanbox/one/42/"
    presentation = {
        "target_key": target_key,
        "title": "Fictional project study",
        "creator_name": "Demo Studio",
    }
    async with task_client(tmp_path, executor, concurrency=1) as (client, headers):
        created_response = await client.post(
            "/api/v1/tasks",
            json=task_payload("one", presentation=presentation),
            headers=headers,
        )
        assert created_response.status_code == 201
        created = created_response.json()
        assert created["presentation"] == presentation

        duplicate = await client.post(
            "/api/v1/tasks",
            json=task_payload(
                "one",
                presentation={**presentation, "title": "A different display title"},
            ),
            headers=headers,
        )
        assert duplicate.status_code == 409

        invalid = await client.post(
            "/api/v1/tasks",
            json=task_payload(
                "other",
                presentation={**presentation, "target_key": "download/fanbox/wrong/42/"},
            ),
            headers=headers,
        )
        assert invalid.status_code == 422

        await wait_for_status(client, created["id"], TaskStatus.running)
        await client.post(f"/api/v1/tasks/{created['id']}/pause", headers=headers)
        paused = await wait_for_status(client, created["id"], TaskStatus.paused)

        preserved = await client.patch(
            f"/api/v1/tasks/{created['id']}",
            json={"spec": paused["spec"]},
            headers=headers,
        )
        assert preserved.status_code == 200
        assert preserved.json()["presentation"] == presentation

        changed_spec = {**preserved.json()["spec"], "post_id": "43"}
        cleared = await client.patch(
            f"/api/v1/tasks/{created['id']}",
            json={"spec": changed_spec},
            headers=headers,
        )
        assert cleared.status_code == 200
        assert cleared.json()["presentation"] is None


@pytest.mark.asyncio
async def test_task_presentation_database_migration_and_store_round_trip(tmp_path: Path) -> None:
    database_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE tasks (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                spec_json TEXT NOT NULL,
                position INTEGER NOT NULL,
                revision INTEGER NOT NULL DEFAULT 1,
                progress_json TEXT NOT NULL DEFAULT '{}',
                error TEXT,
                blocked_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

    database = WebUIDatabase(database_path)
    await database.initialize()
    async with database.connect() as connection:
        cursor = await connection.execute("PRAGMA table_info(tasks)")
        columns = {str(row[1]) for row in await cursor.fetchall()}
        await cursor.close()
        cursor = await connection.execute("SELECT version FROM schema_migrations ORDER BY version")
        versions = [int(row[0]) for row in await cursor.fetchall()]
        await cursor.close()
    assert {"presentation_json", "failure_json"} <= columns
    async with database.connect() as connection:
        cursor = await connection.execute("PRAGMA table_info(task_attempts)")
        attempt_columns = {str(row[1]) for row in await cursor.fetchall()}
        await cursor.close()
    assert "failure_json" in attempt_columns
    assert versions == [1, 2, 3, 4, 5, 6]

    store = TaskStore(database)
    spec = DownloadTaskSpec(service="FanBox", creator_id="creator/id", post_id="42", output=tmp_path)
    assert task_target_key(spec) == "download/fanbox/creator%2Fid/42/"
    presentation = TaskPresentationSnapshot(
        target_key=task_target_key(spec) or "",
        title="Fictional title",
        creator_name="Demo Studio",
    )
    task = await store.create(spec, presentation)
    assert task.presentation == presentation


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
async def test_web_reporter_persists_structured_creator_and_file_failures(tmp_path: Path) -> None:
    database = WebUIDatabase(tmp_path / "webui.sqlite3")
    await database.initialize()
    store = TaskStore(database)
    task = await store.create(DownloadTaskSpec(service="fanbox", creator_id="one", post_id="42", output=tmp_path))
    reporter = WebTaskReporter(task.id, store)
    creator_failure = generic_failure(
        stage=FailureStage.work_list,
        message="Work list failed",
        platform="fanbox",
        creator_id="one",
    )
    file_failure = generic_failure(
        stage=FailureStage.file_request,
        message="File request failed",
        file_name="sample.bin",
    )

    reporter.creator_started("fanbox:one")
    reporter.creator_finished("fanbox:one", creator_failure.message, creator_failure)
    reporter.download_started("one", "fanbox:one", "sample.bin", 100, 0)
    reporter.download_finished("one", "failed", file_failure)
    await reporter.close()

    events = await store.events(task_id=task.id)
    creator_event = next(event for event in events if event.event_type == "creator.finished")
    download_event = next(event for event in events if event.event_type == "download.finished")
    assert creator_event.data["failure"]["stage"] == FailureStage.work_list.value
    assert download_event.data["failure"]["file_name"] == "sample.bin"


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


def test_task_resource_conflicts_identity_forms_and_error_text(tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    base = TaskResources(shared, frozenset({"fanbox:one"}), frozenset({"fanbox:one:42"}))
    assert base.conflicts_with(TaskResources(tmp_path / "other", base.creators, base.posts)) is False
    assert base.conflicts_with(TaskResources(shared, frozenset(), base.posts)) is True
    assert base.conflicts_with(TaskResources(shared, base.creators, frozenset())) is True
    assert base.conflicts_with(TaskResources(shared, frozenset({"fanbox:two"}), frozenset())) is False

    sync = task_resources(
        SyncTaskSpec(
            creators=[CreatorReference(service="FanBox", creator_id="One")],
            output=shared,
        )
    )
    assert sync.creators == frozenset({"fanbox:one"})
    assert sync.posts == frozenset()

    url = task_resources(DownloadTaskSpec(post="https://pawchive.pw/fanbox/user/One/post/42", output=shared))
    assert url.creators == frozenset({"fanbox:one"})
    assert url.posts == frozenset({"fanbox:one:42"})

    no_identity = DownloadTaskSpec.model_construct(
        post=None,
        service=None,
        creator_id=None,
        post_id=None,
        output=shared,
    )
    assert task_resources(no_identity).creators == frozenset()
    no_post = DownloadTaskSpec.model_construct(
        post=None,
        service="fanbox",
        creator_id="one",
        post_id=None,
        output=shared,
    )
    assert task_resources(no_post).posts == frozenset()

    assert _error_text(RuntimeError()) == "RuntimeError"
    assert len(_error_text(RuntimeError("x" * 3000))) == 2000


@pytest.mark.asyncio
async def test_scheduler_control_methods_and_validation(tmp_path: Path) -> None:
    executor = ControlledExecutor()
    scheduler, store = await scheduler_parts(tmp_path, executor)
    with pytest.raises(ValueError, match="concurrency"):
        TaskScheduler(scheduler.context, store, max_concurrency=0, executor=executor)

    task = await scheduler.create(
        DownloadTaskSpec(service="fanbox", creator_id="one", post_id="42", output=tmp_path / "one")
    )
    updated = await scheduler.update(
        task.id,
        DownloadTaskSpec(service="fanbox", creator_id="one", post_id="43", output=tmp_path / "one"),
    )
    assert updated.revision == task.revision + 1
    assert (await scheduler.reorder(task.id, 9)).position == 9
    assert (await scheduler.pause(task.id)).status is TaskStatus.paused
    assert (await scheduler.stop_task(task.id)).status is TaskStatus.stopped
    assert (await scheduler.resume(task.id)).status is TaskStatus.queued
    with pytest.raises(InvalidTaskStateError, match="cannot be resumed"):
        await scheduler.resume(task.id)

    await store.set_status(task.id, TaskStatus.completed)
    with pytest.raises(InvalidTaskStateError, match="only queued"):
        await scheduler.pause(task.id)
    with pytest.raises(InvalidTaskStateError, match="cannot be stopped"):
        await scheduler.stop_task(task.id)
    await store.set_status(task.id, TaskStatus.running)
    with pytest.raises(InvalidTaskStateError, match="before reordering"):
        await scheduler.reorder(task.id, 1)
    await scheduler.stop()


@pytest.mark.asyncio
async def test_scheduler_start_is_idempotent_and_dispatch_timeout(tmp_path: Path) -> None:
    scheduler, _ = await scheduler_parts(tmp_path, ControlledExecutor())
    await scheduler.start()
    dispatch_task = scheduler._dispatch_task
    await scheduler.start()
    assert scheduler._dispatch_task is dispatch_task
    await asyncio.sleep(0.3)
    await scheduler.stop()
    await scheduler.stop()


@pytest.mark.asyncio
async def test_scheduler_dispatches_fairly_across_conflicts_and_capacity(tmp_path: Path) -> None:
    executor = ControlledExecutor()
    scheduler, store = await scheduler_parts(tmp_path, executor, concurrency=1)
    first = await store.create(
        DownloadTaskSpec(service="fanbox", creator_id="one", post_id="42", output=tmp_path / "one")
    )
    second = await store.create(
        DownloadTaskSpec(service="fanbox", creator_id="two", post_id="42", output=tmp_path / "two")
    )
    conflict = await store.create(
        DownloadTaskSpec(service="fanbox", creator_id="one", post_id="99", output=tmp_path / "one")
    )

    await scheduler._dispatch_ready_tasks()
    assert await executor.started.get() == first.id
    assert (await store.get(second.id)).status is TaskStatus.queued
    blocked = await store.get(conflict.id)
    assert blocked.status is TaskStatus.blocked
    assert blocked.blocked_by == first.id
    await scheduler._dispatch_ready_tasks()
    assert (await store.get(conflict.id)).blocked_by == first.id

    executor.release[first.id].set()
    await wait_for_store_status(scheduler, store, first.id, TaskStatus.completed)
    await scheduler._dispatch_ready_tasks()
    assert await executor.started.get() == second.id
    assert (await store.get(conflict.id)).status is TaskStatus.queued

    executor.release[second.id].set()
    await wait_for_store_status(scheduler, store, second.id, TaskStatus.completed)
    await scheduler._dispatch_ready_tasks()
    assert await executor.started.get() == conflict.id
    executor.release[conflict.id].set()
    await wait_for_store_status(scheduler, store, conflict.id, TaskStatus.completed)

    scheduler._stopping = True
    await scheduler._dispatch_ready_tasks()


@pytest.mark.asyncio
async def test_scheduler_stop_interrupts_running_task(tmp_path: Path) -> None:
    executor = ControlledExecutor()
    scheduler, store = await scheduler_parts(tmp_path, executor)
    task = await store.create(
        DownloadTaskSpec(service="fanbox", creator_id="one", post_id="42", output=tmp_path / "one")
    )
    await scheduler._dispatch_ready_tasks()
    assert await executor.started.get() == task.id
    await scheduler.stop()
    assert (await store.get(task.id)).status is TaskStatus.interrupted


@pytest.mark.asyncio
async def test_scheduler_records_snapshot_and_executor_failures(tmp_path: Path) -> None:
    class FailingExecutor:
        async def __call__(self, *_args, **_kwargs) -> None:
            raise RuntimeError("fixture executor failed")

    scheduler, store = await scheduler_parts(tmp_path, FailingExecutor())
    task = await store.create(
        DownloadTaskSpec(service="fanbox", creator_id="one", post_id="42", output=tmp_path / "one")
    )
    await scheduler._dispatch_ready_tasks()
    failed = await wait_for_store_status(scheduler, store, task.id, TaskStatus.failed)
    assert failed.error == "Unexpected RuntimeError during job generation"
    assert failed.failure is not None
    assert failed.failure.items[0].code is FailureCode.unknown
    assert failed.failure.items[0].stage is FailureStage.job_generation
    attempts = await store.attempts(task.id)
    assert attempts[0].failure == failed.failure

    broken_root = tmp_path / "broken"
    broken_root.mkdir()
    scheduler, store = await scheduler_parts(broken_root, ControlledExecutor())
    (broken_root / "ktoolbox.toml").write_text("not = [valid", encoding="utf-8")
    task = await store.create(
        DownloadTaskSpec(service="fanbox", creator_id="one", post_id="42", output=broken_root / "one")
    )
    await scheduler._launch(task, task_resources(task.spec))
    assert (await store.get(task.id)).status is TaskStatus.failed


@pytest.mark.asyncio
async def test_scheduler_cancellation_without_running_entry_is_interrupted(tmp_path: Path) -> None:
    async def cancel_executor(*_args, **_kwargs) -> None:
        raise asyncio.CancelledError

    scheduler, store = await scheduler_parts(tmp_path, cancel_executor)
    task = await store.create(
        DownloadTaskSpec(service="fanbox", creator_id="one", post_id="42", output=tmp_path / "one")
    )
    snapshot = _load_snapshot(tmp_path)
    attempt = await store.start_attempt(task, snapshot.redacted())
    task = await store.set_status(task.id, TaskStatus.running)
    await scheduler._execute(task, snapshot, attempt.id)
    assert (await store.get(task.id)).status is TaskStatus.interrupted
