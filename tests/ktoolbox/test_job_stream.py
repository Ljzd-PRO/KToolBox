from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ktoolbox._enum import RetCodeEnum
from ktoolbox.downloader.base import DownloaderRet
from ktoolbox.failures import FailureCode, FailureItem, FailureStage
from ktoolbox.job.model import Job
from ktoolbox.job.stream import DownloadWorkerPool, FairJobQueue, QueuedJob
from ktoolbox.reporting import NullProgressReporter, ReporterDownloadObserver


def job(path: Path, name: str) -> Job:
    return Job(path=path, server_path=f"/{name}", alt_filename=name)


async def test_fair_queue_round_robins_ready_creator_lanes(tmp_path: Path) -> None:
    queue = FairJobQueue(lane_size=2)
    queue.register("fanbox:a")
    queue.register("fanbox:b")
    await queue.put("fanbox:a", job(tmp_path, "a1"))
    await queue.put("fanbox:a", job(tmp_path, "a2"))
    await queue.put("fanbox:b", job(tmp_path, "b1"))
    await queue.put("fanbox:b", job(tmp_path, "b2"))
    await queue.close("fanbox:a")
    await queue.close("fanbox:b")

    received: list[str] = []
    while queued := await queue.get():
        received.append(queued.job.alt_filename or "")
        queue.task_done(queued.creator_key)

    assert received == ["a1", "b1", "a2", "b2"]
    assert queue.waiting_size == 0


async def test_fair_queue_waits_for_open_empty_lane(tmp_path: Path) -> None:
    queue = FairJobQueue(lane_size=1)
    queue.register("fanbox:a")
    pending = asyncio.create_task(queue.get())
    await asyncio.sleep(0)
    assert not pending.done()
    await queue.put("fanbox:a", job(tmp_path, "later"))
    queued = await pending
    assert queued is not None and queued.job.alt_filename == "later"
    queue.task_done("fanbox:a")
    await queue.close("fanbox:a")
    assert await queue.get() is None


async def test_fair_queue_applies_per_creator_backpressure(tmp_path: Path) -> None:
    queue = FairJobQueue(lane_size=1)
    queue.register("fanbox:a")
    await queue.put("fanbox:a", job(tmp_path, "first"))
    blocked_put = asyncio.create_task(queue.put("fanbox:a", job(tmp_path, "second")))
    await asyncio.sleep(0)
    assert not blocked_put.done()
    first = await queue.get()
    assert first is not None
    queue.task_done(first.creator_key)
    await asyncio.wait_for(blocked_put, timeout=1)
    await queue.close("fanbox:a")


async def test_queue_and_pool_reject_invalid_lifecycle_operations(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="lane_size must be positive"):
        FairJobQueue(0)
    with pytest.raises(ValueError, match="concurrency must be positive"):
        DownloadWorkerPool(0)

    queue = FairJobQueue(1)
    queue.register("fanbox:a")
    with pytest.raises(ValueError, match="already registered"):
        queue.register("fanbox:a")
    await queue.close("fanbox:a")
    with pytest.raises(RuntimeError, match="queue is closed"):
        await queue.put("fanbox:a", job(tmp_path, "late"))


async def test_download_pool_bounds_concurrency_and_reuses_client(tmp_path: Path) -> None:
    queue = FairJobQueue(lane_size=4)
    queue.register("fanbox:a")
    for index in range(4):
        await queue.put("fanbox:a", job(tmp_path, str(index)))
    await queue.close("fanbox:a")

    active = 0
    maximum = 0
    started = asyncio.Event()
    release = asyncio.Event()
    clients: set[int] = set()

    async def download(queued: QueuedJob, client, observer) -> DownloaderRet[str]:
        nonlocal active, maximum
        clients.add(id(client))
        active += 1
        maximum = max(maximum, active)
        if maximum == 2:
            started.set()
        await release.wait()
        active -= 1
        return DownloaderRet(data=queued.job.alt_filename)

    task = asyncio.create_task(DownloadWorkerPool(2, download=download).run(queue))
    await asyncio.wait_for(started.wait(), timeout=1)
    release.set()
    summary = await task

    assert maximum == 2
    assert len(clients) == 1
    assert summary.total == summary.completed == 4
    assert summary.successful


