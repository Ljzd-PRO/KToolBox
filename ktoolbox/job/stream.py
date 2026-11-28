from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from functools import partial
from itertools import count
from pathlib import PurePosixPath
from urllib.parse import urlsplit

import httpx
from loguru import logger

from ktoolbox._enum import RetCodeEnum
from ktoolbox.api.client import PawchiveClient
from ktoolbox.api.utils import get_file_url
from ktoolbox.configuration import config
from ktoolbox.downloader import Downloader
from ktoolbox.downloader.base import DownloaderRet
from ktoolbox.downloader.missing_files import MissingFileHistory
from ktoolbox.downloader.temporary import TemporaryDownloader, TemporaryOutputConflict
from ktoolbox.failures import (
    FailureCode,
    FailureItem,
    FailureStage,
    classify_failure,
    failure_from_http_status,
    generic_failure,
)
from ktoolbox.job.model import Job
from ktoolbox.job.temporary import TemporaryFileUnavailable
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
    failures: list[FailureItem] = field(default_factory=list)
    creator_failures: dict[str, int] = field(default_factory=dict)
    skipped_missing: int = 0

    @property
    def successful(self) -> bool:
        return self.failed == 0


DownloadCallable = Callable[
    [QueuedJob, httpx.AsyncClient, ReporterDownloadObserver],
    Awaitable[DownloaderRet[str]],
]
FailureLogger = Callable[[QueuedJob, FailureItem], None]
_REJECTED_TEMPORARY_URL_STATUSES = frozenset({401, 403, 404, 410})


def _log_download_failure(queued: QueuedJob, failure: FailureItem) -> None:
    logger.error("{}: {}", failure.file_name or queued.creator_key, failure.message)


class DownloadWorkerPool:
    """Consume a fair job queue with one shared HTTPX connection pool."""

    def __init__(
        self,
        concurrency: int,
        *,
        download: DownloadCallable | None = None,
        reporter: ProgressReporter | None = None,
        api_client: PawchiveClient | None = None,
        failure_logger: FailureLogger | None = None,
        missing_files: MissingFileHistory | None = None,
    ) -> None:
        if concurrency < 1:
            raise ValueError("download concurrency must be positive")
        self.concurrency = concurrency
        self._download = download
        self._api_client = api_client
        self._failure_logger = failure_logger or _log_download_failure
        self._missing_files = missing_files
        self.reporter = reporter or NullProgressReporter()
        self._task_ids = count(1)

    async def run(self, queue: FairJobQueue) -> DownloadSummary:
        summary = DownloadSummary()
        limits = httpx.Limits(max_connections=self.concurrency, max_keepalive_connections=self.concurrency)
        async with (
            httpx.AsyncClient(
                verify=config.ssl_verify,
                cookies={"session": config.downloader.session_key} if config.downloader.session_key else None,
                limits=limits,
            ) as client,
            httpx.AsyncClient(verify=config.ssl_verify, limits=limits) as temporary_client,
        ):
            download = self._download or partial(
                _download_job,
                temporary_client=temporary_client,
                api_client=self._api_client,
                missing_files=self._missing_files,
            )
            workers = [
                asyncio.create_task(self._worker(queue, client, summary, download)) for _ in range(self.concurrency)
            ]
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
        download: DownloadCallable,
    ) -> None:
        while queued := await queue.get():
            summary.total += 1
            task_key = f"download-{next(self._task_ids)}"
            status = "failed"
            failure: FailureItem | None = None
            filename = _job_filename(queued.job)
            observer = ReporterDownloadObserver(
                self.reporter,
                task_key,
                queued.creator_key,
                filename or "unknown",
                preserve_filename=queued.job.alt_filename is not None,
            )
            try:
                result = await download(queued, client, observer)
                if result.code == RetCodeEnum.FileExisted:
                    summary.existed += 1
                    status = "existed"
                elif result.code == RetCodeEnum.FileMissingSkipped:
                    summary.skipped_missing += 1
                    status = "skipped_missing"
                elif result.code == RetCodeEnum.Success:
                    summary.completed += 1
                    status = "completed"
                    if result.data:
                        self.reporter.artifact_created(queued.job.path / result.data)
                else:
                    summary.failed += 1
                    summary.creator_failures[queued.creator_key] = (
                        summary.creator_failures.get(queued.creator_key, 0) + 1
                    )
                    failure = (
                        failure_from_http_status(
                            result.status_code,
                            stage=FailureStage.file_request,
                            file_name=filename,
                        )
                        if result.status_code is not None
                        else generic_failure(
                            stage=FailureStage.file_request,
                            message="The file download failed",
                            code=FailureCode.download_failed,
                            retryable=True,
                            file_name=filename,
                        )
                    )
                    summary.failures.append(failure)
            except asyncio.CancelledError:
                status = "cancelled"
                raise
            except Exception as error:
                summary.failed += 1
                summary.creator_failures[queued.creator_key] = summary.creator_failures.get(queued.creator_key, 0) + 1
                if isinstance(error, TemporaryFileUnavailable):
                    failure = FailureItem(
                        code=FailureCode.resource_not_found,
                        stage=FailureStage.file_request,
                        operation="download_temporary_file",
                        message=str(error),
                        retryable=False,
                        file_name=filename,
                        http_status=error.status,
                    )
                elif isinstance(error, TemporaryOutputConflict):
                    failure = FailureItem(
                        code=FailureCode.download_failed,
                        stage=FailureStage.file_write,
                        operation="temporary_file_conflict",
                        message=str(error),
                        retryable=False,
                        file_name=filename,
                    )
                else:
                    failure = classify_failure(
                        error,
                        stage=FailureStage.file_write if isinstance(error, OSError) else FailureStage.file_request,
                        file_name=filename,
                    )
                summary.failures.append(failure)
            finally:
                if failure is not None:
                    self._failure_logger(queued, failure)
                self.reporter.download_finished(task_key, status, failure)
                queue.task_done(queued.creator_key)


async def _download_job(
    queued: QueuedJob,
    client: httpx.AsyncClient,
    observer: ReporterDownloadObserver,
    *,
    temporary_client: httpx.AsyncClient,
    api_client: PawchiveClient | None,
    missing_files: MissingFileHistory | None,
) -> DownloaderRet[str]:
    job = queued.job
    if temporary := job.temporary:
        if temporary.output_conflict:
            raise TemporaryOutputConflict
        url = await temporary.source.resolve(temporary, api_client)
        refreshed = False
        while True:
            result = await TemporaryDownloader(
                url=url,
                path=job.path,
                client=temporary_client,
                designated_filename=job.alt_filename,
                server_path="",
            ).run(progress=observer)
            code = result.status_code
            if code not in _REJECTED_TEMPORARY_URL_STATUSES:
                if code is not None and (200 <= code < 400 or code == 416):
                    raise TemporaryFileUnavailable(code)
                return result
            if refreshed:
                raise TemporaryFileUnavailable(code)
            url = await temporary.source.resolve(temporary, api_client, rejected_url=url, status=code)
            refreshed = True
    downloader = Downloader(
        url=get_file_url(job.server_path),
        path=job.path,
        client=client,
        designated_filename=job.alt_filename,
        server_path=job.server_path,
        post=job.post,
        missing_files=missing_files,
    )
    return await downloader.run(progress=observer)


def _job_filename(job: Job) -> str | None:
    name = job.alt_filename or PurePosixPath(urlsplit(job.server_path).path).name
    return name[:500] if name else None
