from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from time import monotonic

from ktoolbox.failures import FailureItem, TaskFailureReport
from ktoolbox.reporting import NullProgressReporter
from ktoolbox.webui.task_models import ActiveDownload, TaskProgress, WaitingRetry
from ktoolbox.webui.task_store import TaskStore


@dataclass(slots=True)
class _ProgressWrite:
    event_type: str
    data: dict[str, object]
    progress: TaskProgress


@dataclass(slots=True)
class _ArtifactWrite:
    path: Path


class WebTaskReporter(NullProgressReporter):
    """Translate synchronous core progress callbacks into persisted WebUI events."""

    def __init__(
        self,
        task_id: str,
        store: TaskStore,
        *,
        flush_interval: float = 0.2,
        idle_speed_grace: float = 1.5,
    ) -> None:
        self.task_id = task_id
        self.store = store
        self.progress = TaskProgress()
        self.flush_interval = flush_interval
        self.idle_speed_grace = idle_speed_grace
        self._loop = asyncio.get_running_loop()
        self._started_at = monotonic()
        self._download_started_at: dict[str, float] = {}
        self._download_attempt_started_bytes: dict[str, int] = {}
        self._download_bytes: dict[str, int] = {}
        self._speed_samples: deque[tuple[float, int]] = deque()
        self._known_total = 0
        self._has_unknown_total = False
        self._writes: asyncio.Queue[_ProgressWrite | _ArtifactWrite | None] = asyncio.Queue()
        self._writer = self._loop.create_task(
            self._writer_loop(),
            name=f"ktoolbox-webui-reporter-{task_id}",
        )
        self._write_errors: list[BaseException] = []
        self._closed = False
        self._idle_speed_clear: asyncio.Task[object] | None = None
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
        self._cancel_idle_speed_clear()
        first_start = task_key not in self._download_bytes
        previous_completed = self._download_bytes.get(task_key, 0)
        self._download_started_at[task_key] = now
        self._download_attempt_started_bytes[task_key] = completed
        self._download_bytes[task_key] = completed
        self.progress.transferred_bytes += max(completed - previous_completed, 0)
        if first_start:
            if total is None:
                self._has_unknown_total = True
            else:
                self._known_total += total
            self.progress.total_bytes = None if self._has_unknown_total else self._known_total
        self.progress.waiting_retries.pop(task_key, None)
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
        active.speed_bps = (
            active.completed - self._download_attempt_started_bytes.get(task_key, 0)
        ) / elapsed
        self._record_speed(now)
        self._refresh_eta()
        self._emit("download.progress", {"key": task_key})

    def download_retrying(
        self,
        task_key: str,
        creator_key: str,
        filename: str,
        retry_count: int,
        status_code: int | None,
    ) -> None:
        self.progress.active_downloads.pop(task_key, None)
        self._download_started_at.pop(task_key, None)
        self._download_attempt_started_bytes.pop(task_key, None)
        self.progress.waiting_retries[task_key] = WaitingRetry(
            creator_key=creator_key,
            filename=filename,
            retry_count=retry_count,
            status_code=status_code,
        )
        if not self.progress.active_downloads:
            self._schedule_idle_speed_clear()
        self._emit(
            "download.retrying",
            {
                "key": task_key,
                "creator": creator_key,
                "filename": filename,
                "retry_count": retry_count,
                "status_code": status_code,
            },
            immediate=True,
        )

    def download_finished(
        self,
        task_key: str,
        status: str,
        failure: FailureItem | None = None,
    ) -> None:
        self.progress.active_downloads.pop(task_key, None)
        self.progress.waiting_retries.pop(task_key, None)
        self._download_started_at.pop(task_key, None)
        self._download_attempt_started_bytes.pop(task_key, None)
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
            self._schedule_idle_speed_clear()
        self._emit(
            "download.finished",
            {
                "key": task_key,
                "outcome": status,
                "failure": failure.model_dump(mode="json") if failure else None,
            },
            immediate=True,
        )

    def artifact_created(self, path: Path) -> None:
        self._writes.put_nowait(_ArtifactWrite(path))

    def log(
        self,
        level: str,
        message: str,
        failure_report: TaskFailureReport | None = None,
    ) -> None:
        self._emit(
            "task.log",
            {
                "level": level,
                "message": message,
                "failure_report": (
                    failure_report.model_dump(mode="json")
                    if failure_report is not None
                    else None
                ),
            },
            immediate=True,
        )

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._idle_speed_clear is not None:
            self._idle_speed_clear.cancel()
            await asyncio.gather(self._idle_speed_clear, return_exceptions=True)
            self._idle_speed_clear = None
        if self._delayed_flush is not None:
            self._delayed_flush.cancel()
            await asyncio.gather(self._delayed_flush, return_exceptions=True)
            self._delayed_flush = None
            self._enqueue_progress(self._delayed_event_type, self._delayed_event_data)
        self.progress.speed_bps = 0
        self.progress.eta_seconds = 0 if self.progress.total_bytes is not None else None
        self._enqueue_progress("task.progress", {"phase": "settled"})
        await self._writes.join()
        self._writes.put_nowait(None)
        await self._writer
        if self._write_errors:
            raise self._write_errors[0]

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

    def _schedule_idle_speed_clear(self) -> None:
        self._cancel_idle_speed_clear()
        self._idle_speed_clear = self._loop.create_task(self._clear_idle_speed_later())

    def _cancel_idle_speed_clear(self) -> None:
        if self._idle_speed_clear is not None and not self._idle_speed_clear.done():
            self._idle_speed_clear.cancel()
        self._idle_speed_clear = None

    async def _clear_idle_speed_later(self) -> None:
        await asyncio.sleep(self.idle_speed_grace)
        self._idle_speed_clear = None
        if self._closed or self.progress.active_downloads:
            return
        self.progress.speed_bps = 0
        self.progress.eta_seconds = None
        self._emit("task.progress", {"phase": "idle"}, immediate=True)

    def _emit(self, event_type: str, data: dict[str, object], *, immediate: bool = False) -> None:
        if immediate:
            self._enqueue_progress(event_type, data)
            return
        self._delayed_event_type = event_type
        self._delayed_event_data = data
        if self._delayed_flush is None or self._delayed_flush.done():
            task = self._loop.create_task(self._flush_later())
            self._delayed_flush = task

    async def _flush_later(self) -> None:
        await asyncio.sleep(self.flush_interval)
        event_type = self._delayed_event_type
        event_data = self._delayed_event_data
        self._delayed_flush = None
        self._enqueue_progress(event_type, event_data)

    def _enqueue_progress(self, event_type: str, data: dict[str, object]) -> None:
        snapshot = self.progress.model_copy(deep=True)
        self._writes.put_nowait(_ProgressWrite(event_type, dict(data), snapshot))

    async def _writer_loop(self) -> None:
        while True:
            write = await self._writes.get()
            try:
                if write is None:
                    return
                if isinstance(write, _ArtifactWrite):
                    await self.store.add_artifact(self.task_id, write.path)
                else:
                    await self.store.record_progress_event(
                        self.task_id,
                        write.event_type,
                        write.data,
                        write.progress,
                    )
            except BaseException as error:
                self._write_errors.append(error)
            finally:
                self._writes.task_done()
