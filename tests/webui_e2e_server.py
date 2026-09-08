from __future__ import annotations

import asyncio
import hashlib
import io
import json
import os
import sqlite3
import tempfile
from contextlib import AbstractAsyncContextManager
from importlib import import_module
from pathlib import Path
from typing import Any, cast

import httpx
from PIL import Image, ImageDraw

from ktoolbox.api.generated import CreatorProfile, CreatorSummary, FileReference, Post, Revision
from ktoolbox.configuration import RuntimeContext
from ktoolbox.failures import (
    FailureCode,
    FailureStage,
    TaskExecutionError,
    failure_report,
    generic_failure,
)
from ktoolbox.project_config import ProjectNamingConfiguration
from ktoolbox.reporting import ProgressReporter
from ktoolbox.webui.app import create_app
from ktoolbox.webui.filesystem import FilesystemBrowser
from ktoolbox.webui.media import MediaProxyService
from ktoolbox.webui.task_executor import TaskExecutionSnapshot
from ktoolbox.webui.task_models import SyncTaskSpec, TaskRecord
from tests.webui_showcase_data import SHOWCASE_CREATOR_BY_KEY, SHOWCASE_CREATORS

SHOWCASE_MODE = os.environ.get("KTOOLBOX_SHOWCASE") == "1"
HOST_ROOT = Path(tempfile.mkdtemp(prefix="ktoolbox-playwright-host-"))
PROJECT_ROOT = HOST_ROOT / ("Pawchive Showcase" if SHOWCASE_MODE else "project")
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
    "KTOOLBOX_WEBUI__OPEN_BROWSER=false\n"
    "KTOOLBOX_PUBLISHED_TIME__TARGET_TIMEZONE=Asia/Shanghai\n"
    "KTOOLBOX_PUBLISHED_TIME__FALLBACK_SERVICE_TIMEZONE=UTC\n"
    "KTOOLBOX_PUBLISHED_TIME__SERVICE_TIMEZONES__FANBOX=Asia/Tokyo\n"
    "KTOOLBOX_PUBLISHED_TIME__SERVICE_TIMEZONES__PATREON=UTC\n",
    encoding="utf-8",
)
if SHOWCASE_MODE:
    project_configuration = (
        'schema_version = 3\n\n[[creators]]\nservice = "fanbox"\ncreator_id = "476249"\n'
        "enabled = true\n\n"
        '[[creators]]\nservice = "fanbox"\ncreator_id = "6570768"\n'
        'alias = "重点关注"\nenabled = true\n\n'
        '[[creators]]\nservice = "fanbox"\ncreator_id = "6005584"\n'
        "enabled = false\n\n"
        "[[automatic_sync]]\n"
        'id = "daily-pawchive-check"\n'
        'name = "每日更新检查"\n'
        "enabled = true\n"
        'creators = ["fanbox:476249", "fanbox:6570768"]\n'
        'initial_start_date = "2026-07-01"\n\n'
        "[automatic_sync.schedule]\n"
        'kind = "cron"\n'
        'expression = "0 3 * * *"\n'
        'timezone = "Asia/Shanghai"\n\n'
        "[automatic_sync.options]\n"
        'output = "downloads"\n'
        "save_creator_indices = true\n\n"
        "[[automatic_sync]]\n"
        'id = "weekly-archive-check"\n'
        'name = "每周归档检查"\n'
        "enabled = false\n"
        'creators = ["fanbox:6005584"]\n\n'
        "[automatic_sync.schedule]\n"
        'kind = "interval"\n'
        "every = 7\n"
        'unit = "days"\n'
        'timezone = "Asia/Tokyo"\n\n'
        "[automatic_sync.options]\n"
        'output = "downloads"\n\n'
        "[naming]\n"
        'creator_dirname_format = "{creator_name} ({service}-{creator_id})"\n'
    )
