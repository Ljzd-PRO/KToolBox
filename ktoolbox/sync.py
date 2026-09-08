from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import aiofiles.os  # type: ignore[import-untyped]

from ktoolbox.action.job import CreatorJobGeneration, produce_jobs_from_creator
from ktoolbox.action.utils import generate_creator_path_name
from ktoolbox.api.client import PawchiveClient
from ktoolbox.automatic_sync import AutomaticSyncWindow
from ktoolbox.blocker import BlockerEngine
from ktoolbox.configuration import config
from ktoolbox.failures import FailureItem, FailureStage, classify_failure, generic_failure
from ktoolbox.job.model import Job
from ktoolbox.job.stream import DownloadSummary, DownloadWorkerPool, FairJobQueue
from ktoolbox.project_config import (
    CreatorReference,
    ProjectConfigError,
    ProjectConfiguration,
    ProjectNamingConfiguration,
    parse_creator_reference,
)
from ktoolbox.publication_time import PublishedTimePolicy
from ktoolbox.reporting import NullProgressReporter, ProgressReporter


@dataclass(frozen=True, slots=True)
class SyncOptions:
    output: Path = Path(".")
    save_creator_indices: bool = False
    mix_posts: bool | None = None
    download_file: bool | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    offset: int = 0
    length: int | None = None
    keywords: set[str] = field(default_factory=set)
    keywords_exclude: set[str] = field(default_factory=set)
    automatic_windows: dict[str, AutomaticSyncWindow] = field(default_factory=dict)


@dataclass(slots=True)
class CreatorSyncResult:
    creator: CreatorReference
    output: Path | None = None
    generation: CreatorJobGeneration | None = None
    error: str | None = None
    failure: FailureItem | None = None
    download_failures: int = 0

    @property
    def successful(self) -> bool:
        return self.error is None and self.download_failures == 0


@dataclass(slots=True)
class SyncSummary:
    creators: list[CreatorSyncResult]
    downloads: DownloadSummary

    @property
    def successful(self) -> bool:
        return all(result.successful for result in self.creators) and self.downloads.successful


def resolve_sync_targets(targets: list[str], configuration: ProjectConfiguration) -> list[CreatorReference]:
    resolved: list[CreatorReference] = []
    if targets:
        for target in targets:
            creator = configuration.find_creator(target)
            resolved.append(creator if creator is not None else parse_creator_reference(target))
    else:
        resolved.extend(creator for creator in configuration.creators if creator.enabled)

    unique: dict[str, CreatorReference] = {}
    for creator in resolved:
        unique.setdefault(creator.key.casefold(), creator)
    if not unique:
        raise ProjectConfigError("no creators selected; pass a creator or enable one in ktoolbox.toml")
    return list(unique.values())


