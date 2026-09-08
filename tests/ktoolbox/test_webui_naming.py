from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import httpx
import pytest

from ktoolbox._enum import DataStorageNameEnum
from ktoolbox.api.generated import FileReference, Post
from ktoolbox.configuration import Configuration, RuntimeContext
from ktoolbox.job import CreatorIndices
from ktoolbox.project_config import (
    ProjectConfigStore,
    ProjectConfiguration,
    ProjectNamingConfiguration,
)
from ktoolbox.publication_time import PublishedTimePolicy
from ktoolbox.webui.app import create_app
from ktoolbox.webui.auth import CSRF_HEADER
from ktoolbox.webui.config_store import content_revision
from ktoolbox.webui.database import WebUIDatabase
from ktoolbox.webui.event_store import WebUIEventStore
from ktoolbox.webui.naming_models import (
    NamingPreviewResponse,
    PastedConfigConversionSource,
    ProjectLayoutConversionSource,
)
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


async def preview_from_history(
    service: NamingConversionService,
    roots: list[Path],
) -> NamingPreviewResponse:
    versions = await service.layout_versions()
    source_versions = [version.id for version in versions if not version.is_current]
    if not source_versions:
        source_versions = [versions[0].id]
    return await service.preview(
        roots,
        ProjectLayoutConversionSource(version_ids=source_versions),
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
        default_output=Path("../shared-downloads"),
    )
    assert structure_result.naming.mix_posts is True
    assert structure_result.naming.creator_dirname_format == original.creator_dirname_format
    assert structure_result.default_output == Path("../shared-downloads")
    assert structure_result.resolved_default_output == tmp_path.parent / "shared-downloads"
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
    assert templates_result.default_output == Path("../shared-downloads")
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


@pytest.mark.asyncio
async def test_naming_layout_versions_are_persistent_and_deduplicated(tmp_path: Path) -> None:
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)

    initial_versions = await service.layout_versions()
    assert len(initial_versions) == 1
    assert initial_versions[0].is_current is True
    initial_id = initial_versions[0].id

    candidate = store.load().naming.model_copy(update={"post_dirname_format": "{post_id}"})
    await save_naming(service, store, candidate)
    versions = await service.layout_versions()
    assert len(versions) == 2
    assert {version.id for version in versions} >= {initial_id}
    assert sum(version.is_current for version in versions) == 1

    await save_naming(service, store, candidate)
    assert len(await service.layout_versions()) == 2
    await service.stop()

    restarted, _ = await service_for(tmp_path)
    restarted_versions = await restarted.layout_versions()
    assert {version.id for version in restarted_versions} == {version.id for version in versions}
    await restarted.stop()


@pytest.mark.asyncio
async def test_database_migration_marks_existing_layout_versions_as_legacy_raw(
    tmp_path: Path,
) -> None:
    database = WebUIDatabase(tmp_path / ".ktoolbox" / "webui.sqlite3")
    await database.initialize()
    naming = ProjectNamingConfiguration()
    async with database.connect() as connection:
        await connection.execute("DELETE FROM schema_migrations WHERE version = 14")
        await connection.execute(
            """
            INSERT INTO naming_layout_versions(
                id, revision, naming_json, published_time_json, origin, created_at
            ) VALUES (?, ?, ?, NULL, ?, ?)
            """,
            (
                "legacy-layout",
                "legacy-revision",
                naming.model_dump_json(),
                "project_change",
                "2026-01-01T00:00:00+00:00",
            ),
        )
        await connection.commit()

    await database.initialize()

    async with database.connect() as connection:
        row = await (
            await connection.execute(
                "SELECT published_time_json, origin FROM naming_layout_versions WHERE id = ?",
                ("legacy-layout",),
            )
        ).fetchone()
    assert row is not None
    assert json.loads(str(row[0])) == {"mode": "legacy_raw"}
    assert row[1] == "legacy_raw"


