from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from rich.console import Console, Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    DownloadColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Column


class DownloadProgressObserver(Protocol):
    def start(self, filename: str, total: int | None, completed: int) -> None: ...

    def advance(self, amount: int) -> None: ...


class ProgressReporter(Protocol):
    def start(self) -> None: ...

    def stop(self) -> None: ...

    def creator_started(self, creator_key: str) -> None: ...

    def creator_finished(self, creator_key: str, error: str | None = None) -> None: ...

    def job_queued(self, creator_key: str) -> None: ...

    def download_started(
        self,
        task_key: str,
        creator_key: str,
        filename: str,
        total: int | None,
        completed: int,
    ) -> None: ...

    def download_advanced(self, task_key: str, amount: int) -> None: ...

    def download_finished(self, task_key: str, status: str) -> None: ...


class NullProgressReporter:
    def start(self) -> None:
        return None

    def stop(self) -> None:
        return None

    def creator_started(self, creator_key: str) -> None:
        return None

    def creator_finished(self, creator_key: str, error: str | None = None) -> None:
        return None

    def job_queued(self, creator_key: str) -> None:
        return None

    def download_started(
        self,
        task_key: str,
        creator_key: str,
        filename: str,
        total: int | None,
        completed: int,
    ) -> None:
        return None

    def download_advanced(self, task_key: str, amount: int) -> None:
        return None

    def download_finished(self, task_key: str, status: str) -> None:
        return None


class PlainProgressReporter(NullProgressReporter):
    """Stable line-oriented progress for redirected output and CI logs."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self.queued = 0
        self.completed = 0
        self.failed = 0
        self.existed = 0

    def creator_finished(self, creator_key: str, error: str | None = None) -> None:
        if error:
            self.console.print(f"Creator {creator_key} failed: {error}")

    def job_queued(self, creator_key: str) -> None:
        self.queued += 1

    def download_finished(self, task_key: str, status: str) -> None:
        if status == "failed":
            self.failed += 1
        elif status == "existed":
            self.existed += 1
        else:
            self.completed += 1

    def stop(self) -> None:
        if self.queued:
            self.console.print(
                f"Files processed: {self.completed} downloaded, {self.existed} existing, {self.failed} failed."
            )


class RichProgressReporter(NullProgressReporter):
    """Render creator and file activity in one stable Rich Live region."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self.overall = Progress(
            TextColumn("[bold]Files"),
            BarColumn(),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TextColumn("{task.fields[status]}"),
            console=console,
            auto_refresh=False,
        )
        self.creators = Progress(
            SpinnerColumn(),
            TextColumn("{task.description}", table_column=Column(max_width=48, overflow="ellipsis")),
            TextColumn("{task.fields[status]}"),
            console=console,
            auto_refresh=False,
        )
        self.downloads = Progress(
            TextColumn("{task.description}", table_column=Column(max_width=44, overflow="ellipsis")),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
            auto_refresh=False,
        )
        self._overall_task = self.overall.add_task("Files", total=0, status="waiting")
        self._creator_tasks: dict[str, TaskID] = {}
        self._download_tasks: dict[str, TaskID] = {}
        self._failed = 0
        self._existed = 0
        self._live = Live(
            Group(self.overall, self.creators, self.downloads),
            console=console,
            refresh_per_second=10,
            redirect_stdout=True,
            redirect_stderr=True,
        )
        self._started = False

    def start(self) -> None:
        if not self._started:
            self._live.start(refresh=True)
            self._started = True

    def stop(self) -> None:
        if self._started:
            self._refresh_status()
            self._live.stop()
            self._started = False

    def creator_started(self, creator_key: str) -> None:
        if creator_key not in self._creator_tasks:
            self._creator_tasks[creator_key] = self.creators.add_task(
                creator_key,
                total=None,
                status="preparing",
            )

    def creator_finished(self, creator_key: str, error: str | None = None) -> None:
        task_id = self._creator_tasks.pop(creator_key, None)
        if task_id is not None:
            self.creators.remove_task(task_id)
        if error:
            self.console.print(f"[red]Creator {creator_key} failed:[/red] {error}")

    def job_queued(self, creator_key: str) -> None:
        task = self.overall.tasks[self._overall_task]
        self.overall.update(self._overall_task, total=(task.total or 0) + 1, status="downloading")

    def download_started(
        self,
        task_key: str,
        creator_key: str,
        filename: str,
        total: int | None,
        completed: int,
    ) -> None:
        self._download_tasks[task_key] = self.downloads.add_task(
            f"{creator_key}  {filename}",
            total=total,
            completed=completed,
        )

    def download_advanced(self, task_key: str, amount: int) -> None:
        task_id = self._download_tasks.get(task_key)
        if task_id is not None:
            self.downloads.advance(task_id, amount)

    def download_finished(self, task_key: str, status: str) -> None:
        task_id = self._download_tasks.pop(task_key, None)
        if task_id is not None:
            self.downloads.remove_task(task_id)
        if status == "failed":
            self._failed += 1
        elif status == "existed":
            self._existed += 1
        self.overall.advance(self._overall_task)
        self._refresh_status()

    def _refresh_status(self) -> None:
        self.overall.update(
            self._overall_task,
            status=f"{self._existed} existing, {self._failed} failed",
        )


@dataclass(slots=True)
class ReporterDownloadObserver:
    reporter: ProgressReporter
    task_key: str
    creator_key: str

    def start(self, filename: str, total: int | None, completed: int) -> None:
        self.reporter.download_started(self.task_key, self.creator_key, filename, total, completed)

    def advance(self, amount: int) -> None:
        self.reporter.download_advanced(self.task_key, amount)


def create_progress_reporter(
    console: Console,
    *,
    plain: bool = False,
    quiet: bool = False,
) -> ProgressReporter:
    if quiet:
        return NullProgressReporter()
    if plain or not console.is_terminal or "NO_COLOR" in os.environ:
        return PlainProgressReporter(console)
    return RichProgressReporter(console)