else:
    project_configuration = (
        'schema_version = 3\n\n[[creators]]\nservice = "fanbox"\ncreator_id = "demo-studio"\n'
        "enabled = true\n\n"
        '[[creators]]\nservice = "patreon"\ncreator_id = "alpha-atelier"\n'
        'alias = "Priority reference"\nenabled = true\n\n'
        '[[creators]]\nservice = "pixiv"\ncreator_id = "studio-10"\n'
        "enabled = false\n\n"
        "[[automatic_sync]]\n"
        'id = "daily-studios"\n'
        'name = "Daily studios"\n'
        "enabled = true\n"
        'creators = ["fanbox:demo-studio", "patreon:alpha-atelier"]\n'
        'initial_start_date = "2026-07-01"\n\n'
        "[automatic_sync.schedule]\n"
        'kind = "cron"\n'
        'expression = "0 3 * * *"\n'
        'timezone = "Asia/Shanghai"\n\n'
        "[automatic_sync.options]\n"
        'output = "downloads"\n'
        "save_creator_indices = true\n\n"
        "[[automatic_sync]]\n"
        'id = "weekly-reference"\n'
        'name = "Weekly reference"\n'
        "enabled = false\n"
        'creators = ["pixiv:studio-10"]\n\n'
        "[automatic_sync.schedule]\n"
        'kind = "interval"\n'
        "every = 7\n"
        'unit = "days"\n'
        'timezone = "Asia/Tokyo"\n\n'
        "[automatic_sync.options]\n"
        'output = "downloads"\n\n'
        "[naming]\n"
        'creator_dirname_format = "{creator_name} ({service}-{creator_id})"\n'
    )
PROJECT_ROOT.joinpath("ktoolbox.toml").write_text(project_configuration, encoding="utf-8")


