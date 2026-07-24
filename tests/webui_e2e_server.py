from __future__ import annotations

import asyncio
import tempfile
from contextlib import AbstractAsyncContextManager
from importlib import import_module
from pathlib import Path
from typing import Any, cast

import httpx

from ktoolbox.api.generated import CreatorProfile, CreatorSummary, Post, Revision
from ktoolbox.configuration import RuntimeContext
from ktoolbox.failures import (
    FailureCode,
    FailureStage,
    TaskExecutionError,
    failure_report,
    generic_failure,
)
from ktoolbox.reporting import ProgressReporter
from ktoolbox.webui.app import create_app
from ktoolbox.webui.filesystem import FilesystemBrowser
from ktoolbox.webui.task_executor import TaskExecutionSnapshot
from ktoolbox.webui.task_models import SyncTaskSpec, TaskRecord

HOST_ROOT = Path(tempfile.mkdtemp(prefix="ktoolbox-playwright-host-"))
PROJECT_ROOT = HOST_ROOT / "project"
PROJECT_ROOT.mkdir()
HOST_HOME = HOST_ROOT / "home"
HOST_HOME.mkdir()
(HOST_ROOT / "shared").mkdir()
(PROJECT_ROOT / "downloads").mkdir()
(PROJECT_ROOT / "资料").mkdir()
(PROJECT_ROOT / "content.txt").write_text("fixture content\n", encoding="utf-8")
(PROJECT_ROOT / ".hidden-fixture").write_text("hidden\n", encoding="utf-8")
PROJECT_ROOT.joinpath(".env").write_text(
    "KTOOLBOX_WEBUI__USERNAME=playwright\n"
    "KTOOLBOX_WEBUI__PASSWORD=fixture-password\n"
    "KTOOLBOX_WEBUI__OPEN_BROWSER=false\n",
    encoding="utf-8",
)
PROJECT_ROOT.joinpath("ktoolbox.toml").write_text(
    'schema_version = 1\n\n[[creators]]\nservice = "fanbox"\ncreator_id = "demo-studio"\n'
    "enabled = true\n\n"
    '[[creators]]\nservice = "patreon"\ncreator_id = "alpha-atelier"\n'
    'alias = "Priority reference"\nenabled = true\n\n'
    '[[creators]]\nservice = "pixiv"\ncreator_id = "studio-10"\n'
    "enabled = false\n",
    encoding="utf-8",
)


class FixtureClient(AbstractAsyncContextManager["FixtureClient"]):
    async def __aenter__(self) -> FixtureClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def list_creators(self) -> list[CreatorSummary]:
        return [
            CreatorSummary(
                id="demo-studio",
                service="fanbox",
                name="Demo Studio",
                favorited=0,
                indexed=0,
                updated=0,
            ),
            CreatorSummary(
                id="alpha-atelier",
                service="patreon",
                name="Alpha Atelier",
                favorited=0,
                indexed=0,
                updated=0,
            ),
            CreatorSummary(
                id="studio-10",
                service="pixiv",
                name="第 10 工作室",
                favorited=0,
                indexed=0,
                updated=0,
            ),
        ]

    async def get_creator_profile(self, service: str, creator_id: str) -> CreatorProfile:
        names = {
            ("fanbox", "demo-studio"): "Demo Studio",
            ("patreon", "alpha-atelier"): "Alpha Atelier",
            ("pixiv", "studio-10"): "第 10 工作室",
        }
        return CreatorProfile(id=creator_id, service=service, name=names.get((service, creator_id), creator_id))

    async def list_creator_posts(self, service: str, creator_id: str, **_: object) -> list[Post]:
        return [
            Post(
                id="fiction-1001",
                user=creator_id,
                service=service,
                title="Fictional project study",
                content="Harmless fixture text for browser verification.",
                published="2026-07-20T08:30:00Z",
            )
        ]

    async def get_post(self, service: str, creator_id: str, post_id: str) -> Post:
        return (await self.list_creator_posts(service, creator_id))[0].model_copy(update={"id": post_id})

    async def list_post_revisions(self, service: str, creator_id: str, post_id: str) -> list[Revision]:
        return [Revision(id=post_id, user=creator_id, service=service, revision_id=1, title="Fictional revision")]

    async def get_app_version(self) -> str:
        return "playwright-fixture"


