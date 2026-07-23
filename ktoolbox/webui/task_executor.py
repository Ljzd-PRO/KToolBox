from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from ktoolbox.action import create_job_from_post, generate_post_path_name
from ktoolbox.api.client import PawchiveClient
from ktoolbox.api.errors import PawchiveNotFoundError
from ktoolbox.api.generated import Post, Revision
from ktoolbox.api.utils import create_pawchive_client
from ktoolbox.blocker import BlockerEngine
from ktoolbox.configuration import RuntimeContext
from ktoolbox.failures import (
    FailureStage,
    TaskExecutionError,
    classify_failure,
    failure_report,
)
from ktoolbox.job import JobRunner
from ktoolbox.project_config import ProjectConfiguration
from ktoolbox.reporting import ProgressReporter
from ktoolbox.sync import SyncCoordinator, SyncOptions
from ktoolbox.utils import parse_webpage_url
from ktoolbox.webui.task_models import DownloadTaskSpec, SyncTaskSpec, TaskRecord


@dataclass(frozen=True, slots=True)
class TaskExecutionSnapshot:
    runtime: RuntimeContext
    project: ProjectConfiguration

    def redacted(self) -> dict[str, object]:
        return {
            "environment": self.runtime.redacted_configuration(),
            "project": self.project.model_dump(mode="json"),
        }


TaskExecutor = Callable[
    [TaskRecord, TaskExecutionSnapshot, ProgressReporter],
    Awaitable[None],
]


class CoreTaskExecutor:
    """Execute persisted WebUI tasks through the same typed core used by the CLI."""

    async def __call__(
        self,
        task: TaskRecord,
        snapshot: TaskExecutionSnapshot,
        reporter: ProgressReporter,
    ) -> None:
        with snapshot.runtime.activate():
            if isinstance(task.spec, DownloadTaskSpec):
                await self._download(task.spec, reporter)
            else:
                await self._sync(task.spec, snapshot.project, reporter)

    async def _download(self, spec: DownloadTaskSpec, reporter: ProgressReporter) -> None:
        from ktoolbox.configuration import config

        service: str | None = None
        creator_id: str | None = None
        stage = FailureStage.job_generation
        try:
            service, creator_id, post_id, revision_id = self._download_identity(spec)
            stage = FailureStage.revisions if revision_id is not None else FailureStage.work_detail
            async with create_pawchive_client() as client:
                post = await _requested_post(client, service, creator_id, post_id, revision_id)
                stage = FailureStage.job_generation
                post_path = spec.output / generate_post_path_name(post)
                if revision_id is not None:
                    post_path = post_path / config.job.post_structure.revisions / revision_id
                jobs = await create_job_from_post(
                    post,
                    post_path,
                    dump_post_data=spec.dump_post_data,
                    client=client,
                )
                if revision_id is None and config.job.include_revisions:
                    stage = FailureStage.revisions
                    try:
                        revisions = await client.list_post_revisions(service, creator_id, post_id)
                    except PawchiveNotFoundError:
                        revisions = []
                    stage = FailureStage.job_generation
                    for revision in revisions:
                        revision_path = (
                            post_path / config.job.post_structure.revisions / generate_post_path_name(revision)
                        )
                        jobs.extend(
                            await create_job_from_post(
                                revision,
                                revision_path,
                                dump_post_data=spec.dump_post_data,
                                client=client,
                            )
                        )
        except Exception as error:
            item = classify_failure(
                error,
                stage=stage,
                platform=service,
                creator_id=creator_id,
            )
            raise TaskExecutionError(failure_report([item])) from error

        runner = JobRunner(job_list=jobs, reporter=reporter)
        await runner.start()
        if runner.summary.failed:
            raise TaskExecutionError(
                failure_report(
                    runner.summary.failures,
                    file_failures=runner.summary.failed,
                    summary=f"Download finished with {runner.summary.failed} file failures",
                )
            )

    async def _sync(
        self,
        spec: SyncTaskSpec,
        project: ProjectConfiguration,
        reporter: ProgressReporter,
    ) -> None:
        from ktoolbox.configuration import config

        async with create_pawchive_client() as client:
            summary = await SyncCoordinator(
                client,
                blocker_engine=BlockerEngine.from_specs(project.blockers),
                creator_concurrency=config.job.creator_concurrency,
                reporter=reporter,
            ).run(
                spec.creators,
                SyncOptions(
                    output=spec.output,
                    save_creator_indices=spec.save_creator_indices,
                    mix_posts=spec.mix_posts,
                    start_time=spec.start_time,
                    end_time=spec.end_time,
                    offset=spec.offset,
                    length=spec.length,
                    keywords=spec.keywords or set(config.job.keywords),
                    keywords_exclude=spec.keywords_exclude or set(config.job.keywords_exclude),
                ),
            )
        if not summary.successful:
            creator_failures = sum(not result.successful for result in summary.creators)
            items = [result.failure for result in summary.creators if result.failure is not None]
            items.extend(summary.downloads.failures)
            raise TaskExecutionError(
                failure_report(
                    items,
                    creator_failures=creator_failures,
                    file_failures=summary.downloads.failed,
                    summary=(
                        f"Synchronization finished with {creator_failures} creator failures "
                        f"and {summary.downloads.failed} file failures"
                    ),
                )
            )

    @staticmethod
    def _download_identity(spec: DownloadTaskSpec) -> tuple[str, str, str, str | None]:
        if spec.post:
            service, creator_id, post_id, parsed_revision = parse_webpage_url(spec.post)
            revision_id = parsed_revision or spec.revision_id
        else:
            service, creator_id, post_id, revision_id = (
                spec.service,
                spec.creator_id,
                spec.post_id,
                spec.revision_id,
            )
        if service is None or creator_id is None or post_id is None:
            raise ValueError("the post URL does not contain a service, creator, and post ID")
        return service, creator_id, post_id, revision_id


async def _requested_post(
    client: PawchiveClient,
    service: str,
    creator_id: str,
    post_id: str,
    revision_id: str | None,
) -> Post | Revision:
    if revision_id is None:
        return await client.get_post(service, creator_id, post_id)
    revisions = await client.list_post_revisions(service, creator_id, post_id)
    revision = next((item for item in revisions if str(item.revision_id) == revision_id), None)
    if revision is None:
        raise LookupError(f"revision {revision_id} was not found")
    return revision