@pytest.mark.asyncio
async def test_pawchive_raw_layout_converts_fanbox_publication_date_to_target_timezone(
    tmp_path: Path,
) -> None:
    downloads = tmp_path / "downloads"
    source_work = downloads / "Artist [fanbox-123]" / "2025-12-21"
    source_work.mkdir(parents=True)
    post = Post(
        id="one",
        user="123",
        service="fanbox",
        title="Work one",
        published=datetime.fromisoformat("2025-12-21T00:35:43"),
    )
    (source_work / "post.json").write_text(post.model_dump_json(), encoding="utf-8")
    (source_work / "asset.bin").write_bytes(b"data")
    naming = ProjectNamingConfiguration(post_dirname_format="{published}")
    ProjectConfigStore(tmp_path / "ktoolbox.toml").save(ProjectConfiguration(naming=naming))
    service, _ = await service_for(tmp_path)
    try:
        parsed = await service.parse_source(
            "toml",
            '[naming]\npost_dirname_format = "{published}"\n',
        )
        preview = await service.preview(
            [Path("downloads")],
            PastedConfigConversionSource(
                format="toml",
                naming=parsed.naming,
                digest=parsed.digest,
                published_time_mode="pawchive_raw",
            ),
        )

        assert preview.creator_count == 1
        assert preview.creators[0].source == source_work.parent
        assert preview.creators[0].operations == 1
        conversion = await service.apply(preview.id, [preview.creators[0].key])
        await wait_for_conversion(service, conversion.id, "completed")

        target_work = downloads / "Artist [fanbox-123]" / "2025-12-20"
        assert not source_work.exists()
        assert (target_work / "post.json").is_file()
        assert (target_work / "asset.bin").read_bytes() == b"data"
        stored_post = Post.model_validate_json((target_work / "post.json").read_text(encoding="utf-8"))
        assert stored_post.published == post.published
    finally:
        await service.stop()


@pytest.mark.asyncio
async def test_layout_version_history_survives_completed_conversion(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)
    candidate = store.load().naming.model_copy(update={"post_dirname_format": "{post_id}"})
    await save_naming(service, store, candidate)

    preview = await preview_from_history(service, [Path("downloads")])
    conversion = await service.apply(preview.id, [])

    assert conversion.status == "completed"
    assert await service.has_pending_layout() is False
    assert len(await service.layout_versions()) == 2
    await service.stop()


@pytest.mark.asyncio
async def test_pasted_source_preview_uses_current_target_without_resolving_pending(
    tmp_path: Path,
) -> None:
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)
    current = store.load().naming.model_copy(update={"post_dirname_format": "{post_id}"})
    await save_naming(service, store, current)
    parsed = await service.parse_source(
        "env",
        "KTOOLBOX_JOB__POST_DIRNAME_FORMAT={title}\n",
    )
    source = PastedConfigConversionSource(
        format="env",
        naming=parsed.naming,
        digest=parsed.digest,
    )

    preview = await service.preview([Path("downloads")], source)
    conversion = await service.apply(preview.id, [])

    assert preview.source == source
    assert preview.resolves_pending_layout is False
    assert conversion.status == "completed"
    assert await service.has_pending_layout() is True
    async with service.database.connect() as connection:
        stored = await (
            await connection.execute(
                """
                SELECT source_kind, source_json, target_revision
                FROM naming_conversions WHERE id = ?
                """,
                (preview.id,),
            )
        ).fetchone()
    assert stored is not None
    assert stored[0] == "pasted_config"
    assert "KTOOLBOX_JOB" not in str(stored[1])
    assert stored[2]
    await service.stop()


@pytest.mark.asyncio
async def test_preview_rejects_unknown_or_changed_explicit_sources(
    tmp_path: Path,
) -> None:
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)

    with pytest.raises(NamingConversionError, match="unknown project naming versions"):
        await service.preview(
            [Path("downloads")],
            ProjectLayoutConversionSource(version_ids=["missing"]),
        )
    parsed = await service.parse_source(
        "env",
        "KTOOLBOX_JOB__MIX_POSTS=true\n",
    )
    with pytest.raises(NamingConversionError, match="changed after parsing"):
        await service.preview(
            [Path("downloads")],
            PastedConfigConversionSource(
                format="env",
                naming=parsed.naming,
                digest="0" * 64,
            ),
        )
    await service.stop()


def write_downloaded_work(
    root: Path,
    creator_dir: str,
    work_dir: str,
    post_id: str,
    creator_id: str = "123",
) -> Path:
    path = root / creator_dir / work_dir
    path.mkdir(parents=True)
    post = Post(
        id=post_id,
        user=creator_id,
        service="fanbox",
        title=f"Work {post_id}",
    )
    (path / "post.json").write_text(post.model_dump_json(), encoding="utf-8")
    (path / "asset.bin").write_bytes(b"data")
    return path


