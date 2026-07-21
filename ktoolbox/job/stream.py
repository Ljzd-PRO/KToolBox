from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from itertools import count

import httpx
from loguru import logger

from ktoolbox._enum import RetCodeEnum
from ktoolbox.api.utils import get_file_url
from ktoolbox.configuration import config
from ktoolbox.downloader import Downloader
from ktoolbox.downloader.base import DownloaderRet
from ktoolbox.job.model import Job
from ktoolbox.reporting import NullProgressReporter, ProgressReporter, ReporterDownloadObserver


@dataclass(frozen=True, slots=True)
class QueuedJob:
    creator_key: str
    job: Job


class FairJobQueue:
    """A bounded round-robin queue with one producer lane per creator."""

    def __init__(self, lane_size: int) -> None:
        if lane_size < 1:
            raise ValueError("lane_size must be positive")
        self._lane_size = lane_size
        self._queues: dict[str, asyncio.Queue[Job]] = {}
        self._open: set[str] = set()
        self._order: deque[str] = deque()
        self._condition = asyncio.Condition()

    def register(self, creator_key: str) -> None:
        if creator_key in self._queues:
            raise ValueError(f"creator queue already registered: {creator_key}")
        self._queues[creator_key] = asyncio.Queue(maxsize=self._lane_size)
        self._open.add(creator_key)
        self._order.append(creator_key)

    async def put(self, creator_key: str, job: Job) -> None:
        if creator_key not in self._open:
            raise RuntimeError(f"creator queue is closed: {creator_key}")
        await self._queues[creator_key].put(job)
        async with self._condition:
            self._condition.notify_all()

    async def close(self, creator_key: str) -> None:
        self._open.discard(creator_key)
        async with self._condition:
            self._condition.notify_all()

    async def get(self) -> QueuedJob | None:
        async with self._condition:
            while True:
                self._discard_drained_lanes()
                for _ in range(len(self._order)):
                    creator_key = self._order[0]
                    self._order.rotate(-1)
                    queue = self._queues[creator_key]
                    try:
                        return QueuedJob(creator_key=creator_key, job=queue.get_nowait())
                    except asyncio.QueueEmpty:
                        continue
                if not self._open and not self._order:
                    return None
                await self._condition.wait()

    def task_done(self, creator_key: str) -> None:
        self._queues[creator_key].task_done()

    @property
    def waiting_size(self) -> int:
        return sum(queue.qsize() for queue in self._queues.values())

    def _discard_drained_lanes(self) -> None:
        for creator_key in tuple(self._order):
            if creator_key not in self._open and self._queues[creator_key].empty():
                self._order.remove(creator_key)


@dataclass(slots=True)
class DownloadSummary:
    total: int = 0
    completed: int = 0
    existed: int = 0
    failed: int = 0

    @property
    def successful(self) -> bool:
        return self.failed == 0


DownloadCallable = Callable[
    [QueuedJob, httpx.AsyncClient, ReporterDownloadObserver],
    Awaitable[DownloaderRet[str]],
]


class DownloadWorkerPool:
    """Consume a fair job queue with one shared HTTPX connection pool."""

    def __init__(
        self,
        concurrency: int,
        *,
        download: DownloadCallable | None = None,
        reporter: ProgressReporter | None = None,
    ) -> None:
        if concurrency < 1:
            raise ValueError("download concurrency must be positive")
        self.concurrency = concurrency
        self._download = _download_job if download is None else download
        self.reporter = reporter or NullProgressReporter()
        self._task_ids = count(1)

    async def run(self, queue: FairJobQueue) -> DownloadSummary:
        summary = DownloadSummary()
        limits = httpx.Limits(max_connections=self.concurrency, max_keepalive_connections=self.concurrency)
        async with httpx.AsyncClient(
            verify=config.ssl_verify,
            cookies={"session": config.downloader.session_key} if config.downloader.session_key else None,
            limits=limits,
        ) as client:
            workers = [asyncio.create_task(self._worker(queue, client, summary)) for _ in range(self.concurrency)]
            try:
                await asyncio.gather(*workers)
            except BaseException:
                for worker in workers:
                    worker.cancel()
                await asyncio.gather(*workers, return_exceptions=True)
                raise
        return summary

    async def _worker(
        self,
        queue: FairJobQueue,
        client: httpx.AsyncClient,
        summary: DownloadSummary,
    ) -> None:
        while queued := await queue.get():
            summary.total += 1
            task_key = f"download-{next(self._task_ids)}"
            observer = ReporterDownloadObserver(self.reporter, task_key, queued.creator_key)
            status = "failed"
            try:
                result = await self._download(queued, client, observer)
                if result.code == RetCodeEnum.FileExisted:
                    summary.existed += 1
                    status = "existed"
                elif result.code == RetCodeEnum.Success:
                    summary.completed += 1
                    status = "completed"
                    if result.data:
                        self.reporter.artifact_created(queued.job.path / result.data)
                else:
                    summary.failed += 1
                    logger.error(result.message)
            except asyncio.CancelledError:
                status = "cancelled"
                raise
            except Exception as error:
                summary.failed += 1
                logger.error(f"Download failed for {queued.job.alt_filename or queued.job.server_path}: {error}")
            finally:
                self.reporter.download_finished(task_key, status)
                queue.task_done(queued.creator_key)


async def _download_job(
    queued: QueuedJob,
    client: httpx.AsyncClient,
    observer: ReporterDownloadObserver,
) -> DownloaderRet[str]:
    job = queued.job
    downloader = Downloader(
        url=get_file_url(job.server_path),
        path=job.path,
        client=client,
        designated_filename=job.alt_filename,
        server_path=job.server_path,
        post=job.post,
    )
    return await downloader.run(progress=observer)
