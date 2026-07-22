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
from ktoolbox.reporting import ProgressReporter
from ktoolbox.webui.app import create_app
from ktoolbox.webui.task_executor import TaskExecutionSnapshot
from ktoolbox.webui.task_models import SyncTaskSpec, TaskRecord

PROJECT_ROOT = Path(tempfile.mkdtemp(prefix="ktoolbox-playwright-"))
PROJECT_ROOT.joinpath(".env").write_text(
    "KTOOLBOX_WEBUI__USERNAME=playwright\n"
    "KTOOLBOX_WEBUI__PASSWORD=fixture-password\n"
    "KTOOLBOX_WEBUI__OPEN_BROWSER=false\n",
    encoding="utf-8",
)
PROJECT_ROOT.joinpath("ktoolbox.toml").write_text(
    'schema_version = 1\n\n[[creators]]\nservice = "fanbox"\ncreator_id = "demo-studio"\n'
    "enabled = true\n",
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
            )
        ]

    async def get_creator_profile(self, service: str, creator_id: str) -> CreatorProfile:
        return CreatorProfile(id=creator_id, service=service, name="Demo Studio")

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
)