async def wait_for_conversion(
    service: NamingConversionService,
    conversion_id: str,
    status: str,
) -> None:
    for _ in range(200):
        conversion = await service.get(conversion_id)
        if conversion.status == status:
            return
        await asyncio.sleep(0.01)
    pytest.fail(f"conversion {conversion_id} remained {conversion.status!r}; expected {status!r}")


@pytest.mark.asyncio
async def test_preview_converts_creators_from_multiple_project_layout_versions(
    tmp_path: Path,
) -> None:
    downloads = tmp_path / "downloads"
    first_source = write_downloaded_work(
        downloads,
        "First [fanbox-123]",
        "Work one",
        "one",
    )
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)

    intermediate = ProjectNamingConfiguration(
        creator_dirname_format="{creator_name} ({creator_id})",
        post_dirname_format="{post_id}",
    )
    await save_naming(service, store, intermediate)
    second_source = write_downloaded_work(
        downloads,
        "Second (456)",
        "two",
        "two",
        creator_id="456",
    )
    target = intermediate.model_copy(update={"creator_dirname_format": "{creator_name} - {creator_id}"})
    await save_naming(service, store, target)

    versions = await service.layout_versions()
    source_ids = [version.id for version in versions if not version.is_current]
    preview = await service.preview(
        [Path("downloads")],
        ProjectLayoutConversionSource(version_ids=source_ids),
    )

    assert {creator.key.split("@", 1)[0] for creator in preview.creators} == {
        "fanbox:123",
        "fanbox:456",
    }
    assert all(creator.selectable for creator in preview.creators)
    conversion = await service.apply(
        preview.id,
        [creator.key for creator in preview.creators],
    )
    await wait_for_conversion(service, conversion.id, "completed")

    assert not first_source.parent.exists()
    assert not second_source.parent.exists()
    assert (downloads / "First - 123" / "one" / "asset.bin").is_file()
    assert (downloads / "Second - 456" / "two" / "asset.bin").is_file()
    await service.stop()


@pytest.mark.asyncio
async def test_pending_layout_sources_keep_individual_publication_policies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "downloads").mkdir()
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)
    original_policy = PublishedTimePolicy.from_values(
        target_timezone="UTC",
        fallback_service_timezone="UTC",
        service_timezones={"fanbox": "Asia/Tokyo", "patreon": "UTC"},
    )
    changed_policy = PublishedTimePolicy.from_values(
        target_timezone="Asia/Shanghai",
        fallback_service_timezone="UTC",
        service_timezones={"fanbox": "Asia/Tokyo", "patreon": "UTC"},
    )
    changed_naming = ProjectNamingConfiguration(post_dirname_format="{published} [{post_id}]")
    final_naming = changed_naming.model_copy(update={"creator_dirname_format": "{creator_name} ({creator_id})"})

    await save_naming(service, store, changed_naming)
    await service.record_published_time_change(original_policy, changed_policy)
    monkeypatch.setattr(service, "_current_published_time", lambda: changed_policy)
    await save_naming(service, store, final_naming)

    async with service.database.connect() as connection:
        row = await (await connection.execute("SELECT sources_json FROM naming_layout_state WHERE id = 1")).fetchone()
    assert row is not None
    sources = json.loads(str(row[0]))
    assert len(sources) == 3
    assert all(set(source) == {"naming", "published_time"} for source in sources)
    assert {source["published_time"]["target_timezone"] for source in sources} == {
        "UTC",
        "Asia/Shanghai",
    }
    assert {source["naming"]["post_dirname_format"] for source in sources} == {
        ProjectNamingConfiguration().post_dirname_format,
        changed_naming.post_dirname_format,
    }
    changed_naming_sources = [
        source for source in sources if source["naming"] == changed_naming.model_dump(mode="json")
    ]
    assert {source["published_time"]["target_timezone"] for source in changed_naming_sources} == {
        "UTC",
        "Asia/Shanghai",
    }

    versions = await service.layout_versions()
    source_ids = [version.id for version in versions if not version.is_current]
    preview = await service.preview(
        [Path("downloads")],
        ProjectLayoutConversionSource(version_ids=source_ids),
    )
    assert preview.resolves_pending_layout is True
    await service.stop()


