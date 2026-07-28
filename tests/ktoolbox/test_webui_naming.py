from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest

from ktoolbox._enum import DataStorageNameEnum
from ktoolbox.api.generated import Post
from ktoolbox.configuration import Configuration, RuntimeContext
from ktoolbox.job import CreatorIndices
from ktoolbox.project_config import (
    ProjectConfigStore,
    ProjectConfiguration,
    ProjectNamingConfiguration,
)
from ktoolbox.webui.app import create_app
from ktoolbox.webui.auth import CSRF_HEADER
from ktoolbox.webui.config_store import content_revision
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


async def save_naming(
    service: NamingConversionService,
    store: ProjectConfigStore,
    candidate: ProjectNamingConfiguration,
    section: str = "templates",
) -> None:
    await service.update_naming(
        section,  # type: ignore[arg-type]
        candidate,
        content_revision(store.load_text()),
    )


@pytest.mark.asyncio
async def test_legacy_download_roots_move_out_of_project_naming(tmp_path: Path) -> None:
    project_path = tmp_path / "ktoolbox.toml"
    project_path.write_text(
        """
schema_version = 3

[naming]
download_roots = ["downloads", "/archive/ktoolbox"]
creator_dirname_format = "{creator_name} [{service}-{creator_id}]"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    service, _ = await service_for(tmp_path)

    context = await service.legacy_context()
    assert set(context.roots) == {Path("downloads"), Path("/archive/ktoolbox")}
    assert "download_roots" not in project_path.read_text(encoding="utf-8")
    assert ProjectConfigStore(project_path).load().schema_version == 5
    await service.stop()

    restarted, _ = await service_for(tmp_path)
    assert set((await restarted.legacy_context()).roots) == set(context.roots)
    await restarted.stop()


@pytest.mark.asyncio
async def test_naming_sections_save_without_overwriting_each_other(tmp_path: Path) -> None:
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)
    original = store.load().naming
    candidate = original.model_copy(
        update={
            "mix_posts": True,
            "creator_dirname_format": "{creator_name} ({creator_id})",
        }
    )

    structure_result = await service.update_naming(
        "structure",
        candidate,
        content_revision(store.load_text()),
    )
    assert structure_result.naming.mix_posts is True
    assert structure_result.naming.creator_dirname_format == original.creator_dirname_format
    assert structure_result.conversion_pending is True
    first_notice = (await service.notices())[0]
    assert first_notice.kind == "legacy_layout_conversion"
    assert first_notice.payload["target"]["mix_posts"] is True

    templates_result = await service.update_naming(
        "templates",
        candidate,
        structure_result.revision,
    )
    assert templates_result.naming.mix_posts is True
    assert templates_result.naming.creator_dirname_format == "{creator_name} ({creator_id})"
    second_notice = (await service.notices())[0]
    assert second_notice.id != first_notice.id
    assert second_notice.payload["target"]["creator_dirname_format"] == "{creator_name} ({creator_id})"
    await service.resolve_notice(second_notice.id, "ignored")
    assert await service.notices() == []

    another = candidate.model_copy(update={"creator_dirname_format": "{creator_name}"})
    await service.update_naming("templates", another, templates_result.revision)
    assert len(await service.notices()) == 1
    with pytest.raises(NamingPreviewStaleError, match="reload before saving"):
        await service.update_naming("templates", original, structure_result.revision)
    await service.stop()


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
    store.save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)
    candidate = ProjectNamingConfiguration(
        creator_dirname_format="{creator_name} ({creator_id})",
        post_dirname_format="{post_id}",
    )
    await save_naming(service, store, candidate)

    preview = await service.preview([Path("downloads")])

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
    )
    assert conversion.status in {"queued", "running"}
    for _ in range(100):
        conversion = await service.get(preview.id)
        if conversion.status == "completed":
            break
        await asyncio.sleep(0.01)

    assert conversion.status == "completed", conversion.error
    assert await service.notices() == []
    assert not source.exists()
    assert not source.parent.exists()
    assert (downloads / "Artist (123)" / "one" / "asset.bin").is_file()
    assert store.load().naming.post_dirname_format == "{post_id}"

    second_candidate = candidate.model_copy(
        update={"creator_dirname_format": "{creator_name} - {creator_id}"},
    )
    await save_naming(service, store, second_candidate)
    second_preview = await service.preview([Path("downloads")])
    assert second_preview.creators[0].name == "Artist"
    assert second_preview.creators[0].source == downloads / "Artist (123)"
    assert second_preview.creators[0].target == downloads / "Artist - 123"
    await service.stop()


@pytest.mark.asyncio
async def test_preview_detects_conflicts_staleness_and_active_tasks(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    write_downloaded_work(downloads, "Artist [fanbox-123]", "Work one", "one")
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
    service, tasks = await service_for(tmp_path)
    candidate = ProjectNamingConfiguration(
        post_dirname_format="{post_id}",
    )
    await save_naming(service, store, candidate)
    conflict = downloads / "Artist [fanbox-123]" / "one"
    conflict.mkdir(parents=True)
    preview = await service.preview([Path("downloads")])
    assert preview.conflict_count == 1
    with pytest.raises(NamingConversionError, match="conflict"):
        await service.apply(preview.id, [])

    conflict.rmdir()
    preview = await service.preview([Path("downloads")])
    (downloads / "changed.txt").write_text("changed", encoding="utf-8")
    with pytest.raises(NamingPreviewStaleError, match="changed"):
        await service.apply(preview.id, [])

    (downloads / "changed.txt").unlink()
    preview = await service.preview([Path("downloads")])
    await tasks.create(SyncTaskSpec(creators=[], output=downloads))
    with pytest.raises(NamingConversionError, match="overlaps"):
        await service.apply(
            preview.id,
            [preview.creators[0].key],
        )
    await service.stop()


@pytest.mark.asyncio
async def test_conversion_requires_explicit_selection_and_rolls_back_config_race(
    tmp_path: Path,
) -> None:
    downloads = tmp_path / "downloads"
    source = write_downloaded_work(downloads, "Artist [fanbox-123]", "Work one", "one")
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)
    candidate = ProjectNamingConfiguration(
        creator_dirname_format="{creator_name} ({creator_id})",
        post_dirname_format="{post_id}",
    )
    await save_naming(service, store, candidate)
    preview = await service.preview([Path("downloads")])
    with pytest.raises(NamingConversionError, match="select at least one"):
        await service.apply(preview.id, [])

    preview = await service.preview([Path("downloads")])
    original_mark = service._mark_operation

    async def mutate_configuration(operation_id: int, status: str) -> None:
        await original_mark(operation_id, status)
        project = store.load()
        project.creators = [project.creators[0]] if project.creators else []
        project.naming.post_dirname_format = "{title}"
        store.save(project)

    service._mark_operation = mutate_configuration  # type: ignore[method-assign]
    await service.apply(
        preview.id,
        [preview.creators[0].key],
    )
    for _ in range(100):
        conversion = await service.get(preview.id)
        if conversion.status == "failed":
            break
        await asyncio.sleep(0.01)

    assert conversion.status == "failed"
    assert source.is_dir()
    assert not (downloads / "Artist (123)").exists()
    assert store.load().naming.post_dirname_format == "{title}"
    await service.stop()


@pytest.mark.asyncio
async def test_only_one_naming_conversion_can_be_active(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    write_downloaded_work(downloads, "Artist [fanbox-123]", "Work one", "one")
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)
    candidate = ProjectNamingConfiguration(
        post_dirname_format="{post_id}",
    )
    await save_naming(service, store, candidate)
    first = await service.preview([Path("downloads")])
    second = await service.preview([Path("downloads")])
    original_run = service._run_conversion
    started = asyncio.Event()
    release = asyncio.Event()

    async def delayed_run(*args: object, **kwargs: object) -> None:
        started.set()
        await release.wait()
        await original_run(*args, **kwargs)  # type: ignore[arg-type]

    service._run_conversion = delayed_run  # type: ignore[method-assign]
    await service.apply(first.id, [first.creators[0].key])
    await started.wait()

    with pytest.raises(NamingConversionError, match="already active"):
        await service.apply(second.id, [second.creators[0].key])

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
    store.save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)
    candidate = ProjectNamingConfiguration(
        creator_dirname_format="all-creators",
        post_dirname_format="same-work",
    )
    await save_naming(service, store, candidate)

    preview = await service.preview([Path("downloads")])

    assert preview.creator_count == 2
    assert preview.conflict_count >= 2
    assert all(not creator.selectable for creator in preview.creators)
    assert second.exists()
    await service.stop()


@pytest.mark.asyncio
async def test_legacy_migration_requires_explicit_field_confirmation(tmp_path: Path) -> None:
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    project = ProjectConfiguration()
    project.naming.post_dirname_format = "{id}"
    project.naming.filename_format = "{post_id}_{}"
    store.save(project)
    (tmp_path / ".env").write_text(
        "KTOOLBOX_JOB__POST_DIRNAME_FORMAT={title} [{id}]\n"
        "KTOOLBOX_JOB__FILENAME_FORMAT={id}_{}\n",
        encoding="utf-8",
    )
    service, _ = await service_for(tmp_path)

    preview = await service.legacy_migration()
    assert preview.pending is True
    assert {field.path for field in preview.fields} == {
        "post_dirname_format",
        "filename_format",
    }
    result = await service.apply_legacy_migration(
        selected_fields=["post_dirname_format"],
        project_revision=preview.project_revision,
        source_revisions={source.name: source.revision for source in preview.sources},
    )

    assert result.migrated is True
    migrated = store.load()
    assert migrated.naming.post_dirname_format == "{title} [{id}]"
    assert migrated.naming.filename_format == "{post_id}_{}"
    assert (await service.legacy_migration()).pending is False
    assert await service.has_pending_layout() is True
    await service.stop()


@pytest.mark.asyncio
async def test_naming_routes_require_session_and_csrf(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
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
        update_payload = {
            "section": "templates",
            "revision": current.json()["revision"],
            "naming": {
                **current.json()["naming"],
                "post_dirname_format": "{post_id}",
            },
        }
        assert (await client.patch("/api/v1/naming", json=update_payload)).status_code == 403
        updated = await client.patch(
            "/api/v1/naming",
            json=update_payload,
            headers=csrf,
        )
        assert updated.status_code == 200
        preview_payload = {"roots": ["downloads"]}
        assert (await client.post("/api/v1/naming/preview", json=preview_payload)).status_code == 403
        preview = await client.post(
            "/api/v1/naming/preview",
            json=preview_payload,
            headers=csrf,
        )
        assert preview.status_code == 200
        apply = await client.post(
            "/api/v1/naming/apply",
            json={
                "preview_id": preview.json()["id"],
                "selected_creators": [],
            },
            headers=csrf,
        )
        assert apply.status_code == 202
        assert store.load().naming.post_dirname_format == "{post_id}"


@pytest.mark.asyncio
async def test_legacy_migration_routes_apply_selected_fields(tmp_path: Path) -> None:
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
    (tmp_path / ".env").write_text(
        "KTOOLBOX_JOB__POST_DIRNAME_FORMAT={id}\n"
        "KTOOLBOX_JOB__MIX_POSTS=true\n",
        encoding="utf-8",
    )

    async with authenticated_client(tmp_path) as (client, csrf):
        preview = await client.get("/api/v1/naming/legacy-migration")
        assert preview.status_code == 200
        body = preview.json()
        assert body["pending"] is True
        assert {field["path"] for field in body["fields"]} == {
            "post_dirname_format",
            "mix_posts",
        }
        payload = {
            "selected_fields": ["post_dirname_format"],
            "project_revision": body["project_revision"],
            "source_revisions": {
                source["name"]: source["revision"]
                for source in body["sources"]
            },
        }
        assert (
            await client.post(
                "/api/v1/naming/legacy-migration/apply",
                json=payload,
            )
        ).status_code == 403
        applied = await client.post(
            "/api/v1/naming/legacy-migration/apply",
            json=payload,
            headers=csrf,
        )
        assert applied.status_code == 200
        assert applied.json()["naming"]["post_dirname_format"] == "{id}"
        assert applied.json()["naming"]["mix_posts"] is False
        assert (await client.get("/api/v1/naming/legacy-migration")).json()["pending"] is False
