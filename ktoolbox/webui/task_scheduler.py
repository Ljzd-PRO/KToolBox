from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

import anyio

from ktoolbox.configuration import RuntimeContext
from ktoolbox.project_config import ProjectConfigStore
from ktoolbox.utils import parse_webpage_url
from ktoolbox.webui.task_executor import CoreTaskExecutor, TaskExecutionSnapshot, TaskExecutor
from ktoolbox.webui.task_models import (
    RUNNING_TASK_STATUSES,
    SyncTaskSpec,
    TaskRecord,
    TaskSpec,
    TaskStatus,
)
from ktoolbox.webui.task_reporter import WebTaskReporter
from ktoolbox.webui.task_store import InvalidTaskStateError, TaskStore


@dataclass(frozen=True, slots=True)
class TaskResources:
    output: Path
    creators: frozenset[str]
    posts: frozenset[str]

    def conflicts_with(self, other: TaskResources) -> bool:
        if not _paths_overlap(self.output, other.output):
            return False
        if self.posts & other.posts:
            return True
        return bool(self.creators & other.creators)


@dataclass(slots=True)
class RunningTask:
    task: asyncio.Task[None]
    resources: TaskResources
    requested_final_status: TaskStatus = TaskStatus.interrupted


class TaskScheduler:
    """Persisted bounded scheduler for WebUI sync and download tasks."""

    def __init__(
        self,
        context: RuntimeContext,
        store: TaskStore,
        *,
        max_concurrency: int,
        executor: TaskExecutor | None = None,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("task concurrency must be positive")
        self.context = context
        self.store = store
        self.max_concurrency = max_concurrency
        self.executor = executor or CoreTaskExecutor()
        self._running: dict[str, RunningTask] = {}
        self._wake = asyncio.Event()
        self._control_lock = asyncio.Lock()
        self._dispatch_task: asyncio.Task[None] | None = None
        self._stopping = False

    async def start(self) -> None:
        if self._dispatch_task is not None:
            return
        await self.store.recover_interrupted()
        self._stopping = False
        self._dispatch_task = asyncio.create_task(self._dispatch_loop(), name="ktoolbox-webui-scheduler")
        self._wake.set()

    async def stop(self) -> None:
        self._stopping = True
        dispatch_task = self._dispatch_task
        self._dispatch_task = None
        if dispatch_task is not None:
            dispatch_task.cancel()
            await asyncio.gather(dispatch_task, return_exceptions=True)
        async with self._control_lock:
            running = tuple(self._running.values())
            for item in running:
                item.requested_final_status = TaskStatus.interrupted
                item.task.cancel()
        if running:
            await asyncio.gather(*(item.task for item in running), return_exceptions=True)

    async def create(self, spec: TaskSpec) -> TaskRecord:
        task = await self.store.create(spec)
        self._wake.set()
        return task

    async def update(self, task_id: str, spec: TaskSpec) -> TaskRecord:
        async with self._control_lock:
            task = await self.store.update_spec(task_id, spec)
        self._wake.set()
        return task

    async def reorder(self, task_id: str, position: int) -> TaskRecord:
        async with self._control_lock:
            task = await self.store.get(task_id)
            if task.status in RUNNING_TASK_STATUSES:
                raise InvalidTaskStateError("pause or stop a running task before reordering it")
            task = await self.store.reorder(task_id, position)
        self._wake.set()
        return task

    async def pause(self, task_id: str) -> TaskRecord:
        async with self._control_lock:
            task = await self.store.get(task_id)
            if task.status in {TaskStatus.queued, TaskStatus.blocked}:
                return await self.store.set_status(task_id, TaskStatus.paused)
            running = self._running.get(task_id)
            if task.status is not TaskStatus.running or running is None:
                raise InvalidTaskStateError("only queued, blocked, or running tasks can be paused")
            running.requested_final_status = TaskStatus.paused
            updated = await self.store.set_status(task_id, TaskStatus.pause_requested)
            running.task.cancel()
            return updated

    async def stop_task(self, task_id: str) -> TaskRecord:
        async with self._control_lock:
            task = await self.store.get(task_id)
            if task.status in {TaskStatus.queued, TaskStatus.blocked, TaskStatus.paused}:
                return await self.store.set_status(task_id, TaskStatus.stopped)
            running = self._running.get(task_id)
            if task.status is not TaskStatus.running or running is None:
                raise InvalidTaskStateError("this task cannot be stopped in its current state")
            running.requested_final_status = TaskStatus.stopped
            updated = await self.store.set_status(task_id, TaskStatus.stop_requested)
            running.task.cancel()
            return updated

    async def resume(self, task_id: str) -> TaskRecord:
        async with self._control_lock:
            task = await self.store.get(task_id)
            if task.status not in {
                TaskStatus.paused,
                TaskStatus.stopped,
                TaskStatus.failed,
                TaskStatus.interrupted,
                TaskStatus.completed,
            }:
                raise InvalidTaskStateError("this task cannot be resumed in its current state")
            updated = await self.store.queue_again(task_id)
        self._wake.set()
        return updated

    async def _dispatch_loop(self) -> None:
        while True:
            self._wake.clear()
            await self._dispatch_ready_tasks()
            try:
                await asyncio.wait_for(self._wake.wait(), timeout=0.25)
            except TimeoutError:
                pass

    async def _dispatch_ready_tasks(self) -> None:
        async with self._control_lock:
            if self._stopping:
                return
            tasks = await self.store.list_tasks()
            for task in tasks:
                if task.status not in {TaskStatus.queued, TaskStatus.blocked}:
                    continue
                resources = task_resources(task.spec)
                conflict = next(
                    (
                        task_id
                        for task_id, running in self._running.items()
                        if resources.conflicts_with(running.resources)
                    ),
                    None,
                )
                if conflict is not None:
                    if task.status is not TaskStatus.blocked or task.blocked_by != conflict:
                        await self.store.set_status(task.id, TaskStatus.blocked, blocked_by=conflict)
                    continue
                if task.status is TaskStatus.blocked:
                    task = await self.store.set_status(task.id, TaskStatus.queued)
                if len(self._running) >= self.max_concurrency:
                    continue
                await self._launch(task, resources)

    async def _launch(self, task: TaskRecord, resources: TaskResources) -> None:
        try:
            snapshot = await anyio.to_thread.run_sync(_load_snapshot, self.context.project_root)
            attempt = await self.store.start_attempt(task, snapshot.redacted())
            task = await self.store.set_status(task.id, TaskStatus.running)
        except Exception as error:
            await self.store.set_status(task.id, TaskStatus.failed, error=_error_text(error))
            return
        runner = asyncio.create_task(
            self._execute(task, snapshot, attempt.id),
            name=f"ktoolbox-webui-task-{task.id}",
        )
        self._running[task.id] = RunningTask(task=runner, resources=resources)

    async def _execute(self, task: TaskRecord, snapshot: TaskExecutionSnapshot, attempt_id: int) -> None:
        reporter = WebTaskReporter(task.id, self.store)
        final_status = TaskStatus.completed
        error_text: str | None = None
        try:
            await self.executor(task, snapshot, reporter)
        except asyncio.CancelledError:
            running = self._running.get(task.id)
            final_status = running.requested_final_status if running is not None else TaskStatus.interrupted
        except Exception as error:
            final_status = TaskStatus.failed
            error_text = _error_text(error)
            reporter.log("error", error_text)
        finally:
            await reporter.close()
            await self.store.finish_attempt(attempt_id, final_status, error_text)
            await self.store.set_status(task.id, final_status, error=error_text)
            async with self._control_lock:
                self._running.pop(task.id, None)
            self._wake.set()


def task_resources(spec: TaskSpec) -> TaskResources:
    output = spec.output.expanduser().resolve()
    if isinstance(spec, SyncTaskSpec):
        creators = frozenset(creator.key.casefold() for creator in spec.creators)
        return TaskResources(output=output, creators=creators, posts=frozenset())
    service, creator_id, post_id = spec.service, spec.creator_id, spec.post_id
    if spec.post:
        service, creator_id, post_id, _ = parse_webpage_url(spec.post)
    creators = frozenset({f"{service}:{creator_id}".casefold()}) if service and creator_id else frozenset()
    posts = (
        frozenset({f"{service}:{creator_id}:{post_id}".casefold()})
        if service and creator_id and post_id
        else frozenset()
    )
    return TaskResources(output=output, creators=creators, posts=posts)


def _paths_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _load_snapshot(project_root: Path) -> TaskExecutionSnapshot:
    runtime = RuntimeContext.from_project(project_root).snapshot()
    project = ProjectConfigStore(project_root / "ktoolbox.toml").load().model_copy(deep=True)
    return TaskExecutionSnapshot(runtime=runtime, project=project)


def _error_text(error: Exception) -> str:
    text = str(error).strip() or error.__class__.__name__
    return text[:2000]