@pytest.mark.asyncio
async def test_pasted_env_source_converts_files_without_persisting_raw_text(
    tmp_path: Path,
) -> None:
    downloads = tmp_path / "downloads"
    source = write_downloaded_work(
        downloads,
        "Artist [fanbox-123]",
        "Work one",
        "one",
    )
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)
    target = ProjectNamingConfiguration(
        creator_dirname_format="{creator_name} ({creator_id})",
        post_dirname_format="{post_id}",
    )
    await save_naming(service, store, target)
    raw_source = (
        'KTOOLBOX_JOB__CREATOR_DIRNAME_FORMAT="{creator_name} '
        '[{service}-{creator_id}]"\n'
        'KTOOLBOX_JOB__POST_DIRNAME_FORMAT="{title}"\n'
    )
    parsed = await service.parse_source("env", raw_source)
    preview = await service.preview(
        [Path("downloads")],
        PastedConfigConversionSource(
            format="env",
            naming=parsed.naming,
            digest=parsed.digest,
        ),
    )
    conversion = await service.apply(preview.id, [preview.creators[0].key])
    await wait_for_conversion(service, conversion.id, "completed")

    assert not source.parent.exists()
    assert (downloads / "Artist (123)" / "one" / "asset.bin").is_file()
    assert raw_source.encode() not in service.database.path.read_bytes()
    stored = await service.get(conversion.id)
    assert stored.preview.source.kind == "pasted_config"
    assert "KTOOLBOX_JOB" not in stored.preview.source.model_dump_json()
    await service.stop()


def write_flat_attachment_work(root: Path, attachment_dir: str = ".", *, sequential: bool = False) -> Path:
    work = root / "Artist [fanbox-123]" / "Work one"
    files = work / attachment_dir
    files.mkdir(parents=True)
    post = Post(
        id="one",
        user="123",
        service="fanbox",
        title="Work one",
        file=FileReference(name="cover.png", path="/cover.png"),
        attachments=[
            FileReference(name="drawing.jpg", path="/drawing.jpg"),
            FileReference(name="bundle.zip", path="/bundle.zip"),
            FileReference(name="second.png", path="/second.png"),
        ],
    )
    (work / "post.json").write_text(post.model_dump_json(), encoding="utf-8")
    (work / "one_cover.png").write_bytes(b"cover")
    (work / "content.txt").write_bytes(b"body")
    (work / "external_links.txt").write_bytes(b"links")
    (work / "notes.keep").write_bytes(b"unrecognized file")
    (files / ("1.jpg" if sequential else "drawing.jpg")).write_bytes(b"first attachment")
    (files / "bundle.zip").write_bytes(b"archive attachment")
    (files / ("2.png" if sequential else "second.png")).write_bytes(b"second attachment")
    return work


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("old_dir", "new_dir", "sequential"),
    [(".", "attachments", False), (".", ".", False), ("attachments", ".", False), (".", "files", True)],
)
async def test_conversion_moves_root_attachments_without_scooping_up_work_files(
    tmp_path: Path, old_dir: str, new_dir: str, sequential: bool
) -> None:
    downloads = tmp_path / "downloads"
    source_work = write_flat_attachment_work(downloads, old_dir, sequential=sequential)
    metadata = (source_work / "post.json").read_bytes()
    target = ProjectNamingConfiguration.model_validate(
        {"post_dirname_format": "{post_id}", "post_structure": {"attachments": new_dir}}
    )
    ProjectConfigStore(tmp_path / "ktoolbox.toml").save(ProjectConfiguration(naming=target))
    service, _ = await service_for(tmp_path)
    try:
        parsed = await service.parse_source(
            "env",
            f"KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS={old_dir}/\n"
            f"KTOOLBOX_JOB__SEQUENTIAL_FILENAME={str(sequential).lower()}\n"
            'KTOOLBOX_JOB__SEQUENTIAL_FILENAME_EXCLUDES=[".zip"]\n',
        )
        preview = await service.preview(
            [downloads], PastedConfigConversionSource(format="env", naming=parsed.naming, digest=parsed.digest)
        )
        assert preview.creator_count == 1
        assert preview.work_count == 1
        assert preview.file_count == 8
        assert preview.conflict_count == 0
        conversion = await service.apply(preview.id, [preview.creators[0].key])
        await wait_for_conversion(service, conversion.id, "completed")

        work = source_work.parent / "one"
        files = work / new_dir
        assert (files / "1.jpg").read_bytes() == b"first attachment"
        assert (files / "2.zip").read_bytes() == b"archive attachment"
        assert (files / "3.png").read_bytes() == b"second attachment"
        assert (work / "post.json").read_bytes() == metadata
        assert (work / "one_cover.png").read_bytes() == b"cover"
        assert (work / "content.txt").read_bytes() == b"body"
        assert (work / "external_links.txt").read_bytes() == b"links"
        assert (work / "notes.keep").read_bytes() == b"unrecognized file"
        assert not source_work.exists()
        assert len([path for path in work.rglob("*") if path.is_file()]) == 8
    finally:
        await service.stop()


