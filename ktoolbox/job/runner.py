from __future__ import annotations

import asyncio

from loguru import logger
from rich.console import Console

from ktoolbox.configuration import config
from ktoolbox.job.model import Job
from ktoolbox.job.stream import DownloadSummary, DownloadWorkerPool, FairJobQueue
from ktoolbox.reporting import NullProgressReporter, ProgressReporter, create_progress_reporter

__all__ = ["JobRunner"]


class JobRunner:
    """Compatibility wrapper for running a finite list through the shared worker pool."""

    def __init__(
        self,
        *,
        job_list: list[Job] | None = None,
        progress: bool = True,
        reporter: ProgressReporter | None = None,
        concurrency: int | None = None,
    ) -> None:
        self._jobs = list(job_list or ())
        self._lock = asyncio.Lock()
        self._summary = DownloadSummary()
        self._concurrency = config.job.count if concurrency is None else concurrency
        if reporter is not None:
            self._reporter = reporter
        elif progress:
            self._reporter = create_progress_reporter(Console(stderr=True))
        else:
            self._reporter = NullProgressReporter()

    @property
    def finished(self) -> bool:
        return not self._lock.locked()

    @property
    def waiting_size(self) -> int:
        return len(self._jobs) if self.finished and self._summary.total == 0 else 0

    @property
    def done_size(self) -> int:
        return self._summary.total

    @property
    def processing_size(self) -> int:
        return 0

    @property
    def summary(self) -> DownloadSummary:
        return self._summary

    async def add_jobs(self, *jobs: Job) -> None:
        if not self.finished:
            raise RuntimeError("cannot add jobs after the runner has started")
        self._jobs.extend(jobs)

    async def start(self) -> int:
        async with self._lock:
            queue = FairJobQueue(max(1, len(self._jobs)))
            queue.register("direct")
            for job in self._jobs:
                await queue.put("direct", job)
                self._reporter.job_queued("direct")
            await queue.close("direct")

            self._reporter.start()
            try:
                self._summary = await DownloadWorkerPool(
                    self._concurrency,
                    reporter=self._reporter,
                ).run(queue)
            finally:
                self._reporter.stop()
            self._jobs.clear()

        if self._summary.failed:
            logger.warning(f"{self._summary.failed} jobs failed, download finished")
        else:
            logger.success("All jobs in queue finished")
        return self._summary.failed