class SyncCoordinator:
    """Coordinate bounded creator producers and a shared fair download pool."""

    def __init__(
        self,
        client: PawchiveClient,
        *,
        naming: ProjectNamingConfiguration | None = None,
        published_time: PublishedTimePolicy | None = None,
        blocker_engine: BlockerEngine | None = None,
        creator_concurrency: int = 4,
        download_pool: DownloadWorkerPool | None = None,
        lane_size: int | None = None,
        reporter: ProgressReporter | None = None,
    ) -> None:
        if creator_concurrency < 1:
            raise ValueError("creator concurrency must be positive")
        self.client = client
        self.naming = naming or ProjectNamingConfiguration()
        self.published_time = published_time or config.published_time.policy()
        self.blocker_engine = blocker_engine or BlockerEngine()
        self.creator_concurrency = creator_concurrency
        self.reporter = reporter or NullProgressReporter()
        self.download_pool = download_pool or DownloadWorkerPool(config.job.count, reporter=self.reporter)
        self.download_pool.reporter = self.reporter
        self.lane_size = lane_size or max(2, self.download_pool.concurrency)

    async def run(self, creators: list[CreatorReference], options: SyncOptions) -> SyncSummary:
        unique = {creator.key.casefold(): creator for creator in creators}
        if not unique:
            raise ProjectConfigError("no creators selected")
        unique_creators = list(unique.values())
        queue = FairJobQueue(self.lane_size)
        for creator in unique_creators:
            queue.register(creator.key)

        semaphore = asyncio.Semaphore(self.creator_concurrency)
        self.reporter.start()
        download_task = asyncio.create_task(self.download_pool.run(queue))
        producer_tasks = [
            asyncio.create_task(self._produce_creator(creator, options, queue, semaphore))
            for creator in unique_creators
        ]
        try:
            creator_results = await asyncio.gather(*producer_tasks)
            downloads = await download_task
            for result in creator_results:
                result.download_failures = downloads.creator_failures.get(result.creator.key, 0)
        except BaseException:
            for task in producer_tasks:
                task.cancel()
            for creator in unique_creators:
                await queue.close(creator.key)
            download_task.cancel()
            await asyncio.gather(*producer_tasks, download_task, return_exceptions=True)
            raise
        finally:
            self.reporter.stop()
        return SyncSummary(creators=creator_results, downloads=downloads)

    async def _produce_creator(
        self,
        creator: CreatorReference,
        options: SyncOptions,
        queue: FairJobQueue,
        semaphore: asyncio.Semaphore,
    ) -> CreatorSyncResult:
        result = CreatorSyncResult(creator=creator)
        stage = FailureStage.creator_profile
        self.reporter.creator_started(creator.key)
        try:
            async with semaphore:
                profile = await self.client.get_creator_profile(creator.service, creator.creator_id)
                dirname = generate_creator_path_name(
                    creator.service,
                    creator.creator_id,
                    profile.name,
                    self.naming,
                    alias=creator.alias,
                )
                creator_path = options.output / dirname
                await aiofiles.os.makedirs(creator_path, exist_ok=True)
                result.output = creator_path

                async def enqueue(job: Job) -> None:
                    await queue.put(creator.key, job)
                    self.reporter.job_queued(creator.key)

                stage = FailureStage.job_generation
                generation = await produce_jobs_from_creator(
                    creator.service,
                    creator.creator_id,
                    creator_path,
                    enqueue,
                    naming=self.naming,
                    published_time=self.published_time,
                    all_pages=options.length is None,
                    offset=options.offset,
                    length=options.length,
                    save_creator_indices=options.save_creator_indices,
                    mix_posts=options.mix_posts,
                    download_file=options.download_file,
                    start_time=options.start_time,
                    end_time=options.end_time,
                    keywords=options.keywords,
                    keywords_exclude=options.keywords_exclude,
                    post_filter=(
                        options.automatic_windows[creator.key].includes
                        if creator.key in options.automatic_windows
                        else None
                    ),
                    blocker_engine=self.blocker_engine,
                    client=self.client,
                )
                if generation:
                    result.generation = generation.data
                else:
                    result.failure = (
                        classify_failure(
                            generation.exception,
                            stage=stage,
                            platform=creator.service,
                            creator_id=creator.creator_id,
                        )
                        if generation.exception is not None
                        else generic_failure(
                            stage=stage,
                            message="Creator task generation failed",
                            platform=creator.service,
                            creator_id=creator.creator_id,
                        )
                    )
                    result.error = result.failure.message
        except asyncio.CancelledError:
            raise
        except Exception as error:
            result.failure = classify_failure(
                error,
                stage=stage,
                platform=creator.service,
                creator_id=creator.creator_id,
            )
            result.error = result.failure.message
        finally:
            await queue.close(creator.key)
            self.reporter.creator_finished(
                creator.key,
                result.error,
                result.failure,
                fetched_posts=result.generation.fetched_posts if result.generation is not None else None,
                accepted_posts=result.generation.accepted_posts if result.generation is not None else None,
            )
        return result