@pytest.mark.asyncio
async def test_root_attachment_conversion_rejects_existing_target_file(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    source = write_flat_attachment_work(downloads)
    (source / "attachments").mkdir()
    (source / "attachments/1.jpg").write_bytes(b"must not overwrite")
    ProjectConfigStore(tmp_path / "ktoolbox.toml").save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)
    try:
        parsed = await service.parse_source("env", "KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./\n")
        preview = await service.preview(
            [downloads], PastedConfigConversionSource(format="env", naming=parsed.naming, digest=parsed.digest)
        )
        assert preview.conflict_count > 0
        assert not preview.creators[0].selectable
        with pytest.raises(NamingConversionError):
            await service.apply(preview.id, [preview.creators[0].key])
        assert (source / "attachments/1.jpg").read_bytes() == b"must not overwrite"
        assert (source / "drawing.jpg").read_bytes() == b"first attachment"
    finally:
        await service.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("obstacle", ["symlink", "parent_file", "metadata"])
async def test_root_attachment_conversion_protects_boundaries_and_metadata(tmp_path: Path, obstacle: str) -> None:
    downloads = tmp_path / "downloads"
    source = write_flat_attachment_work(downloads)
    if obstacle == "symlink":
        outside = tmp_path / "outside"
        outside.mkdir()
        try:
            (source / "attachments").symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("directory symlinks are unavailable")
    elif obstacle == "parent_file":
        (source / "attachments").write_bytes(b"not a directory")
    else:
        metadata = source / "post.json"
        post = Post.model_validate_json(metadata.read_text(encoding="utf-8"))
        post.attachments = [FileReference(name="post.json", path="/post.json")]
        metadata.write_text(post.model_dump_json(), encoding="utf-8")
    original_metadata = (source / "post.json").read_bytes()
    ProjectConfigStore(tmp_path / "ktoolbox.toml").save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)
    try:
        parsed = await service.parse_source("env", "KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./\n")
        preview = await service.preview(
            [downloads], PastedConfigConversionSource(format="env", naming=parsed.naming, digest=parsed.digest)
        )
        assert preview.conflict_count > 0
        with pytest.raises(NamingConversionError):
            await service.apply(preview.id, [preview.creators[0].key])
        assert (source / "post.json").read_bytes() == original_metadata
        if obstacle == "symlink":
            assert list((tmp_path / "outside").iterdir()) == []
    finally:
        await service.stop()


@pytest.mark.asyncio
async def test_webui_routes_parse_preview_and_convert_legacy_root_attachments(tmp_path: Path) -> None:
    source = write_flat_attachment_work(tmp_path / "downloads")
    async with authenticated_client(tmp_path) as (client, headers):
        parsed = await client.post(
            "/api/v1/naming/source/parse",
            headers=headers,
            json={"format": "env", "content": "KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./\n"},
        )
        assert parsed.status_code == 200, parsed.text
        data = parsed.json()
        assert data["naming"]["post_structure"]["attachments"] == "."
        preview = await client.post(
            "/api/v1/naming/preview",
            headers=headers,
            json={
                "roots": ["downloads"],
                "source": {
                    "kind": "pasted_config",
                    "format": "env",
                    "naming": data["naming"],
                    "digest": data["digest"],
                },
            },
        )
        assert preview.status_code == 200, preview.text
        data = preview.json()
        assert data["conflict_count"] == 0
        applied = await client.post(
            "/api/v1/naming/apply",
            headers=headers,
            json={"preview_id": data["id"], "selected_creators": [data["creators"][0]["key"]]},
        )
        assert applied.status_code == 202, applied.text
        for _ in range(200):
            result = await client.get(f"/api/v1/naming/conversions/{data['id']}")
            assert result.status_code == 200
            if result.json()["status"] == "completed":
                break
            await asyncio.sleep(0.01)
        assert result.json()["status"] == "completed", result.text
        assert (source.parent / "Work one [one]/attachments/1.jpg").read_bytes() == b"first attachment"


