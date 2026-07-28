from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from ktoolbox.configuration import Configuration, RuntimeContext
from ktoolbox.project_config import (
    AutomaticSyncOptions,
    AutomaticSyncPlan,
    CreatorReference,
    CronAutomaticSyncSchedule,
    ProjectConfigStore,
    ProjectConfiguration,
)
from ktoolbox.webui.auto_sync_models import AutomaticSyncRunStatus
from ktoolbox.webui.auto_sync_scheduler import AutomaticSyncConflictError, AutoSyncScheduler
from ktoolbox.webui.auto_sync_store import AutomaticSyncStore
from ktoolbox.webui.database import WebUIDatabase
from ktoolbox.webui.event_store import WebUIEventStore
from ktoolbox.webui.task_models import CreatorTaskExecutionResult, TaskExecutionResult, TaskStatus
from ktoolbox.webui.task_store import TaskStore


class MutableClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value


class StoreTaskScheduler:
    def __init__(self, store: TaskStore) -> None:
        self.store = store

    async def create(self, spec, presentation=None, automatic_origin=None):
        return await self.store.create(spec, presentation, automatic_origin)


async def scheduler_fixture(
    tmp_path: Path,
    clock: MutableClock,
    plan: AutomaticSyncPlan,
    *,
    default_output: Path = Path("downloads"),
) -> tuple[AutoSyncScheduler, AutomaticSyncStore, TaskStore]:
    creator = CreatorReference(service="fanbox", creator_id="creator")
    ProjectConfigStore(tmp_path / "ktoolbox.toml").save(
        ProjectConfiguration(
            default_output=default_output,
            creators=[creator],
            automatic_sync=[plan],
        )
    )
    database = WebUIDatabase(tmp_path / ".ktoolbox" / "webui.sqlite3")
    await database.initialize()
    event_store = WebUIEventStore(database)
    tasks = TaskStore(database, event_store)
    automatic = AutomaticSyncStore(database, event_store)
    context = RuntimeContext(tmp_path, Configuration(_env_file=None))
    scheduler = AutoSyncScheduler(
        context,
        StoreTaskScheduler(tasks),  # type: ignore[arg-type]
        tasks,
        automatic,
        clock=clock,
        poll_interval=0.01,
    )
    return scheduler, automatic, tasks


async def test_run_now_builds_baseline_task_and_rejects_duplicate_active_run(tmp_path: Path) -> None:
    now = datetime(2026, 7, 27, 4, tzinfo=UTC)
    plan = AutomaticSyncPlan(
        id="daily",
        name="Daily",
        creators=["fanbox:creator"],
        options=AutomaticSyncOptions(output=Path("downloads")),
    )
    scheduler, automatic, tasks = await scheduler_fixture(tmp_path, MutableClock(now), plan)

    task_id = await scheduler.run_now("daily")
    task = await tasks.get(task_id)

    assert task.automatic_origin is not None
    assert task.automatic_origin.plan_id == "daily"
    assert task.automatic_origin.windows[0].baseline is True
    assert task.automatic_origin.windows[0].start_at is None
    assert task.spec.output == tmp_path / "downloads"
    assert (await automatic.active_run("daily")).task_id == task_id  # type: ignore[union-attr]
    with pytest.raises(AutomaticSyncConflictError) as caught:
        await scheduler.run_now("daily")
    assert caught.value.task_id == task_id


async def test_successful_checkpoint_creates_24_hour_overlap_window(tmp_path: Path) -> None:
    first = datetime(2026, 7, 27, 4, tzinfo=UTC)
    clock = MutableClock(first)
    plan = AutomaticSyncPlan(id="daily", name="Daily", creators=["fanbox:creator"])
    scheduler, automatic, tasks = await scheduler_fixture(tmp_path, clock, plan)
    first_task_id = await scheduler.run_now("daily")
    first_task = await tasks.set_status(first_task_id, TaskStatus.completed)
    await automatic.reconcile_task(
        first_task,
        result=TaskExecutionResult(
            creators=[
                CreatorTaskExecutionResult(
                    creator_key="fanbox:creator",
                    accepted_post_ids=["one"],
                    generation_successful=True,
                )
            ]
        ),
    )

    clock.value = datetime(2026, 7, 28, 8, tzinfo=UTC)
    second_task = await tasks.get(await scheduler.run_now("daily"))

    assert second_task.automatic_origin is not None
    assert second_task.automatic_origin.windows[0].start_at == datetime(2026, 7, 26, 4, tzinfo=UTC)
    assert second_task.automatic_origin.windows[0].baseline is False


async def test_automatic_sync_inherits_external_project_default_output(tmp_path: Path) -> None:
    plan = AutomaticSyncPlan(id="daily", name="Daily", creators=["fanbox:creator"])
    scheduler, _, tasks = await scheduler_fixture(
        tmp_path,
        MutableClock(datetime(2026, 7, 27, 4, tzinfo=UTC)),
        plan,
        default_output=Path("../shared-downloads"),
    )

    task = await tasks.get(await scheduler.run_now("daily"))

    assert task.spec.output == tmp_path.parent / "shared-downloads"


async def test_explicit_initial_date_uses_plan_timezone_and_counts_updates(tmp_path: Path) -> None:
    now = datetime(2026, 7, 27, 4, tzinfo=UTC)
    plan = AutomaticSyncPlan(
        id="dated",
        name="Dated",
        creators=["fanbox:creator"],
        initial_start_date=date(2026, 7, 20),
        schedule=CronAutomaticSyncSchedule(timezone="Asia/Shanghai"),
    )
    scheduler, _, tasks = await scheduler_fixture(tmp_path, MutableClock(now), plan)

    task = await tasks.get(await scheduler.run_now("dated"))

    assert task.automatic_origin is not None
    window = task.automatic_origin.windows[0]
    assert window.start_at == datetime(2026, 7, 19, 16, tzinfo=UTC)
    assert window.baseline is False


async def test_scheduler_skips_missed_occurrences_without_catch_up(tmp_path: Path) -> None:
    clock = MutableClock(datetime(2026, 7, 27, 12, 34, 30, tzinfo=UTC))
    plan = AutomaticSyncPlan(
        id="minute",
        name="Minute",
        creators=["fanbox:creator"],
        schedule=CronAutomaticSyncSchedule(expression="* * * * *", timezone="UTC"),
    )
    scheduler, automatic, tasks = await scheduler_fixture(tmp_path, clock, plan)
    await scheduler.reload()
    assert scheduler.next_run_at("minute") == datetime(2026, 7, 27, 12, 35, tzinfo=UTC)

    clock.value = datetime(2026, 7, 27, 12, 36, 10, tzinfo=UTC)
    await scheduler._trigger_due_plans()

    assert len(await tasks.list_tasks()) == 1
    assert len(await automatic.list_runs()) == 1
    assert scheduler.next_run_at("minute") == datetime(2026, 7, 27, 12, 37, tzinfo=UTC)
    assert (await automatic.list_runs())[0].status is AutomaticSyncRunStatus.queued
