from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from ktoolbox.project_config import AutomaticSyncPlan
from ktoolbox.webui.auto_sync_models import AutomaticSyncRunStatus, AutomaticSyncRunTrigger
from ktoolbox.webui.auto_sync_store import AutomaticSyncStore
from ktoolbox.webui.database import WebUIDatabase
from ktoolbox.webui.event_store import WebUIEventStore
from ktoolbox.webui.task_models import (
    AutomaticCreatorWindowSnapshot,
    AutomaticTaskOrigin,
    CreatorTaskExecutionResult,
    SyncTaskSpec,
    TaskExecutionResult,
    TaskStatus,
)
from ktoolbox.webui.task_store import TaskStore


def plan(plan_id: str, *creators: str) -> AutomaticSyncPlan:
    return AutomaticSyncPlan(
        id=plan_id,
        name=f"Plan {plan_id}",
        creators=list(creators),
    )


async def create_automatic_task(
    task_store: TaskStore,
    automatic_store: AutomaticSyncStore,
    *,
    plan_value: AutomaticSyncPlan,
    cutoff: datetime,
    baseline: bool,
    creators: list[str],
) -> tuple[str, str]:
    run = await automatic_store.create_run(
        plan_value,
        AutomaticSyncRunTrigger.immediate,
        cutoff,
    )
    origin = AutomaticTaskOrigin(
        plan_id=plan_value.id,
        plan_name=plan_value.name,
        run_id=run.id,
        windows=[
            AutomaticCreatorWindowSnapshot(
                creator_key=creator,
                start_at=None,
                end_at=cutoff,
                timezone="UTC",
                baseline=baseline,
            )
            for creator in creators
        ],
    )
    spec = SyncTaskSpec(
        creators=[
            {
                "service": creator.partition(":")[0],
                "creator_id": creator.partition(":")[2],
            }
            for creator in creators
        ],
        output=Path("downloads"),
    )
    task = await task_store.create(spec, automatic_origin=origin)
    await automatic_store.attach_task(run.id, task.id)
    return run.id, task.id


async def test_automatic_sync_store_advances_only_successful_creators_and_deduplicates(tmp_path: Path) -> None:
    database = WebUIDatabase(tmp_path / "webui.sqlite3")
    await database.initialize()
    events = WebUIEventStore(database)
    tasks = TaskStore(database, events)
    automatic = AutomaticSyncStore(database, events)
    cutoff = datetime(2026, 7, 27, 4, tzinfo=UTC)
    plan_value = plan("morning", "fanbox:one", "fanbox:two")
    run_id, task_id = await create_automatic_task(
        tasks,
        automatic,
        plan_value=plan_value,
        cutoff=cutoff,
        baseline=False,
        creators=plan_value.creators,
    )

    running = await tasks.set_status(task_id, TaskStatus.running)
    assert (await automatic.reconcile_task(running, result=None)).status is AutomaticSyncRunStatus.running
    result = TaskExecutionResult(
        creators=[
            CreatorTaskExecutionResult(
                creator_key="fanbox:one",
                accepted_post_ids=["post-1", "post-1"],
                generation_successful=True,
            ),
            CreatorTaskExecutionResult(
                creator_key="fanbox:two",
                accepted_post_ids=["post-2"],
                generation_successful=True,
                download_failures=1,
            ),
        ]
    )
    completed = await tasks.set_status(task_id, TaskStatus.completed)
    finished = await automatic.reconcile_task(completed, result=result)

    assert finished is not None
    assert finished.id == run_id
    assert finished.status is AutomaticSyncRunStatus.completed
    assert await automatic.checkpoint("morning", "fanbox:one") == cutoff
    assert await automatic.checkpoint("morning", "fanbox:two") is None
    updates = await automatic.recent_updates(since=None)
    assert [(item.service, item.creator_id, item.new_posts) for item in updates] == [
        ("fanbox", "one", 1),
    ]

    second_plan = plan("evening", "fanbox:one")
    _, second_task_id = await create_automatic_task(
        tasks,
        automatic,
        plan_value=second_plan,
        cutoff=cutoff,
        baseline=False,
        creators=second_plan.creators,
    )
    second_result = TaskExecutionResult(
        creators=[
            CreatorTaskExecutionResult(
                creator_key="fanbox:one",
                accepted_post_ids=["post-1"],
                generation_successful=True,
            )
        ]
    )
    second_task = await tasks.set_status(second_task_id, TaskStatus.completed)
    await automatic.reconcile_task(second_task, result=second_result)
    assert (await automatic.recent_updates(since=None))[0].new_posts == 1


async def test_automatic_sync_baseline_and_task_deletion_preserve_run_history(tmp_path: Path) -> None:
    database = WebUIDatabase(tmp_path / "webui.sqlite3")
    await database.initialize()
    events = WebUIEventStore(database)
    tasks = TaskStore(database, events)
    automatic = AutomaticSyncStore(database, events)
    cutoff = datetime(2026, 7, 27, 4, tzinfo=UTC)
    plan_value = plan("baseline", "fanbox:one")
    run_id, task_id = await create_automatic_task(
        tasks,
        automatic,
        plan_value=plan_value,
        cutoff=cutoff,
        baseline=True,
        creators=plan_value.creators,
    )
    result = TaskExecutionResult(
        creators=[
            CreatorTaskExecutionResult(
                creator_key="fanbox:one",
                accepted_post_ids=["historical"],
                generation_successful=True,
            )
        ]
    )
    task = await tasks.set_status(task_id, TaskStatus.completed)
    await automatic.reconcile_task(task, result=result)

    assert await automatic.recent_updates(since=None) == []
    assert await automatic.checkpoint("baseline", "fanbox:one") == cutoff
    await tasks.delete(task_id)
    assert (await automatic.get_run(run_id)).task_id is None


async def test_task_attempt_round_trips_automatic_execution_result(tmp_path: Path) -> None:
    database = WebUIDatabase(tmp_path / "webui.sqlite3")
    await database.initialize()
    tasks = TaskStore(database)
    task = await tasks.create(
        SyncTaskSpec(
            creators=[{"service": "fanbox", "creator_id": "one"}],
            output=tmp_path,
        )
    )
    attempt = await tasks.start_attempt(task, {})
    result = TaskExecutionResult(
        creators=[
            CreatorTaskExecutionResult(
                creator_key="fanbox:one",
                accepted_post_ids=["work"],
                generation_successful=True,
            )
        ]
    )

    await tasks.finish_attempt(attempt.id, TaskStatus.completed, result=result)

    assert (await tasks.attempts(task.id))[0].result == result