@pytest.mark.asyncio
async def test_root_attachment_conversion_uses_creator_index_without_post_json(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    source = write_flat_attachment_work(downloads)
    metadata = source / "post.json"
    post = Post.model_validate_json(metadata.read_text(encoding="utf-8"))
    index = CreatorIndices(creator_id="123", service="fanbox", posts={post.id: post})
    (source.parent / DataStorageNameEnum.CreatorIndicesData.value).write_text(index.model_dump_json(), encoding="utf-8")
    metadata.unlink()
    ProjectConfigStore(tmp_path / "ktoolbox.toml").save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)
    try:
        parsed = await service.parse_source("env", "KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./\n")
        preview = await service.preview(
            [downloads], PastedConfigConversionSource(format="env", naming=parsed.naming, digest=parsed.digest)
        )
        assert preview.work_count == 1
        conversion = await service.apply(preview.id, [preview.creators[0].key])
        await wait_for_conversion(service, conversion.id, "completed")
        target = source.parent / "Work one [one]"
        assert (target / "attachments/1.jpg").read_bytes() == b"first attachment"
        assert (target / "notes.keep").is_file()
        assert not (target / "post.json").exists()
    finally:
        await service.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("pause_after", [None, 1, 6, 9])
async def test_root_attachment_conversion_includes_revision_files(tmp_path: Path, pause_after: int | None) -> None:
    downloads = tmp_path / "downloads"
    source = write_flat_attachment_work(downloads)
    revision = source / "revisions/7"
    revision.mkdir(parents=True)
    for path in source.iterdir():
        if path.is_file():
            (revision / path.name).write_bytes(path.read_bytes())
    metadata = Post.model_validate_json((revision / "post.json").read_text(encoding="utf-8"))
    metadata = metadata.model_copy(update={"revision_id": 7})
    (revision / "post.json").write_text(metadata.model_dump_json(), encoding="utf-8")
    target = ProjectNamingConfiguration.model_validate(
        {"revision_dirname_format": "v{revision_id}", "post_structure": {"revisions": "history"}}
    )
    ProjectConfigStore(tmp_path / "ktoolbox.toml").save(ProjectConfiguration(naming=target))
    service, _ = await service_for(tmp_path)
    held = asyncio.Event()
    release = asyncio.Event()
    original_mark = service._mark_operation
    completed = 0

    async def hold_revision_conversion(operation_id: int, status: str) -> None:
        nonlocal completed
        await original_mark(operation_id, status)
        if status == "completed":
            completed += 1
            if completed == pause_after:
                held.set()
                await release.wait()

    try:
        parsed = await service.parse_source("env", "KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./\n")
        preview = await service.preview(
            [downloads], PastedConfigConversionSource(format="env", naming=parsed.naming, digest=parsed.digest)
        )
        assert preview.conflict_count == 0
        service._mark_operation = hold_revision_conversion  # type: ignore[method-assign]
        conversion = await service.apply(preview.id, [preview.creators[0].key])
        if pause_after is not None:
            await asyncio.wait_for(held.wait(), timeout=2)
            await service.pause(conversion.id)
            release.set()
            await wait_for_conversion(service, conversion.id, "paused")
            await service.resume(conversion.id)
        await wait_for_conversion(service, conversion.id, "completed")
        work = source.parent / "Work one [one]"
        for directory in (work, work / "history/v7"):
            assert (directory / "attachments/1.jpg").read_bytes() == b"first attachment"
            assert (directory / "attachments/2.zip").read_bytes() == b"archive attachment"
            assert (directory / "attachments/3.png").read_bytes() == b"second attachment"
            assert (directory / "one_cover.png").read_bytes() == b"cover"
            assert (directory / "post.json").is_file()
            assert (directory / "notes.keep").read_bytes() == b"unrecognized file"
    finally:
        release.set()
        await service.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["resume", "cancel", "failure", "symlink"])