async def test_download_pool_classifies_results_and_exceptions(tmp_path: Path) -> None:
    queue = FairJobQueue(lane_size=4)
    queue.register("fanbox:a")
    for name in ("exists", "empty-success", "failure", "exception"):
        await queue.put("fanbox:a", job(tmp_path, name))
    await queue.close("fanbox:a")

    async def download(queued: QueuedJob, client, observer) -> DownloaderRet[str]:
        if queued.job.alt_filename == "exists":
            return DownloaderRet(code=RetCodeEnum.FileExisted)
        if queued.job.alt_filename == "empty-success":
            return DownloaderRet()
        if queued.job.alt_filename == "failure":
            return DownloaderRet(code=RetCodeEnum.GeneralFailure, message="failed")
        raise RuntimeError("broken")

    summary = await DownloadWorkerPool(2, download=download).run(queue)
    assert summary.total == 4
    assert summary.completed == 1
    assert summary.existed == 1
    assert summary.failed == 2
    assert [failure.code for failure in summary.failures] == [
        FailureCode.download_failed,
        FailureCode.unknown,
    ]
    assert [failure.file_name for failure in summary.failures] == ["failure", "exception"]
    assert all(failure.stage is FailureStage.file_request for failure in summary.failures)
    assert not summary.successful


async def test_download_pool_overlaps_ready_creators(tmp_path: Path) -> None:
    queue = FairJobQueue(lane_size=2)
    for creator_key in ("fanbox:a", "fanbox:b"):
        queue.register(creator_key)
        await queue.put(creator_key, job(tmp_path, creator_key))
        await queue.close(creator_key)

    active_creators: set[str] = set()
    both_started = asyncio.Event()
    release = asyncio.Event()

    async def download(queued: QueuedJob, client, observer) -> DownloaderRet[str]:
        active_creators.add(queued.creator_key)
        if len(active_creators) == 2:
            both_started.set()
        await release.wait()
        return DownloaderRet(data=queued.job.alt_filename)

    task = asyncio.create_task(DownloadWorkerPool(2, download=download).run(queue))
    await asyncio.wait_for(both_started.wait(), timeout=1)
    assert active_creators == {"fanbox:a", "fanbox:b"}
    release.set()
    assert (await task).completed == 2


async def test_download_pool_cancels_workers_and_reports_cancelled_status(tmp_path: Path) -> None:
    queue = FairJobQueue(1)
    queue.register("fanbox:a")
    await queue.put("fanbox:a", job(tmp_path, "cancel"))
    await queue.close("fanbox:a")
    started = asyncio.Event()

    class Reporter(NullProgressReporter):
        def __init__(self) -> None:
            self.finished: list[tuple[str, str]] = []

        def download_finished(
            self,
            task_key: str,
            status: str,
            failure: FailureItem | None = None,
        ) -> None:
            assert failure is None
            self.finished.append((task_key, status))

    reporter = Reporter()

    async def download(queued: QueuedJob, client, observer) -> DownloaderRet[str]:
        started.set()
        await asyncio.Event().wait()
        return DownloaderRet(data="unreachable")

    task = asyncio.create_task(DownloadWorkerPool(2, download=download, reporter=reporter).run(queue))
    await asyncio.wait_for(started.wait(), timeout=1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert reporter.finished == [("download-1", "cancelled")]


async def test_download_pool_classifies_http_and_disk_failures(tmp_path: Path) -> None:
    queue = FairJobQueue(lane_size=2)
    queue.register("fanbox:a")
    for name in ("limited", "disk"):
        await queue.put("fanbox:a", job(tmp_path, name))
    await queue.close("fanbox:a")

    async def download(queued: QueuedJob, client, observer) -> DownloaderRet[str]:
        if queued.job.alt_filename == "limited":
            return DownloaderRet(code=RetCodeEnum.GeneralFailure, status_code=429)
        raise OSError(28, "No space left on device")

    summary = await DownloadWorkerPool(1, download=download).run(queue)

    assert [failure.code for failure in summary.failures] == [
        FailureCode.rate_limited,
        FailureCode.disk_full,
    ]
    assert [failure.stage for failure in summary.failures] == [
        FailureStage.file_request,
        FailureStage.file_write,
    ]
    assert [failure.retryable for failure in summary.failures] == [True, False]


async def test_default_download_callable_builds_downloader_and_observer(tmp_path: Path) -> None:
    queue = FairJobQueue(1)
    queue.register("fanbox:a")
    queued_job = job(tmp_path, "default.bin")
    await queue.put("fanbox:a", queued_job)
    await queue.close("fanbox:a")

    with patch("ktoolbox.job.stream.Downloader") as downloader_type:
        downloader = downloader_type.return_value
        downloader.run = AsyncMock(return_value=DownloaderRet(data="default.bin"))
        summary = await DownloadWorkerPool(1).run(queue)

    assert summary.completed == 1
    assert downloader_type.call_args.kwargs["path"] == tmp_path
    assert downloader_type.call_args.kwargs["designated_filename"] == "default.bin"
    observer = downloader.run.await_args.kwargs["progress"]
    assert isinstance(observer, ReporterDownloadObserver)
