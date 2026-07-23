from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from ktoolbox._enum import RetCodeEnum
from ktoolbox.action.base import ActionRet
from ktoolbox.action.job import CreatorJobGeneration
from ktoolbox.api.generated import CreatorProfile
from ktoolbox.blocker import BlockerEngine
from ktoolbox.downloader.base import DownloaderRet
from ktoolbox.failures import FailureCode, FailureItem, FailureStage
from ktoolbox.job.model import Job
from ktoolbox.job.stream import DownloadWorkerPool, QueuedJob
from ktoolbox.project_config import CreatorReference, ProjectConfigError, ProjectConfiguration
from ktoolbox.reporting import NullProgressReporter
from ktoolbox.sync import SyncCoordinator, SyncOptions, resolve_sync_targets


def creator(creator_id: str, *, alias: str | None = None, enabled: bool = True) -> CreatorReference:
    return CreatorReference(service="fanbox", creator_id=creator_id, alias=alias, enabled=enabled)


def test_resolve_sync_targets_uses_roster_aliases_enabled_state_and_deduplication() -> None:
    configuration = ProjectConfiguration(creators=[creator("1", alias="first"), creator("2", enabled=False)])
    assert [item.key for item in resolve_sync_targets([], configuration)] == ["fanbox:1"]
    selected = resolve_sync_targets(["first", "fanbox:2", "https://pawchive.pw/fanbox/user/1"], configuration)
    assert [item.key for item in selected] == ["fanbox:1", "fanbox:2"]
    with pytest.raises(ProjectConfigError, match="no creators selected"):
        resolve_sync_targets([], ProjectConfiguration())


async def test_sync_coordinator_bounds_creators_and_downloads_all_jobs(tmp_path: Path) -> None:
    active = 0
    maximum = 0
    two_started = asyncio.Event()
    release = asyncio.Event()
    downloaded: list[str] = []

    class Client:
        async def get_creator_profile(self, service: str, creator_id: str) -> CreatorProfile:
            return CreatorProfile(id=creator_id, service=service, name=f"Artist {creator_id}")

    async def produce(service: str, creator_id: str, path: Path, sink, **kwargs: object) -> ActionRet:
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        if maximum == 2:
            two_started.set()
        await two_started.wait()
        await release.wait()
        await sink(Job(path=path, server_path=f"/{creator_id}", alt_filename=creator_id))
        active -= 1
        return ActionRet(data=CreatorJobGeneration(fetched_posts=1, accepted_posts=1, generated_jobs=1))

    async def download(queued: QueuedJob, client, observer) -> DownloaderRet[str]:
        downloaded.append(queued.creator_key)
        return DownloaderRet(data=queued.job.alt_filename)

    coordinator = SyncCoordinator(
        Client(),  # type: ignore[arg-type]
        creator_concurrency=2,
        download_pool=DownloadWorkerPool(2, download=download),
    )
    with patch("ktoolbox.sync.produce_jobs_from_creator", produce):
        task = asyncio.create_task(
            coordinator.run([creator("1"), creator("2"), creator("3")], SyncOptions(output=tmp_path))
        )
        await asyncio.wait_for(two_started.wait(), timeout=1)
        assert maximum == 2
        release.set()
        summary = await task

    assert summary.successful
    assert summary.downloads.completed == 3
    assert set(downloaded) == {"fanbox:1", "fanbox:2", "fanbox:3"}
    assert {result.output.name for result in summary.creators if result.output} == {
        "Artist 1 [fanbox-1]",
        "Artist 2 [fanbox-2]",
        "Artist 3 [fanbox-3]",
    }


async def test_sync_coordinator_isolates_creator_failure(tmp_path: Path) -> None:
    client = SimpleNamespace(
        get_creator_profile=AsyncMock(
            side_effect=lambda service, creator_id: CreatorProfile(
                id=creator_id,
                service=service,
                name=f"Artist {creator_id}",
            )
        )
    )

    async def produce(service: str, creator_id: str, path: Path, sink, **kwargs: object) -> ActionRet:
        if creator_id == "bad":
            return ActionRet(code=RetCodeEnum.GeneralFailure, message="API failed")
        await sink(Job(path=path, server_path="/ok", alt_filename="ok"))
        return ActionRet(data=CreatorJobGeneration(generated_jobs=1))

    async def download(queued: QueuedJob, client, observer) -> DownloaderRet[str]:
        return DownloaderRet(data="ok")

    coordinator = SyncCoordinator(
        client,
        download_pool=DownloadWorkerPool(1, download=download),
    )
    with patch("ktoolbox.sync.produce_jobs_from_creator", produce):
        summary = await coordinator.run([creator("bad"), creator("good")], SyncOptions(output=tmp_path))

    assert not summary.successful
    assert summary.downloads.completed == 1
    assert [result.error for result in summary.creators] == ["Creator task generation failed", None]
    assert summary.creators[0].failure is not None
    assert summary.creators[0].failure.code is FailureCode.unknown
    assert summary.creators[0].failure.stage is FailureStage.job_generation


async def test_sync_coordinator_rejects_empty_target_list() -> None:
    with pytest.raises(ValueError, match="creator concurrency must be positive"):
        SyncCoordinator(SimpleNamespace(), creator_concurrency=0)  # type: ignore[arg-type]

    coordinator = SyncCoordinator(SimpleNamespace())  # type: ignore[arg-type]
    with pytest.raises(ProjectConfigError, match="no creators selected"):
        await coordinator.run([], SyncOptions())


async def test_sync_coordinator_captures_unexpected_creator_failure(tmp_path: Path) -> None:
    client = SimpleNamespace(get_creator_profile=AsyncMock(side_effect=RuntimeError("profile failed")))

    async def download(queued: QueuedJob, client, observer) -> DownloaderRet[str]:
        return DownloaderRet(data="unused")

    coordinator = SyncCoordinator(
        client,
        blocker_engine=BlockerEngine(),
        download_pool=DownloadWorkerPool(1, download=download),
        lane_size=1,
    )
    summary = await coordinator.run([creator("broken")], SyncOptions(output=tmp_path))

    assert not summary.successful
    assert summary.creators[0].error == "Unexpected RuntimeError during creator profile"
    assert summary.creators[0].failure is not None
    assert summary.creators[0].failure.stage is FailureStage.creator_profile
    assert summary.downloads.total == 0


async def test_sync_coordinator_cancellation_closes_producers_and_download_pool(tmp_path: Path) -> None:
    profile_started = asyncio.Event()

    class Client:
        async def get_creator_profile(self, service: str, creator_id: str) -> CreatorProfile:
            profile_started.set()
            await asyncio.Event().wait()
            raise AssertionError("unreachable")

    class Reporter(NullProgressReporter):
        def __init__(self) -> None:
            self.started = 0
            self.stopped = 0
            self.finished: list[tuple[str, str | None]] = []

        def start(self) -> None:
            self.started += 1

        def stop(self) -> None:
            self.stopped += 1

        def creator_finished(
            self,
            creator_key: str,
            error: str | None = None,
            failure: FailureItem | None = None,
        ) -> None:
            assert failure is None
            self.finished.append((creator_key, error))

    reporter = Reporter()
    coordinator = SyncCoordinator(Client(), reporter=reporter)  # type: ignore[arg-type]
    task = asyncio.create_task(coordinator.run([creator("cancelled")], SyncOptions(output=tmp_path)))
    await asyncio.wait_for(profile_started.wait(), timeout=1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert reporter.started == reporter.stopped == 1
    assert reporter.finished == [("fanbox:cancelled", None)]