async def test_root_attachment_conversion_recovers_after_partial_file_moves(tmp_path: Path, action: str) -> None:
    downloads = tmp_path / "downloads"
    source = write_flat_attachment_work(downloads)
    before = {path.relative_to(downloads): path.read_bytes() for path in downloads.rglob("*") if path.is_file()}
    ProjectConfigStore(tmp_path / "ktoolbox.toml").save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)
    held = asyncio.Event()
    release = asyncio.Event()
    original_mark = service._mark_operation
    completed = 0

    async def hold_after_attachment_move(operation_id: int, status: str) -> None:
        nonlocal completed
        await original_mark(operation_id, status)
        if status == "completed":
            completed += 1
            if completed == 2:
                if action == "failure":
                    raise OSError("simulated disk failure")
                held.set()
                await release.wait()

    try:
        parsed = await service.parse_source("env", "KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./\n")
        preview = await service.preview(
            [downloads], PastedConfigConversionSource(format="env", naming=parsed.naming, digest=parsed.digest)
        )
        service._mark_operation = hold_after_attachment_move  # type: ignore[method-assign]
        conversion = await service.apply(preview.id, [preview.creators[0].key])
        if action == "failure":
            await wait_for_conversion(service, conversion.id, "failed")
            assert "simulated disk failure" in ((await service.get(conversion.id)).error or "")
        else:
            await asyncio.wait_for(held.wait(), timeout=2)
            await service.pause(conversion.id)
            release.set()
            await wait_for_conversion(service, conversion.id, "paused")
            await service.stop()
            service, _ = await service_for(tmp_path)
            if action == "symlink":
                attachment_dir = source.parent / "Work one [one]/attachments"
                outside = tmp_path / "moved-attachments"
                attachment_dir.rename(outside)
                try:
                    attachment_dir.symlink_to(outside, target_is_directory=True)
                except OSError:
                    outside.rename(attachment_dir)
                    pytest.skip("directory symlinks are unavailable")
                with pytest.raises(NamingPreviewStaleError, match="completed conversion paths changed"):
                    await service.resume(conversion.id)
                assert (await service.get(conversion.id)).status == "paused"
                attachment_dir.unlink()
                outside.rename(attachment_dir)
            if action == "resume":
                await service.resume(conversion.id)
                await wait_for_conversion(service, conversion.id, "completed")
                assert (source.parent / "Work one [one]/attachments/3.png").read_bytes() == b"second attachment"
                return
            await service.cancel(conversion.id)
            await wait_for_conversion(service, conversion.id, "cancelled")
        after = {path.relative_to(downloads): path.read_bytes() for path in downloads.rglob("*") if path.is_file()}
        assert after == before
        assert not (source.parent / "Work one [one]").exists()
    finally:
        release.set()
        await service.stop()


@pytest.mark.asyncio
async def test_cancelled_conversion_rolls_back_every_completed_move(
    tmp_path: Path,
) -> None:
    downloads = tmp_path / "downloads"
    first = write_downloaded_work(
        downloads,
        "Artist [fanbox-123]",
        "Work one",
        "one",
    )
    second = write_downloaded_work(
        downloads,
        "Artist [fanbox-123]",
        "Work two",
        "two",
    )
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)
    await save_naming(
        service,
        store,
        ProjectNamingConfiguration(post_dirname_format="{post_id}"),
    )
    preview = await preview_from_history(service, [Path("downloads")])

    first_operation = asyncio.Event()
    release_operation = asyncio.Event()
    original_mark = service._mark_operation

    async def hold_after_first_move(operation_id: int, status: str) -> None:
        await original_mark(operation_id, status)
        if status == "completed" and not first_operation.is_set():
            first_operation.set()
            await release_operation.wait()

    service._mark_operation = hold_after_first_move  # type: ignore[method-assign]
    conversion = await service.apply(preview.id, [preview.creators[0].key])
    await asyncio.wait_for(first_operation.wait(), timeout=1)
    await service.pause(conversion.id)
    release_operation.set()
    await wait_for_conversion(service, conversion.id, "paused")
    await service.cancel(conversion.id)
    await wait_for_conversion(service, conversion.id, "cancelled")

    assert first.is_dir()
    assert second.is_dir()
    assert not (downloads / "Artist [fanbox-123]" / "one").exists()
    assert not (downloads / "Artist [fanbox-123]" / "two").exists()
    await service.stop()


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

    preview = await preview_from_history(service, [Path("downloads")])

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
    second_preview = await preview_from_history(service, [Path("downloads")])
    assert second_preview.creators[0].name == "Artist"
    assert second_preview.creators[0].source == downloads / "Artist (123)"
    assert second_preview.creators[0].target == downloads / "Artist - 123"
    await service.stop()


