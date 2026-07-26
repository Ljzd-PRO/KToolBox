from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest

from ktoolbox._enum import DataStorageNameEnum
from ktoolbox.api.generated import Post
from ktoolbox.configuration import Configuration, RuntimeContext
from ktoolbox.job import CreatorIndices
from ktoolbox.naming_migration import MIGRATION_NOTICE_PATH
from ktoolbox.project_config import (
    ProjectConfigStore,
    ProjectConfiguration,
    ProjectNamingConfiguration,
)
from ktoolbox.webui.app import create_app
from ktoolbox.webui.auth import CSRF_HEADER
from ktoolbox.webui.database import WebUIDatabase
from ktoolbox.webui.event_store import WebUIEventStore
from ktoolbox.webui.naming_service import (
    NamingConversionError,
    NamingConversionService,
    NamingPreviewStaleError,
)
from ktoolbox.webui.task_models import SyncTaskSpec
from ktoolbox.webui.task_store import TaskStore


@asynccontextmanager
async def authenticated_client(
    tmp_path: Path,
) -> AsyncIterator[tuple[httpx.AsyncClient, dict[str, str]]]:
    app = create_app(
        RuntimeContext(
            tmp_path,
            Configuration(
                _env_file=None,
                webui={"username": "owner", "password": "secret"},
            ),
        )
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 1234))
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            login = await client.post(
                "/api/v1/session/login",
                json={"username": "owner", "password": "secret"},
            )
            yield client, {CSRF_HEADER: login.json()["csrf_token"]}


async def service_for(tmp_path: Path) -> tuple[NamingConversionService, TaskStore]:
    database = WebUIDatabase(tmp_path / ".ktoolbox" / "webui.sqlite3")
    await database.initialize()
    events = WebUIEventStore(database)
    tasks = TaskStore(database, events)
    service = NamingConversionService(tmp_path, database, events, tasks)
    await service.start()
    return service, tasks


def write_downloaded_work(root: Path, creator_dir: str, work_dir: str, post_id: str) -> Path:
    path = root / creator_dir / work_dir
    path.mkdir(parents=True)
    post = Post(
        id=post_id,
        user="123",
        service="fanbox",
        title=f"Work {post_id}",
    )
    (path / "post.json").write_text(post.model_dump_json(), encoding="utf-8")
    (path / "asset.bin").write_bytes(b"data")
    return path