def _fixture_image(width: int, height: int, image_format: str, seed: int) -> bytes:
    palettes = (
        ((219, 234, 254), (37, 99, 235), (20, 184, 166), (15, 23, 42)),
        ((220, 252, 231), (5, 150, 105), (234, 179, 8), (20, 83, 45)),
        ((243, 232, 255), (126, 34, 206), (14, 165, 233), (59, 7, 100)),
        ((255, 228, 230), (225, 29, 72), (249, 115, 22), (76, 5, 25)),
    )
    background, primary, accent, ink = palettes[seed % len(palettes)]
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width * 0.34, height), fill=primary)
    draw.polygon(
        ((width * 0.22, height), (width * 0.57, 0), (width * 0.78, 0), (width * 0.43, height)),
        fill=accent,
    )
    bar_height = max(4, height // 28)
    draw.rectangle((width * 0.68, height * 0.68, width * 0.93, height * 0.68 + bar_height), fill=ink)
    draw.rectangle((width * 0.76, height * 0.78, width * 0.93, height * 0.78 + bar_height), fill=ink)
    output = io.BytesIO()
    image.save(output, format=image_format, quality=84)
    return output.getvalue()


def _fixture_media_response(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    seed = sum(path.encode("utf-8"))
    if path.startswith("/icons/"):
        content = _fixture_image(160, 160, "JPEG", seed)
        return httpx.Response(200, content=content, headers={"Content-Type": "application/octet-stream"})
    if path.startswith("/banners/"):
        content = _fixture_image(960, 344, "WEBP", seed)
        return httpx.Response(200, content=content, headers={"Content-Type": "image/webp"})
    if "broken" in path:
        return httpx.Response(200, content=b"not-an-image", headers={"Content-Type": "image/jpeg"})
    if "portrait" in path:
        content = _fixture_image(900, 1200, "JPEG", seed)
    elif "hires" in path:
        content = _fixture_image(4032, 2760, "JPEG", seed)
    elif "wide" in path:
        content = _fixture_image(1800, 520, "JPEG", seed)
    else:
        content = _fixture_image(1200, 630, "JPEG", seed)
    return httpx.Response(200, content=content, headers={"Content-Type": "image/jpeg"})


fixture_media_client = httpx.AsyncClient(transport=httpx.MockTransport(_fixture_media_response))

LEGACY_FIXTURES = (
    (
        ProjectNamingConfiguration(),
        "Fixture Artist [fanbox-demo-studio]",
        Post(
            id="fiction-1001",
            user="demo-studio",
            service="fanbox",
            title="Fictional project study",
            content="Harmless fixture text for browser verification.",
            published="2026-07-20T00:30:00",
        ),
    ),
    (
        ProjectNamingConfiguration(creator_dirname_format="{creator_name}_{creator_id}"),
        "Archive Artist_archive-studio",
        Post(
            id="archive-2002",
            user="archive-studio",
            service="patreon",
            title="Archived layout sample",
            content="Harmless fixture text for browser verification.",
            published="2026-06-10T09:00:00Z",
        ),
    ),
)
for _naming, _creator_directory, _post in LEGACY_FIXTURES:
    _work_directory = PROJECT_ROOT / "downloads" / _creator_directory / str(_post.title)
    _work_directory.mkdir(parents=True)
    _work_directory.joinpath("post.json").write_text(
        _post.model_dump_json(),
        encoding="utf-8",
    )
    _work_directory.joinpath(f"{_post.id}_cover.jpg").write_bytes(b"fixture-image-data")


class FixtureClient(AbstractAsyncContextManager["FixtureClient"]):
    async def __aenter__(self) -> FixtureClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def list_creators(self) -> list[CreatorSummary]:
        if SHOWCASE_MODE:
            return [
                CreatorSummary(
                    id=creator.creator_id,
                    service=creator.service,
                    name=creator.name,
                    favorited=0,
                    indexed=creator.indexed,
                    updated=creator.updated,
                )
                for creator in SHOWCASE_CREATORS
            ]
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
        if SHOWCASE_MODE:
            creator = SHOWCASE_CREATOR_BY_KEY.get(f"{service}:{creator_id}")
            if creator is not None:
                return CreatorProfile(
                    id=creator.creator_id,
                    service=creator.service,
                    name=creator.name,
                    indexed=creator.indexed,
                    updated=creator.updated,
                )
        names = {
            ("fanbox", "demo-studio"): "Demo Studio",
            ("patreon", "alpha-atelier"): "Alpha Atelier",
            ("pixiv", "studio-10"): "第 10 工作室",
        }
        return CreatorProfile(id=creator_id, service=service, name=names.get((service, creator_id), creator_id))

    async def list_creator_posts(self, service: str, creator_id: str, **_: object) -> list[Post]:
        if SHOWCASE_MODE:
            creator = SHOWCASE_CREATOR_BY_KEY.get(f"{service}:{creator_id}")
            if creator is not None:
                return [
                    Post(
                        id=post.post_id,
                        user=creator.creator_id,
                        service=creator.service,
                        title=post.title,
                        published=post.published,
                        added=post.added,
                    )
                    for post in creator.posts
                ]
        return [
            Post(
                id="fiction-1001",
                user=creator_id,
                service=service,
                title="Fictional project study",
                content=(
                    "Harmless fixture text for browser verification. "
                    '<img src="https://file.pawchive.pw/data/fixtures/wide-content.jpg">'
                ),
                published="2026-07-20T00:30:00",
                file=FileReference(name="cover.jpg", path="/data/fixtures/cover-fiction-1001.jpg"),
                attachments=[
                    FileReference(name="detail.jpg", path="/data/fixtures/hires-detail.jpg"),
                    FileReference(name="portrait.jpg", path="/data/fixtures/portrait-detail.jpg"),
                    FileReference(name="broken.jpg", path="/data/fixtures/broken.jpg"),
                    *[
                        FileReference(name=f"study-{index}.jpg", path=f"/data/fixtures/study-{index}.jpg")
                        for index in range(1, 11)
                    ],
                ],
            )
        ]

    async def get_post(self, service: str, creator_id: str, post_id: str) -> Post:
        posts = await self.list_creator_posts(service, creator_id)
        return next((post for post in posts if post.id == post_id), posts[0].model_copy(update={"id": post_id}))

    async def list_post_revisions(self, service: str, creator_id: str, post_id: str) -> list[Revision]:
        if not SHOWCASE_MODE:
            return [
                Revision(
                    id=post_id,
                    user=creator_id,
                    service=service,
                    revision_id=1,
                    title="Fictional revision",
                )
            ]
        post = await self.get_post(service, creator_id, post_id)
        return [Revision(id=post_id, user=creator_id, service=service, revision_id=1, title=post.title)]

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
            creator = "fanbox:476249" if SHOWCASE_MODE else "fanbox:demo-studio"
            failure = generic_failure(
                code=FailureCode.response_incompatible,
                stage=FailureStage.work_list,
                message="Pawchive returned data in an unsupported format",
                platform="fanbox",
                creator_id="476249" if SHOWCASE_MODE else "demo-studio",
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
            creators = (
                ["fanbox:476249", "fanbox:6570768"]
                if SHOWCASE_MODE
                else ["fanbox:demo-studio", "patreon:alpha-atelier"]
            )
            showcase_files = (
                [
                    *SHOWCASE_CREATORS[0].posts[0].files,
                    *SHOWCASE_CREATORS[0].posts[1].files[1:],
                ]
                if SHOWCASE_MODE
                else []
            )
            reporter.start()
            for creator in creators:
                reporter.creator_started(creator)
            active_downloads: dict[int, tuple[int, int]] = {}
            for index in range(8):
                creator = creators[index % len(creators)]
                file_name = (
                    showcase_files[index].name if SHOWCASE_MODE else f"fictional-active-file-{index + 1:02d}.zip"
                )
                total = (
                    showcase_files[index].size_bytes
                    if SHOWCASE_MODE
                    else (1024 * 1024 if index < 4 else 2 * 1024 * 1024)
                )
                reporter.job_queued(creator)
                reporter.download_started(
                    f"live-{index}",
                    creator,
                    file_name,
                    total,
                    0,
                )
                active_downloads[index] = (total, 0)
            step_count = 320 if SHOWCASE_MODE else 64
            for _ in range(step_count):
                await asyncio.sleep(0.25)
                for index, (total, transferred) in list(active_downloads.items()):
                    chunk = min(32 * 1024, total - transferred)
                    reporter.download_advanced(f"live-{index}", chunk)
                    transferred += chunk
                    if transferred >= total:
                        reporter.download_finished(f"live-{index}", "completed")
                        del active_downloads[index]
                    else:
                        active_downloads[index] = (total, transferred)
                if not active_downloads:
                    break
            for index in active_downloads:
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
        creators = creators or (["fanbox:476249"] if SHOWCASE_MODE else ["fanbox:demo-studio"])
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
    media_proxy=MediaProxyService(fixture_media_client),
)


async def seed_automatic_sync_fixtures() -> None:
    database = app.state.database
    await database.initialize()
    plan_id = "daily-pawchive-check" if SHOWCASE_MODE else "daily-studios"
    plan_name = "每日更新检查" if SHOWCASE_MODE else "Daily studios"
    run_id = "showcase-auto-run" if SHOWCASE_MODE else "fixture-auto-run"
    run_timestamps = (
        ("2026-07-28T19:01:12+00:00",) * 5
        if SHOWCASE_MODE
        else (
            "2026-07-26T19:00:00+00:00",
            "2026-07-26T19:00:00+00:00",
            "2026-07-26T19:00:00+00:00",
            "2026-07-26T19:00:01+00:00",
            "2026-07-26T19:01:12+00:00",
        )
    )
    with sqlite3.connect(database.path) as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO automatic_sync_runs(
                id, plan_id, plan_name, trigger, status, task_id,
                scheduled_for, cutoff_at, created_at, started_at, finished_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                plan_id,
                plan_name,
                "scheduled",
                "completed",
                None,
                *run_timestamps,
            ),
        )
        profile_fixtures = (
            [(creator.service, creator.creator_id, creator.name) for creator in SHOWCASE_CREATORS]
            if SHOWCASE_MODE
            else [("fanbox", "demo-studio", "Demo Studio")]
        )
        for service, creator_id, name in profile_fixtures:
            connection.execute(
                """
                INSERT OR REPLACE INTO creator_profile_cache(service, creator_id, name, fetched_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    service,
                    creator_id,
                    name,
                    "2026-07-29T00:00:00+00:00" if SHOWCASE_MODE else "2026-07-27T00:00:00+00:00",
                ),
            )
        for naming, _, _ in LEGACY_FIXTURES:
            naming_json = json.dumps(
                naming.model_dump(mode="json"),
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            revision = hashlib.sha256(naming_json.encode("utf-8")).hexdigest()
            connection.execute(
                """
                INSERT OR IGNORE INTO naming_layout_versions(
                    id, revision, naming_json, origin, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    f"fixture-layout-{revision[:24]}",
                    revision,
                    naming_json,
                    "recovered",
                    "2026-07-20T00:00:00+00:00",
                ),
            )
        observed_posts = (
            [
                ("fanbox", creator.creator_id, post.post_id)
                for creator in SHOWCASE_CREATORS[:2]
                for post in creator.posts[: (4 if creator.creator_id == "476249" else 3)]
            ]
            if SHOWCASE_MODE
            else [
                ("fanbox", "demo-studio", "fixture-new-1"),
                ("fanbox", "demo-studio", "fixture-new-2"),
                ("fanbox", "demo-studio", "fixture-new-3"),
            ]
        )
        for service, creator_id, post_id in observed_posts:
            connection.execute(
                """
                INSERT OR IGNORE INTO automatic_sync_observed_posts(
                    service, creator_id, post_id, first_seen_at,
                    plan_id, run_id, is_baseline
                ) VALUES (?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    service,
                    creator_id,
                    post_id,
                    "2026-07-28T19:01:00+00:00" if SHOWCASE_MODE else "2026-07-26T19:01:00+00:00",
                    plan_id,
                    run_id,
                ),
            )
        connection.commit()


asyncio.run(seed_automatic_sync_fixtures())
