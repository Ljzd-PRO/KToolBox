from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ktoolbox.job.model import Job
from ktoolbox.job.runner import JobRunner
from ktoolbox.job.stream import DownloadSummary


def jobs(tmp_path: Path, *names: str) -> list[Job]:
    return [Job(path=tmp_path, alt_filename=name, server_path=f"/{name}.bin") for name in names]


async def test_runner_uses_shared_pool_and_reports_finite_jobs(tmp_path: Path) -> None:
    reporter = Mock()
    pool = SimpleNamespace(run=AsyncMock(return_value=DownloadSummary(total=3, completed=2, failed=1)))
    runner = JobRunner(job_list=jobs(tmp_path, "one", "two", "three"), reporter=reporter, concurrency=2)

    assert runner.finished
    assert runner.waiting_size == 3
    with patch("ktoolbox.job.runner.DownloadWorkerPool", return_value=pool) as pool_type:
        assert await runner.start() == 1

    pool_type.assert_called_once_with(2, reporter=reporter)
    reporter.start.assert_called_once_with()
    reporter.stop.assert_called_once_with()
    assert reporter.job_queued.call_count == 3
    assert runner.done_size == 3
    assert runner.waiting_size == 0
    assert runner.summary.failed == 1


async def test_runner_adds_jobs_before_start_and_rejects_changes_while_running(tmp_path: Path) -> None:
    reporter = Mock()
    started = asyncio.Event()
    release = asyncio.Event()

    async def run(queue) -> DownloadSummary:
        started.set()
        await release.wait()
        return DownloadSummary(total=1, completed=1)

    pool = SimpleNamespace(run=run)
    runner = JobRunner(progress=False, reporter=reporter)
    await runner.add_jobs(*jobs(tmp_path, "one"))
    with patch("ktoolbox.job.runner.DownloadWorkerPool", return_value=pool):
        task = asyncio.create_task(runner.start())
        await started.wait()
        assert not runner.finished
        with pytest.raises(RuntimeError, match="cannot add jobs"):
            await runner.add_jobs(*jobs(tmp_path, "late"))
        release.set()
        assert await task == 0
    assert runner.finished


async def test_runner_stops_reporter_when_pool_is_cancelled(tmp_path: Path) -> None:
    reporter = Mock()
    pool = SimpleNamespace(run=AsyncMock(side_effect=asyncio.CancelledError))
    runner = JobRunner(job_list=jobs(tmp_path, "one"), reporter=reporter)
    with patch("ktoolbox.job.runner.DownloadWorkerPool", return_value=pool):
        with pytest.raises(asyncio.CancelledError):
            await runner.start()
    reporter.stop.assert_called_once_with()