@pytest.mark.asyncio
async def test_preview_scans_filesystem_and_conversion_updates_project(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    source = write_downloaded_work(downloads, "Artist [fanbox-123]", "Work one", "one")
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(
        ProjectConfiguration(
            naming=ProjectNamingConfiguration(download_roots=[Path("downloads")]),
        )
    )
    service, _ = await service_for(tmp_path)
    candidate = ProjectNamingConfiguration(
        download_roots=[Path("downloads")],
        creator_dirname_format="{creator_name} ({creator_id})",
        post_dirname_format="{post_id}",
    )

    preview = await service.preview(candidate)

    assert preview.creator_count == 1
    assert preview.work_count == 1
    assert preview.file_count == 2
    assert preview.total_bytes > 4
    assert preview.creators[0].source == downloads / "Artist [fanbox-123]"
    assert preview.creators[0].target == downloads / "Artist (123)"
    assert preview.creators[0].operations == 1

    conversion = await service.apply(
        preview.id,
        [preview.creators[0].key],
        convert_existing=True,
    )
    assert conversion.status in {"queued", "running"}
    for _ in range(100):
        conversion = await service.get(preview.id)
        if conversion.status == "completed":
            break
        await asyncio.sleep(0.01)

    assert conversion.status == "completed", conversion.error
    assert not source.exists()
    assert not source.parent.exists()
    assert (downloads / "Artist (123)" / "one" / "asset.bin").is_file()
    assert store.load().naming.post_dirname_format == "{post_id}"

    second_preview = await service.preview(
        candidate.model_copy(
            update={"creator_dirname_format": "{creator_name} - {creator_id}"},
        )
    )
    assert second_preview.creators[0].name == "Artist"
    assert second_preview.creators[0].source == downloads / "Artist (123)"
    assert second_preview.creators[0].target == downloads / "Artist - 123"
    await service.stop()


@pytest.mark.asyncio
async def test_preview_detects_conflicts_staleness_and_active_tasks(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    write_downloaded_work(downloads, "Artist [fanbox-123]", "Work one", "one")
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(
        ProjectConfiguration(
            naming=ProjectNamingConfiguration(download_roots=[Path("downloads")]),
        )
    )
    service, tasks = await service_for(tmp_path)
    candidate = ProjectNamingConfiguration(
        download_roots=[Path("downloads")],
        post_dirname_format="{post_id}",
    )
    conflict = downloads / "Artist [fanbox-123]" / "one"
    conflict.mkdir(parents=True)
    preview = await service.preview(candidate)
    assert preview.conflict_count == 1
    with pytest.raises(NamingConversionError, match="conflict"):
        await service.apply(preview.id, [], convert_existing=True)

    conflict.rmdir()
    preview = await service.preview(candidate)
    (downloads / "changed.txt").write_text("changed", encoding="utf-8")
    with pytest.raises(NamingPreviewStaleError, match="changed"):
        await service.apply(preview.id, [], convert_existing=True)

    (downloads / "changed.txt").unlink()
    preview = await service.preview(candidate)
    await tasks.create(SyncTaskSpec(creators=[], output=downloads))
    with pytest.raises(NamingConversionError, match="overlaps"):
        await service.apply(
            preview.id,
            [preview.creators[0].key],
            convert_existing=True,
        )
    await service.stop()


@pytest.mark.asyncio
async def test_conversion_requires_explicit_selection_and_rolls_back_config_race(
    tmp_path: Path,
) -> None:
    downloads = tmp_path / "downloads"
    source = write_downloaded_work(downloads, "Artist [fanbox-123]", "Work one", "one")
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(
        ProjectConfiguration(
            naming=ProjectNamingConfiguration(download_roots=[Path("downloads")]),
        )
    )
    service, _ = await service_for(tmp_path)
    candidate = ProjectNamingConfiguration(
        download_roots=[Path("downloads")],
        creator_dirname_format="{creator_name} ({creator_id})",
        post_dirname_format="{post_id}",
    )
    preview = await service.preview(candidate)
    with pytest.raises(NamingConversionError, match="select at least one"):
        await service.apply(preview.id, [], convert_existing=True)

    preview = await service.preview(candidate)
    original_mark = service._mark_operation

    async def mutate_configuration(operation_id: int, status: str) -> None:
        await original_mark(operation_id, status)
        project = store.load()
        project.creators = []
        project.naming.download_roots = [Path("changed-downloads")]
        store.save(project)

    service._mark_operation = mutate_configuration  # type: ignore[method-assign]
    await service.apply(
        preview.id,
        [preview.creators[0].key],
        convert_existing=True,
    )
    for _ in range(100):
        conversion = await service.get(preview.id)
        if conversion.status == "failed":
            break
        await asyncio.sleep(0.01)

    assert conversion.status == "failed"
    assert source.is_dir()
    assert not (downloads / "Artist (123)").exists()
    assert store.load().naming.download_roots == [Path("changed-downloads")]
    await service.stop()


@pytest.mark.asyncio
async def test_only_one_naming_conversion_can_be_active(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    write_downloaded_work(downloads, "Artist [fanbox-123]", "Work one", "one")
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(
        ProjectConfiguration(
            naming=ProjectNamingConfiguration(download_roots=[Path("downloads")]),
        )
    )
    service, _ = await service_for(tmp_path)
    candidate = ProjectNamingConfiguration(
        download_roots=[Path("downloads")],
        post_dirname_format="{post_id}",
    )
    first = await service.preview(candidate)
    second = await service.preview(candidate)
    original_run = service._run_conversion
    started = asyncio.Event()
    release = asyncio.Event()

    async def delayed_run(*args: object, **kwargs: object) -> None:
        started.set()
        await release.wait()
        await original_run(*args, **kwargs)  # type: ignore[arg-type]

    service._run_conversion = delayed_run  # type: ignore[method-assign]
    await service.apply(first.id, [first.creators[0].key], convert_existing=True)
    await started.wait()

    with pytest.raises(NamingConversionError, match="already active"):
        await service.apply(second.id, [second.creators[0].key], convert_existing=True)

    release.set()
    for _ in range(100):
        conversion = await service.get(first.id)
        if conversion.status == "completed":
            break
        await asyncio.sleep(0.01)
    assert conversion.status == "completed", conversion.error
    await service.stop()


@pytest.mark.asyncio
async def test_preview_uses_creator_index_and_detects_duplicate_targets(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    first = write_downloaded_work(downloads, "First [fanbox-123]", "Work one", "one")
    second = write_downloaded_work(downloads, "Second [fanbox-456]", "Work two", "two")
    (first / "post.json").unlink()
    first_post = Post(id="one", user="123", service="fanbox", title="Work one")
    index = CreatorIndices(
        creator_id="123",
        service="fanbox",
        posts={"one": first_post},
        posts_path={"one": first},
    )
    (first.parent / DataStorageNameEnum.CreatorIndicesData.value).write_text(
        index.model_dump_json(),
        encoding="utf-8",
    )
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(
        ProjectConfiguration(
            naming=ProjectNamingConfiguration(download_roots=[Path("downloads")]),
        )
    )
    service, _ = await service_for(tmp_path)
    candidate = ProjectNamingConfiguration(
        download_roots=[Path("downloads")],
        creator_dirname_format="all-creators",
        post_dirname_format="same-work",
    )

    preview = await service.preview(candidate)

    assert preview.creator_count == 2
    assert preview.conflict_count >= 2
    assert all(not creator.selectable for creator in preview.creators)
    assert second.exists()
    await service.stop()


@pytest.mark.asyncio
async def test_startup_migration_notice_is_imported_and_acknowledged(tmp_path: Path) -> None:
    notice_path = tmp_path / MIGRATION_NOTICE_PATH
    notice_path.parent.mkdir(parents=True)
    notice_path.write_text(
        json.dumps(
            {
                "id": "project-naming-v2",
                "backup_paths": [".ktoolbox/migrations/project-naming-v2/.env.bak"],
                "ignored_environment_keys": [],
            }
        ),
        encoding="utf-8",
    )

    service, _ = await service_for(tmp_path)

    assert not notice_path.exists()
    notices = await service.notices()
    assert [notice.id for notice in notices] == ["project-naming-v2"]
    acknowledged = await service.acknowledge_notice("project-naming-v2")
    assert acknowledged.acknowledged_at is not None
    assert await service.notices() == []
    await service.stop()


@pytest.mark.asyncio
async def test_naming_routes_require_session_and_csrf(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(
        ProjectConfiguration(
            naming=ProjectNamingConfiguration(download_roots=[Path("downloads")]),
        )
    )
    app = create_app(
        RuntimeContext(
            tmp_path,
            Configuration(
                _env_file=None,
                webui={"username": "owner", "password": "secret"},
            ),
        )
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 1234))
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as anonymous:
            assert (await anonymous.get("/api/v1/naming")).status_code == 401

    async with authenticated_client(tmp_path) as (client, csrf):
        current = await client.get("/api/v1/naming")
        assert current.status_code == 200
        assert current.json()["naming"]["download_roots"] == ["downloads"]
        payload = {
            "naming": {
                **current.json()["naming"],
                "post_dirname_format": "{post_id}",
            }
        }
        assert (await client.post("/api/v1/naming/preview", json=payload)).status_code == 403
        preview = await client.post(
            "/api/v1/naming/preview",
            json=payload,
            headers=csrf,
        )
        assert preview.status_code == 200
        apply = await client.post(
            "/api/v1/naming/apply",
            json={
                "preview_id": preview.json()["id"],
                "selected_creators": [],
                "convert_existing": False,
            },
            headers=csrf,
        )
        assert apply.status_code == 202
        assert store.load().naming.post_dirname_format == "{post_id}"