class FixtureExecutor:
    async def __call__(
        self,
        task: TaskRecord,
        _snapshot: TaskExecutionSnapshot,
        reporter: ProgressReporter,
    ) -> None:
        if task.spec.output.name == "failure-fixture":
            creator = "fanbox:demo-studio"
            failure = generic_failure(
                code=FailureCode.response_incompatible,
                stage=FailureStage.work_list,
                message="Pawchive returned data in an unsupported format",
                platform="fanbox",
                creator_id="demo-studio",
            ).model_copy(
                update={
                    "operation": "list_creator_posts",
                    "fields": ["items.8.tags"],
                }
            )
            reporter.start()
            reporter.creator_started(creator)
            reporter.creator_finished(creator, failure.message, failure)
            reporter.stop()
            raise TaskExecutionError(
                failure_report(
                    [failure],
                    creator_failures=1,
                    summary="Synchronization finished with 1 creator failure and 0 file failures",
                )
            )

        if task.spec.output.name == "retry-fixture":
            creator = "fanbox:retry-demo"
            reporter.start()
            reporter.creator_started(creator)
            for index in range(18):
                task_key = f"retry-{index}"
                reporter.job_queued(creator)
                reporter.download_retrying(
                    task_key,
                    creator,
                    f"fictional-retry-file-{index + 1:02d}.zip",
                    index % 4,
                    (429, 500, 503, None)[index % 4],
                )
            await asyncio.sleep(30)
            for index in range(18):
                reporter.download_finished(f"retry-{index}", "completed")
            reporter.creator_finished(creator)
            reporter.stop()
            return

        if task.spec.output.name == "live-layout-fixture":
            creators = ["fanbox:demo-studio", "patreon:alpha-atelier"]
            reporter.start()
            for creator in creators:
                reporter.creator_started(creator)
            for index in range(8):
                creator = creators[index % len(creators)]
                reporter.job_queued(creator)
                reporter.download_started(
                    f"live-{index}",
                    creator,
                    f"fictional-active-file-{index + 1:02d}.zip",
                    1024 * 1024 if index < 4 else 2 * 1024 * 1024,
                    0,
                )
            for step in range(64):
                await asyncio.sleep(0.25)
                for index in range(4 if step >= 32 else 8):
                    task_index = index + 4 if step >= 32 else index
                    reporter.download_advanced(f"live-{task_index}", 32 * 1024)
                if step == 31:
                    for index in range(4):
                        reporter.download_finished(f"live-{index}", "completed")
            for index in range(4, 8):
                reporter.download_finished(f"live-{index}", "completed")
            for creator in creators:
                reporter.creator_finished(creator)
            reporter.stop()
            return

        transport = httpx.MockTransport(lambda __: httpx.Response(200, json={"fixture": True}))
        async with httpx.AsyncClient(transport=transport) as client:
            await client.get("https://fixture.invalid/metadata")

        creators = (
            [creator.key for creator in task.spec.creators]
            if isinstance(task.spec, SyncTaskSpec)
            else [f"{task.spec.service}:{task.spec.creator_id}"]
        )
        creators = creators or ["fanbox:demo-studio"]
        reporter.start()
        for creator in creators:
            reporter.creator_started(creator)
            reporter.job_queued(creator)
        reporter.download_started("fixture", creators[0], "fictional-long-responsive-filename.zip", 1024 * 1024, 0)
        for _step in range(64):
            await asyncio.sleep(0.08)
            reporter.download_advanced("fixture", 16 * 1024)
        reporter.download_finished("fixture", "completed")
        for creator in creators:
            reporter.creator_finished(creator)
        reporter.stop()


pawchive_module = cast(Any, import_module("ktoolbox.webui.pawchive_routes"))
pawchive_module.create_pawchive_client = FixtureClient
app = create_app(
    RuntimeContext.from_project(PROJECT_ROOT),
    task_executor=FixtureExecutor(),
    creator_client_factory=FixtureClient,
    filesystem_browser=FilesystemBrowser(
        PROJECT_ROOT,
        home=HOST_HOME,
        host_roots=(HOST_ROOT,),
        restrict_host_to_roots=True,
    ),
)
