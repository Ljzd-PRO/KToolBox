from __future__ import annotations

import asyncio
from contextlib import suppress
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ktoolbox._enum import RetCodeEnum
from ktoolbox.configuration import config
from ktoolbox.downloader.base import DownloaderRet
from ktoolbox.job import Job
from ktoolbox.job.runner import JobRunner


class FakeHTTPClient:
    calls: list[dict[str, object]] = []

    def __init__(self, **kwargs: object) -> None:
        self.calls.append(kwargs)

    async def __aenter__(self) -> FakeHTTPClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class FakeDownloader:
    instances: list[FakeDownloader] = []

    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.name = str(kwargs["designated_filename"])
        self.finished = True
        self.cancelled = False
        self.instances.append(self)

    async def run(self, **kwargs: object) -> DownloaderRet[str]:
        self.run_kwargs = kwargs
        if self.name == "error":
            raise RuntimeError("download failed")
        if self.name == "cancel":
            raise asyncio.CancelledError
        if self.name == "exists":
            return DownloaderRet(code=RetCodeEnum.FileExisted, message="exists")
        if self.name == "failure":
            return DownloaderRet(code=RetCodeEnum.GeneralFailure, message="failure")
        return DownloaderRet(data=self.name)

    def cancel(self) -> None:
        self.cancelled = True


def jobs(tmp_path: Path, *names: str) -> list[Job]:
    return [Job(path=tmp_path, alt_filename=name, server_path=f"/{name}.bin") for name in names]


@pytest.fixture(autouse=True)
def reset_fakes() -> None:
    FakeHTTPClient.calls.clear()
    FakeDownloader.instances.clear()
    config.job.count = 2


@pytest.mark.asyncio
async def test_runner_processes_all_result_and_exception_types(tmp_path: Path) -> None:
    config.downloader.session_key = "file-cookie"
    runner = JobRunner(
        job_list=jobs(tmp_path, "success", "exists", "failure", "error", "cancel"),
        progress=False,
    )
    assert runner.finished
    assert runner.waiting_size == 5
    assert isinstance(runner.downloaders, MappingProxyType)

    with (
        patch("ktoolbox.job.runner.httpx.AsyncClient", FakeHTTPClient),
        patch("ktoolbox.job.runner.Downloader", FakeDownloader),
    ):
        failed = await runner.start()

    assert failed == 2
    assert runner.waiting_size == 0
    assert runner.done_size == 5
    assert runner.processing_size == 0
    assert {item.name for item in FakeDownloader.instances} == {"success", "exists", "failure", "error", "cancel"}
    assert all(item.run_kwargs["progress"] is False for item in FakeDownloader.instances)
    assert FakeHTTPClient.calls
    assert all(call["cookies"] == {"session": "file-cookie"} for call in FakeHTTPClient.calls)
    with pytest.raises(TypeError):
        runner.downloaders[object()] = object()


@pytest.mark.asyncio
async def test_processor_updates_progress_and_legacy_existed_counter(tmp_path: Path) -> None:
    manager = Mock()
    runner = JobRunner(job_list=jobs(tmp_path, "exists", "failure", "success"), progress=False)
    runner._progress_manager = manager

    with (
        patch("ktoolbox.job.runner.httpx.AsyncClient", FakeHTTPClient),
        patch("ktoolbox.job.runner.Downloader", FakeDownloader),
    ):
        assert await runner.processor() == 1

    manager.increment_existed.assert_called_once_with(1)
    assert manager.update_job_progress.call_count == 3

    legacy_manager = SimpleNamespace(
        _existed_jobs=2,
        increment_existed=Mock(side_effect=AttributeError),
        update_job_progress=Mock(),
    )
    runner = JobRunner(job_list=jobs(tmp_path, "exists"), progress=False)
    runner._progress_manager = legacy_manager
    with (
        patch("ktoolbox.job.runner.httpx.AsyncClient", FakeHTTPClient),
        patch("ktoolbox.job.runner.Downloader", FakeDownloader),
    ):
        assert await runner.processor() == 0
    legacy_manager.update_job_progress.assert_any_call(existed=3)


@pytest.mark.asyncio
async def test_centralized_start_lifecycle_add_jobs_and_cancelled_processor(tmp_path: Path) -> None:
    manager = Mock()
    tqdm_class = object()
    with (
        patch("ktoolbox.job.runner.ProgressManager", return_value=manager) as progress_factory,
        patch("ktoolbox.job.runner.create_managed_tqdm_class", return_value=tqdm_class),
    ):
        runner = JobRunner(job_list=[], use_colors=False, use_emojis=False)
    progress_factory.assert_called_once_with(max_workers=2, use_colors=False, use_emojis=False)
    assert runner._tqdm_class is tqdm_class

    await runner.add_jobs(*jobs(tmp_path, "success"))
    manager.set_job_totals.assert_called_with(1)
    with (
        patch("ktoolbox.job.runner.httpx.AsyncClient", FakeHTTPClient),
        patch("ktoolbox.job.runner.Downloader", FakeDownloader),
        patch("ktoolbox.job.runner.setup_logger_for_progress") as setup_logger,
    ):
        assert await runner.start() == 0
    manager.start_display.assert_called_once_with()
    manager.stop_display.assert_called_once_with()
    setup_logger.assert_any_call(manager)
    setup_logger.assert_called_with(None)

    cancelled = JobRunner(progress=False)
    config.job.count = 1
    cancelled.processor = AsyncMock(side_effect=asyncio.CancelledError)
    assert await cancelled.start() == 0


@pytest.mark.asyncio
async def test_status_and_display_loops_cover_normal_and_cancel_paths(tmp_path: Path) -> None:
    runner = JobRunner(job_list=jobs(tmp_path, "waiting"), progress=False)
    runner._progress_manager = SimpleNamespace(_existed_jobs=3, update_display=Mock())

    async def finish_sleep(_: float) -> None:
        runner._job_queue.get_nowait()

    with patch("ktoolbox.job.runner.asyncio.sleep", side_effect=finish_sleep):
        await runner._watch_status()

    runner._job_queue.put_nowait(jobs(tmp_path, "waiting")[0])
    with patch("ktoolbox.job.runner.asyncio.sleep", side_effect=asyncio.CancelledError):
        await runner._watch_status()
        await runner._update_display_loop()
    runner._progress_manager.update_display.assert_called_once_with()


@pytest.mark.asyncio
async def test_add_jobs_properties_force_cancel_and_cancel_downloader(tmp_path: Path) -> None:
    manager = Mock()
    runner = JobRunner(progress=False)
    runner._progress_manager = manager
    added = jobs(tmp_path, "one", "two")
    await runner.add_jobs(*added)
    assert runner.waiting_size == 2
    manager.set_job_totals.assert_called_once_with(2)

    gate = asyncio.Event()

    async def wait_forever() -> None:
        await gate.wait()

    task = asyncio.create_task(wait_forever())
    target = Mock()
    target.finished = False
    runner._downloaders_with_task[target] = task
    assert runner.processing_size == 1
    assert await runner.cancel_downloader(target) is True
    target.cancel.assert_called_once_with()
    with suppress(asyncio.CancelledError):
        await task

    completed = asyncio.create_task(asyncio.sleep(0))
    await completed
    done_target = Mock()
    done_target.finished = False
    runner._downloaders_with_task[done_target] = completed
    assert await runner.cancel_downloader(done_target) is True
    done_target.cancel.assert_not_called()

    direct = asyncio.create_task(wait_forever())
    assert await JobRunner._force_cancel(direct) is True
    with suppress(asyncio.CancelledError):
        await direct