@pytest.mark.asyncio
async def test_conversion_pauses_at_atomic_boundary_and_resumes_after_restart(
    tmp_path: Path,
) -> None:
    downloads = tmp_path / "downloads"
    write_downloaded_work(downloads, "Artist [fanbox-123]", "Work one", "one")
    write_downloaded_work(downloads, "Artist [fanbox-123]", "Work two", "two")
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
    service, _ = await service_for(tmp_path)
    candidate = ProjectNamingConfiguration(post_dirname_format="{post_id}")
    await save_naming(service, store, candidate)
    preview = await preview_from_history(service, [Path("downloads")])

    first_operation = asyncio.Event()
    release_operation = asyncio.Event()
    original_mark = service._mark_operation

    async def hold_after_first_move(operation_id: int, status: str) -> None:
        await original_mark(operation_id, status)
        if not first_operation.is_set():
            first_operation.set()
            await release_operation.wait()

    service._mark_operation = hold_after_first_move  # type: ignore[method-assign]
    conversion = await service.apply(
        preview.id,
        [preview.creators[0].key],
    )
    await asyncio.wait_for(first_operation.wait(), timeout=1)
    requested = await service.pause(conversion.id)
    assert requested.status == "pause_requested"
    release_operation.set()

    for _ in range(100):
        conversion = await service.get(conversion.id)
        if conversion.status == "paused":
            break
        await asyncio.sleep(0.01)
    assert conversion.status == "paused"
    assert conversion.progress.completed_operations == 1
    await service.stop()

    restarted, _ = await service_for(tmp_path)
    assert (await restarted.get(conversion.id)).status == "paused"
    resumed = await restarted.resume(conversion.id)
    assert resumed.status in {"queued", "running"}
    for _ in range(100):
        resumed = await restarted.get(conversion.id)
        if resumed.status == "completed":
            break
        await asyncio.sleep(0.01)
    assert resumed.status == "completed", resumed.error
    assert resumed.progress.completed_operations == resumed.progress.total_operations
    lifecycle = []
    for _ in range(100):
        lifecycle = await restarted.events.events(
            event_types={
                "naming.conversion.paused",
                "naming.conversion.resumed",
                "naming.conversion.completed",
            },
        )
        if len(lifecycle) == 3:
            break
        await asyncio.sleep(0.01)
    assert [event.event_type for event in lifecycle] == [
        "naming.conversion.paused",
        "naming.conversion.resumed",
        "naming.conversion.completed",
    ]
    assert all(event.resource_id == conversion.id for event in lifecycle)
    await restarted.stop()


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
    preview = await preview_from_history(service, [Path("downloads")])
    assert preview.conflict_count == 1
    with pytest.raises(NamingConversionError, match="conflict"):
        await service.apply(preview.id, [])

    conflict.rmdir()
    preview = await preview_from_history(service, [Path("downloads")])
    (downloads / "changed.txt").write_text("changed", encoding="utf-8")
    with pytest.raises(NamingPreviewStaleError, match="changed"):
        await service.apply(preview.id, [])

    (downloads / "changed.txt").unlink()
    preview = await preview_from_history(service, [Path("downloads")])
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
    preview = await preview_from_history(service, [Path("downloads")])
    with pytest.raises(NamingConversionError, match="select at least one"):
        await service.apply(preview.id, [])

    preview = await preview_from_history(service, [Path("downloads")])
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
    first = await preview_from_history(service, [Path("downloads")])
    second = await preview_from_history(service, [Path("downloads")])
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
    first = write_downloaded_work(downloads, "First [fanbox-123]", "Work one [one]", "one")
    second = write_downloaded_work(downloads, "Second [fanbox-456]", "Work two [two]", "two")
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

    preview = await preview_from_history(service, [Path("downloads")])

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
        "KTOOLBOX_JOB__POST_DIRNAME_FORMAT={title} [{id}]\nKTOOLBOX_JOB__FILENAME_FORMAT={id}_{}\n",
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
        versions = await client.get("/api/v1/naming/layout-versions")
        assert versions.status_code == 200
        assert len(versions.json()) == 1
        source_parse = await client.post(
            "/api/v1/naming/source/parse",
            json={
                "format": "env",
                "content": "KTOOLBOX_JOB__POST_DIRNAME_FORMAT={post_id}\n",
            },
            headers=csrf,
        )
        assert source_parse.status_code == 200
        assert source_parse.json()["naming"]["post_dirname_format"] == "{post_id}"
        assert "content" not in source_parse.json()
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
        preview_payload = {
            "roots": ["downloads"],
            "source": {
                "kind": "project_layout",
                "version_ids": [versions.json()[0]["id"]],
            },
        }
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
        "KTOOLBOX_JOB__POST_DIRNAME_FORMAT={id}\nKTOOLBOX_JOB__MIX_POSTS=true\n",
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
            "source_revisions": {source["name"]: source["revision"] for source in body["sources"]},
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
