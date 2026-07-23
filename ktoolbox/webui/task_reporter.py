from __future__ import annotations

import asyncio
from collections import deque
from pathlib import Path
from time import monotonic

from ktoolbox.failures import FailureItem
from ktoolbox.reporting import NullProgressReporter
from ktoolbox.webui.task_models import ActiveDownload, TaskProgress
from ktoolbox.webui.task_store import TaskStore


class WebTaskReporter(NullProgressReporter):
    """Translate synchronous core progress callbacks into persisted WebUI events."""

    def __init__(self, task_id: str, store: TaskStore, *, flush_interval: float = 0.2) -> None:
        self.task_id = task_id
        self.store = store
        self.progress = TaskProgress()
        self.flush_interval = flush_interval
        self._loop = asyncio.get_running_loop()
        self._started_at = monotonic()
        self._download_started_at: dict[str, float] = {}
        self._download_bytes: dict[str, int] = {}
        self._speed_samples: deque[tuple[float, int]] = deque()
        self._known_total = 0
        self._has_unknown_total = False
        self._pending: set[asyncio.Task[object]] = set()
        self._delayed_flush: asyncio.Task[object] | None = None
        self._delayed_event_type = "task.progress"
        self._delayed_event_data: dict[str, object] = {}

    def start(self) -> None:
        self._emit("task.progress", {"phase": "started"}, immediate=True)

    def stop(self) -> None:
        self._emit("task.progress", {"phase": "stopped"}, immediate=True)

    def creator_started(self, creator_key: str) -> None:
        if creator_key not in self.progress.active_creators:
            self.progress.active_creators.append(creator_key)
        self._emit("creator.started", {"creator": creator_key}, immediate=True)

    def creator_finished(
        self,
        creator_key: str,
        error: str | None = None,
        failure: FailureItem | None = None,
    ) -> None:
        if creator_key in self.progress.active_creators:
            self.progress.active_creators.remove(creator_key)
        self._emit(
            "creator.finished",
            {
                "creator": creator_key,
                "error": error,
                "failure": failure.model_dump(mode="json") if failure else None,
            },
            immediate=True,
        )

    def job_queued(self, creator_key: str) -> None:
        self.progress.queued_files += 1
        self._emit("job.queued", {"creator": creator_key})

    def download_started(
        self,
        task_key: str,
        creator_key: str,
        filename: str,
        total: int | None,
        completed: int,
    ) -> None:
        now = monotonic()
        self._download_started_at[task_key] = now
        self._download_bytes[task_key] = completed
        self.progress.transferred_bytes += completed
        if total is None:
            self._has_unknown_total = True
        else:
            self._known_total += total
        self.progress.total_bytes = None if self._has_unknown_total else self._known_total
        self.progress.active_downloads[task_key] = ActiveDownload(
            creator_key=creator_key,
            filename=filename,
            total=total,
            completed=completed,
        )
        self._record_speed(now)
        self._emit(
            "download.started",
            {"key": task_key, "creator": creator_key, "filename": filename, "total": total},
            immediate=True,
        )

    def download_advanced(self, task_key: str, amount: int) -> None:
        active = self.progress.active_downloads.get(task_key)
        if active is None:
            return
        now = monotonic()
        active.completed += amount
        self.progress.transferred_bytes += amount
        self._download_bytes[task_key] = active.completed
        elapsed = max(now - self._download_started_at[task_key], 0.001)
        active.speed_bps = active.completed / elapsed
        self._record_speed(now)
        self._refresh_eta()
        self._emit("download.progress", {"key": task_key})

    def download_finished(
        self,
        task_key: str,
        status: str,
        failure: FailureItem | None = None,
    ) -> None:
        self.progress.active_downloads.pop(task_key, None)
        self._download_started_at.pop(task_key, None)
        self._download_bytes.pop(task_key, None)
        self.progress.processed_files += 1
        if status == "completed":
            self.progress.completed_files += 1
        elif status == "existed":
            self.progress.existing_files += 1
        elif status == "failed":
            self.progress.failed_files += 1
        self._record_speed(monotonic())
        self._refresh_eta()
        if not self.progress.active_downloads:
            self.progress.speed_bps = 0
            self.progress.eta_seconds = 0 if self.progress.total_bytes is not None else None
        self._emit(
            "download.finished",
            {
                "key": task_key,
                "status": status,
                "failure": failure.model_dump(mode="json") if failure else None,
            },
            immediate=True,
        )

    def artifact_created(self, path: Path) -> None:
        self._track(self.store.add_artifact(self.task_id, path))

    def log(self, level: str, message: str) -> None:
        self._track(
            self.store.add_event(
                self.task_id,
                "task.log",
                {"level": level, "message": message},
            )
        )

    async def close(self) -> None:
        if self._delayed_flush is not None:
            self._delayed_flush.cancel()
            await asyncio.gather(self._delayed_flush, return_exceptions=True)
            self._delayed_flush = None
            await self._persist(self._delayed_event_type, self._delayed_event_data)
        await self._persist("task.progress", {"phase": "settled"})
        while self._pending:
            await asyncio.gather(*tuple(self._pending), return_exceptions=True)

    def _record_speed(self, now: float) -> None:
        self._speed_samples.append((now, self.progress.transferred_bytes))
        cutoff = now - 5
        while len(self._speed_samples) > 1 and self._speed_samples[0][0] < cutoff:
            self._speed_samples.popleft()
        if len(self._speed_samples) > 1:
            first_time, first_bytes = self._speed_samples[0]
            self.progress.speed_bps = (self.progress.transferred_bytes - first_bytes) / max(now - first_time, 0.001)
        elif self.progress.transferred_bytes:
            self.progress.speed_bps = self.progress.transferred_bytes / max(now - self._started_at, 0.001)

    def _refresh_eta(self) -> None:
        total = self.progress.total_bytes
        if total is None or self.progress.speed_bps <= 0:
            self.progress.eta_seconds = None
            return
        remaining = max(total - self.progress.transferred_bytes, 0)
        self.progress.eta_seconds = remaining / self.progress.speed_bps

    def _emit(self, event_type: str, data: dict[str, object], *, immediate: bool = False) -> None:
        if immediate:
            self._track(self._persist(event_type, data))
            return
        self._delayed_event_type = event_type
        self._delayed_event_data = data
        if self._delayed_flush is None or self._delayed_flush.done():
            task = self._loop.create_task(self._flush_later())
            self._delayed_flush = task
            self._remember(task)

    async def _flush_later(self) -> None:
        await asyncio.sleep(self.flush_interval)
        event_type = self._delayed_event_type
        event_data = self._delayed_event_data
        self._delayed_flush = None
        await self._persist(event_type, event_data)

    async def _persist(self, event_type: str, data: dict[str, object]) -> None:
        snapshot = self.progress.model_copy(deep=True)
        await self.store.update_progress(self.task_id, snapshot)
        await self.store.add_event(
            self.task_id,
            event_type,
            {**data, "progress": snapshot.model_dump(mode="json")},
        )

    def _track(self, coroutine: object) -> None:
        if not asyncio.iscoroutine(coroutine):
            raise TypeError("expected coroutine")
        self._remember(self._loop.create_task(coroutine))

    def _remember(self, task: asyncio.Task[object]) -> None:
        self._pending.add(task)
        task.add_done_callback(self._pending.discard)
