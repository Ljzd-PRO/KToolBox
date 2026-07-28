from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone

from ktoolbox.automatic_sync import next_automatic_sync_time
from ktoolbox.configuration import RuntimeContext
from ktoolbox.project_config import (
    AutomaticSyncPlan,
    CreatorReference,
    ProjectConfigStore,
    resolve_project_output,
)
from ktoolbox.webui.auto_sync_models import AutomaticSyncRunTrigger
from ktoolbox.webui.auto_sync_store import AutomaticSyncStore
from ktoolbox.webui.database import utc_now
from ktoolbox.webui.task_models import (
    AutomaticCreatorWindowSnapshot,
    AutomaticTaskOrigin,
    SyncTaskSpec,
    TaskStatus,
)
from ktoolbox.webui.task_scheduler import TaskScheduler
from ktoolbox.webui.task_store import DuplicateTaskError, TaskNotFoundError, TaskStore

CHECKPOINT_OVERLAP = timedelta(hours=24)


class AutomaticSyncConflictError(ValueError):
    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"automatic sync plan already has an active task: {task_id}")


@dataclass(slots=True)
class _ScheduledPlan:
    signature: str
    next_run_at: datetime


class AutoSyncScheduler:
    """Create ordinary persisted sync tasks from project-local recurring plans."""

    def __init__(
        self,
        context: RuntimeContext,
        task_scheduler: TaskScheduler,
        task_store: TaskStore,
        store: AutomaticSyncStore,
        *,
        clock: Callable[[], datetime] = utc_now,
        poll_interval: float = 1.0,
    ) -> None:
        self.context = context
        self.task_scheduler = task_scheduler
        self.task_store = task_store
        self.store = store
        self.clock = clock
        self.poll_interval = poll_interval
        self._scheduled: dict[str, _ScheduledPlan] = {}
        self._loop_task: asyncio.Task[None] | None = None
        self._wake = asyncio.Event()

    async def start(self) -> None:
        if self._loop_task is not None:
            return
        await self.reload()
        await self.reconcile()
        self._loop_task = asyncio.create_task(self._run_loop(), name="ktoolbox-auto-sync-scheduler")

    async def stop(self) -> None:
        task = self._loop_task
        self._loop_task = None
        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    async def reload(self) -> None:
        await self._refresh_plans()
        self._wake.set()

    async def _refresh_plans(self) -> None:
        now = self._now()
        configuration = self._project_store().load()
        enabled = {plan.id: plan for plan in configuration.automatic_sync if plan.enabled}
        for plan_id in tuple(self._scheduled):
            if plan_id not in enabled:
                self._scheduled.pop(plan_id)
        for plan in enabled.values():
            signature = plan.model_dump_json()
            current = self._scheduled.get(plan.id)
            if current is None or current.signature != signature:
                self._scheduled[plan.id] = _ScheduledPlan(
                    signature=signature,
                    next_run_at=next_automatic_sync_time(plan.schedule, now),
                )

    async def run_now(self, plan_id: str) -> str:
        plan = self._find_plan(plan_id)
        active = await self.store.active_run(plan.id)
        if active is not None and active.task_id is not None:
            raise AutomaticSyncConflictError(active.task_id)
        task_id = await self._enqueue(plan, AutomaticSyncRunTrigger.immediate, self._now())
        return task_id

    async def reconcile(self) -> None:
        for run in await self.store.list_runs(limit=200):
            if run.task_id is None:
                continue
            try:
                task = await self.task_store.get(run.task_id)
            except TaskNotFoundError:
                continue
            result = None
            if task.status in {
                TaskStatus.completed,
                TaskStatus.failed,
                TaskStatus.interrupted,
                TaskStatus.paused,
                TaskStatus.stopped,
            }:
                attempts = await self.task_store.attempts(task.id)
                result = attempts[0].result if attempts else None
            await self.store.reconcile_task(task, result=result)

    def next_run_at(self, plan_id: str) -> datetime | None:
        scheduled = self._scheduled.get(plan_id)
        return scheduled.next_run_at if scheduled is not None else None

    async def _run_loop(self) -> None:
        while True:
            self._wake.clear()
            await self._refresh_plans()
            await self.reconcile()
            await self._trigger_due_plans()
            try:
                await asyncio.wait_for(self._wake.wait(), timeout=self.poll_interval)
            except TimeoutError:
                pass

    async def _trigger_due_plans(self) -> None:
        now = self._now()
        plans = {plan.id: plan for plan in self._project_store().load().automatic_sync}
        for plan_id, scheduled in tuple(self._scheduled.items()):
            plan = plans.get(plan_id)
            if plan is None or not plan.enabled or scheduled.next_run_at > now:
                continue
            due_at = scheduled.next_run_at
            active = await self.store.active_run(plan.id)
            if active is not None:
                await self.store.mark_skipped(
                    plan,
                    now,
                    scheduled_for=due_at,
                    reason="an earlier run for this plan is still active",
                )
            else:
                await self._enqueue(
                    plan,
                    AutomaticSyncRunTrigger.scheduled,
                    now,
                    scheduled_for=due_at,
                )
            scheduled.next_run_at = next_automatic_sync_time(plan.schedule, now)

    async def _enqueue(
        self,
        plan: AutomaticSyncPlan,
        trigger: AutomaticSyncRunTrigger,
        cutoff_at: datetime,
        *,
        scheduled_for: datetime | None = None,
    ) -> str:
        project = self._project_store().load()
        creators = [self._creator(project.creators, creator_key) for creator_key in plan.creators]
        windows = [await self._window(plan, creator.key, cutoff_at) for creator in creators]
        run = await self.store.create_run(
            plan,
            trigger,
            cutoff_at,
            scheduled_for=scheduled_for,
        )
        origin = AutomaticTaskOrigin(
            plan_id=plan.id,
            plan_name=plan.name,
            run_id=run.id,
            windows=windows,
        )
        output = resolve_project_output(
            self.context.project_root,
            project,
            plan.options.output,
        )
        spec = SyncTaskSpec(
            creators=creators,
            output=output,
            save_creator_indices=plan.options.save_creator_indices,
            mix_posts=plan.options.mix_posts,
            keywords=plan.options.keywords,
            keywords_exclude=plan.options.keywords_exclude,
        )
        try:
            task = await self.task_scheduler.create(spec, automatic_origin=origin)
        except DuplicateTaskError as error:
            await self.store.mark_failed(run.id, str(error))
            raise AutomaticSyncConflictError(error.task_id) from error
        except Exception as error:
            await self.store.mark_failed(run.id, str(error)[:2000])
            raise
        await self.store.attach_task(run.id, task.id)
        return task.id

    async def _window(
        self,
        plan: AutomaticSyncPlan,
        creator_key: str,
        cutoff_at: datetime,
    ) -> AutomaticCreatorWindowSnapshot:
        checkpoint = await self.store.checkpoint(plan.id, creator_key)
        baseline = checkpoint is None and plan.initial_start_date is None
        if checkpoint is not None:
            start_at = checkpoint - CHECKPOINT_OVERLAP
        elif plan.initial_start_date is not None:
            zone = plan.schedule.timezone
            from zoneinfo import ZoneInfo

            start_at = datetime.combine(
                plan.initial_start_date,
                time.min,
                tzinfo=ZoneInfo(zone),
            ).astimezone(timezone.utc)
        else:
            start_at = None
        return AutomaticCreatorWindowSnapshot(
            creator_key=creator_key,
            start_at=start_at,
            end_at=cutoff_at,
            timezone=plan.schedule.timezone,
            baseline=baseline,
        )

    def _find_plan(self, plan_id: str) -> AutomaticSyncPlan:
        normalized = plan_id.casefold()
        for plan in self._project_store().load().automatic_sync:
            if plan.id.casefold() == normalized:
                return plan
        raise LookupError(f"automatic sync plan not found: {plan_id}")

    @staticmethod
    def _creator(creators: list[CreatorReference], creator_key: str) -> CreatorReference:
        normalized = creator_key.casefold()
        for creator in creators:
            if creator.key.casefold() == normalized:
                return creator
        raise LookupError(f"automatic sync creator not found: {creator_key}")

    def _project_store(self) -> ProjectConfigStore:
        return ProjectConfigStore(self.context.project_root / "ktoolbox.toml")

    def _now(self) -> datetime:
        value = self.clock()
        if value.tzinfo is None:
            raise ValueError("automatic sync clock must include a timezone")
        return value.astimezone(timezone.utc)
