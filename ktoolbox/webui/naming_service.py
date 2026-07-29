from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from string import Formatter
from urllib.parse import urlparse
from uuid import uuid4

import aiosqlite
import anyio
import tomlkit
from pathvalidate import is_valid_filename

from ktoolbox._enum import DataStorageNameEnum
from ktoolbox.action.utils import (
    generate_creator_path_name,
    generate_filename,
    generate_grouped_post_path,
    generate_post_path_name,
    generate_revision_path_name,
)
from ktoolbox.api.generated import Post
from ktoolbox.job import CreatorIndices
from ktoolbox.naming_migration import (
    LegacyNamingApplyResult,
    LegacyNamingPreview,
    apply_legacy_naming,
    preview_legacy_naming,
)
from ktoolbox.project_config import (
    ProjectConfigStore,
    ProjectNamingConfiguration,
    resolve_project_output,
)
from ktoolbox.webui.config_store import content_revision
from ktoolbox.webui.database import WebUIDatabase, utc_now
from ktoolbox.webui.event_store import WebUIEventStore
from ktoolbox.webui.naming_models import (
    LegacyNamingFieldResponse,
    LegacyNamingMigrationResponse,
    LegacyNamingMigrationResultResponse,
    LegacyNamingSourceResponse,
    NamingConfigurationResponse,
    NamingConversionProgress,
    NamingConversionResponse,
    NamingCreatorPreview,
    NamingLayoutVersionOrigin,
    NamingLayoutVersionResponse,
    NamingLegacyContextResponse,
    NamingPreviewResponse,
    NamingSection,
    StartupNoticeResolution,
    StartupNoticeResponse,
)
from ktoolbox.webui.task_models import ACTIVE_TASK_STATUSES
from ktoolbox.webui.task_store import TaskStore


class NamingConversionError(ValueError):
    pass


class NamingPreviewStaleError(NamingConversionError):
    pass


@dataclass(frozen=True, slots=True)
class _Move:
    creator_key: str
    source: Path
    target: Path


@dataclass(slots=True)
class _CreatorScan:
    selection_key: str
    identity: str
    name: str
    source: Path
    target: Path
    works: int
    files: int
    bytes: int
    skipped: int
    conflicts: list[str]
    moves: list[_Move]


class NamingConversionService:
    """Scan, persist, execute, and roll back project naming conversions."""

    def __init__(
        self,
        project_root: Path,
        database: WebUIDatabase,
        events: WebUIEventStore,
        tasks: TaskStore,
    ) -> None:
        self.project_root = project_root.resolve()
        self.database = database
        self.events = events
        self.tasks = tasks
        self.project_store = ProjectConfigStore(self.project_root / "ktoolbox.toml")
        self._workers: dict[str, asyncio.Task[None]] = {}
        self._cancellations: dict[str, asyncio.Event] = {}
        self._pauses: dict[str, asyncio.Event] = {}
        self._apply_lock = asyncio.Lock()

    async def start(self) -> None:
        await self._migrate_legacy_roots()
        await self._seed_layout_versions()
        await self._recover_incomplete()

    async def stop(self) -> None:
        for cancellation in self._cancellations.values():
            cancellation.set()
        if self._workers:
            await asyncio.gather(*self._workers.values(), return_exceptions=True)
        self._workers.clear()
        self._cancellations.clear()
        self._pauses.clear()

    async def legacy_context(self) -> NamingLegacyContextResponse:
        project = self.project_store.load()
        default_output = resolve_project_output(self.project_root, project)
        roots: list[Path] = [_stored_root(default_output, self.project_root)]
        async with self.database.connect() as connection:
            rows = await connection.execute_fetchall("SELECT path FROM naming_legacy_roots ORDER BY created_at, path")
        seen: set[str] = {_normalized_path(default_output)}
        for (stored_path,) in rows:
            root = Path(str(stored_path))
            normalized = _normalized_path(self._resolve_root(root))
            if normalized not in seen:
                seen.add(normalized)
                roots.append(root)
        for task in await self.tasks.list_tasks():
            resolved = task.spec.output.expanduser()
            if not resolved.is_absolute():
                resolved = self.project_root / resolved
            normalized = _normalized_path(resolved)
            if normalized not in seen:
                seen.add(normalized)
                roots.append(_stored_root(resolved, self.project_root))
        return NamingLegacyContextResponse(
            roots=roots,
            conversion_pending=await self.has_pending_layout(),
        )

    async def configuration(self) -> NamingConfigurationResponse:
        project = self.project_store.load()
        return NamingConfigurationResponse(
            default_output=project.default_output,
            resolved_default_output=resolve_project_output(self.project_root, project),
            naming=project.naming,
            revision=content_revision(self.project_store.load_text()),
            conversion_pending=await self.has_pending_layout(),
        )

    async def layout_versions(self) -> list[NamingLayoutVersionResponse]:
        current_revision = _naming_revision(self.project_store.load().naming)
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            rows = await connection.execute_fetchall(
                """
                SELECT id, revision, naming_json, origin, created_at
                FROM naming_layout_versions
                ORDER BY created_at DESC, id DESC
                """
            )
        return [
            NamingLayoutVersionResponse(
                id=row["id"],
                revision=row["revision"],
                naming=ProjectNamingConfiguration.model_validate_json(row["naming_json"]),
                origin=row["origin"],
                created_at=row["created_at"],
                is_current=row["revision"] == current_revision,
            )
            for row in rows
        ]

    async def legacy_migration(self) -> LegacyNamingMigrationResponse:
        preview = await anyio.to_thread.run_sync(
            preview_legacy_naming,
            self.project_root,
        )
        return _legacy_migration_response(preview)

    async def apply_legacy_migration(
        self,
        *,
        selected_fields: list[str],
        project_revision: str,
        source_revisions: dict[str, str],
    ) -> LegacyNamingMigrationResultResponse:
        async with self._apply_lock:
            previous = self.project_store.load().naming
            await self.events.publish(
                "naming.migration.started",
                {"field_count": len(selected_fields)},
                resource="naming",
                resource_id="legacy-naming",
            )
            try:
                result = await anyio.to_thread.run_sync(
                    lambda: apply_legacy_naming(
                        self.project_root,
                        selected_fields=set(selected_fields),
                        project_revision=project_revision,
                        source_revisions=source_revisions,
                    )
                )
            except ValueError as error:
                await self.events.publish(
                    "naming.migration.failed",
                    {"reason": "configuration_changed"},
                    resource="naming",
                    resource_id="legacy-naming",
                )
                raise NamingPreviewStaleError(str(error)) from error
            except Exception:
                await self.events.publish(
                    "naming.migration.failed",
                    {"reason": "migration_failed"},
                    resource="naming",
                    resource_id="legacy-naming",
                )
                raise
            if result.naming != previous:
                await self._record_layout_change(
                    previous,
                    result.naming,
                    create_prompt=False,
                    target_origin="legacy_migration",
                )
            await self.events.publish(
                "configuration.changed",
                {"documents": [".env", "prod.env", "ktoolbox.toml"]},
                resource="configuration",
                resource_id="legacy-naming",
            )
            await self.events.publish(
                "naming.migration.completed",
                {
                    "backup_count": len(result.backup_paths),
                    "conversion_pending": result.naming != previous,
                },
                resource="naming",
                resource_id="legacy-naming",
            )
            return _legacy_migration_result_response(result)

    async def update_naming(
        self,
        section: NamingSection,
        candidate: ProjectNamingConfiguration,
        revision: str,
        *,
        default_output: Path | None = None,
    ) -> NamingConfigurationResponse:
        async with self._apply_lock:
            current_revision = content_revision(self.project_store.load_text())
            if revision != current_revision:
                raise NamingPreviewStaleError("project configuration changed; reload before saving")
            project = self.project_store.load()
            previous = project.naming
            merged = _merge_naming_section(previous, candidate, section)
            naming_changed = merged != previous
            output_changed = (
                section == "structure" and default_output is not None and default_output != project.default_output
            )
            if naming_changed or output_changed:
                project.naming = merged
                if output_changed:
                    assert default_output is not None
                    project.default_output = default_output
                await anyio.to_thread.run_sync(self.project_store.save, project)
                if naming_changed:
                    await self._record_layout_change(previous, merged)
                await self.events.publish(
                    "naming.changed",
                    {
                        "section": section,
                        "conversion_pending": naming_changed,
                        "default_output_changed": output_changed,
                    },
                    resource="naming",
                    resource_id=section,
                )
                if output_changed:
                    await self.events.publish(
                        "configuration.changed",
                        {"documents": ["ktoolbox.toml"]},
                        resource="configuration",
                        resource_id="project-default-output",
                    )
            return await self.configuration()

    async def has_pending_layout(self) -> bool:
        async with self.database.connect() as connection:
            row = await (await connection.execute("SELECT 1 FROM naming_layout_state WHERE id = 1")).fetchone()
        return row is not None

    async def preview(self, roots: list[Path]) -> NamingPreviewResponse:
        project = self.project_store.load()
        revision = content_revision(self.project_store.load_text())
        resolved_roots = [self._resolve_root(root) for root in _unique_paths(roots)]
        if not resolved_roots:
            raise NamingConversionError("add at least one old download location before scanning")
        for root in resolved_roots:
            if not root.is_dir():
                raise NamingConversionError(f"old download location is not a directory: {root}")
            if root.is_symlink():
                raise NamingConversionError(f"old download location cannot be a symbolic link: {root}")

        sources, candidate = await self._layout_snapshots(project.naming)
        fingerprint = await anyio.to_thread.run_sync(_filesystem_fingerprint, resolved_roots)
        scans = await anyio.to_thread.run_sync(
            _scan_download_roots,
            resolved_roots,
            sources,
            candidate,
        )
        preview_id = uuid4().hex
        now = utc_now()
        creators = [
            NamingCreatorPreview(
                key=scan.selection_key,
                name=scan.name,
                source=scan.source,
                target=scan.target,
                works=scan.works,
                files=scan.files,
                bytes=scan.bytes,
                operations=len(scan.moves),
                skipped=scan.skipped,
                conflicts=scan.conflicts,
                selectable=not scan.conflicts and bool(scan.moves),
            )
            for scan in scans
        ]
        preview = NamingPreviewResponse(
            id=preview_id,
            revision=revision,
            fingerprint=fingerprint,
            roots=resolved_roots,
            creators=creators,
            creator_count=len(creators),
            work_count=sum(item.works for item in creators),
            file_count=sum(item.files for item in creators),
            total_bytes=sum(item.bytes for item in creators),
            skipped_count=sum(item.skipped for item in creators),
            conflict_count=sum(len(item.conflicts) for item in creators),
            created_at=now,
        )
        async with self.database.connect() as connection:
            await connection.execute(
                """
                INSERT INTO naming_conversions(
                    id, status, candidate_json, preview_json, fingerprint, progress_json,
                    created_at, updated_at
                ) VALUES (?, 'preview', ?, ?, ?, ?, ?, ?)
                """,
                (
                    preview_id,
                    candidate.model_dump_json(),
                    preview.model_dump_json(),
                    fingerprint,
                    NamingConversionProgress().model_dump_json(),
                    now.isoformat(),
                    now.isoformat(),
                ),
            )
            for sequence, move in enumerate(
                (move for scan in scans for move in scan.moves),
                start=1,
            ):
                await connection.execute(
                    """
                    INSERT INTO naming_operations(
                        conversion_id, sequence, creator_key, source, target, status
                    ) VALUES (?, ?, ?, ?, ?, 'planned')
                    """,
                    (
                        preview_id,
                        sequence,
                        move.creator_key,
                        str(move.source),
                        str(move.target),
                    ),
                )
            await connection.commit()
        return preview

    async def apply(
        self,
        preview_id: str,
        selected_creators: list[str],
    ) -> NamingConversionResponse:
        async with self._apply_lock:
            return await self._apply(preview_id, selected_creators)

    async def _apply(
        self,
        preview_id: str,
        selected_creators: list[str],
    ) -> NamingConversionResponse:
        conversion = await self.get(preview_id)
        if conversion.status != "preview":
            raise NamingConversionError("this preview has already been applied")
        await self._ensure_no_active_conversion()
        await self._ensure_preview_current(conversion.preview)
        selected = selected_creators
        allowed = {creator.key for creator in conversion.preview.creators if creator.selectable}
        if unknown := sorted(set(selected) - allowed):
            raise NamingConversionError("selected creators are unavailable: " + ", ".join(unknown))
        if conversion.preview.conflict_count:
            raise NamingConversionError("resolve every target path conflict before applying this preview")

        candidate = ProjectNamingConfiguration.model_validate_json(await self._candidate_json(preview_id))
        available_operations = await self._operations(preview_id, [], reverse=False)
        if not available_operations:
            await self._clear_layout_state(candidate)
            await self._resolve_layout_notices(candidate, "convert_selected")
            await self._set_status(preview_id, "completed", selected=[])
            await self.events.publish(
                "naming.changed",
                {"conversion_id": preview_id, "converted": False, "already_current": True},
                resource="naming",
                resource_id=preview_id,
            )
            return await self.get(preview_id)

        if not selected:
            raise NamingConversionError("select at least one downloaded creator to convert")
        await self._ensure_no_overlapping_tasks(conversion.preview.roots)
        await self._resolve_layout_notices(candidate, "convert_selected")
        await self._set_status(preview_id, "queued", selected=selected)
        await self.events.publish(
            "naming.conversion.started",
            {"status": "queued"},
            resource="naming",
            resource_id=preview_id,
        )
        self._start_conversion_worker(preview_id, candidate, selected)
        return await self.get(preview_id)

    async def pause(self, conversion_id: str) -> NamingConversionResponse:
        pause = self._pauses.get(conversion_id)
        if pause is None:
            await self.get(conversion_id)
            raise NamingConversionError("conversion worker is not active")
        changed = await self._set_status_if_current(
            conversion_id,
            {"queued", "running"},
            "pause_requested",
        )
        if not changed:
            raise NamingConversionError("only queued or running conversions can be paused")
        pause.set()
        return await self.get(conversion_id)

    async def resume(self, conversion_id: str) -> NamingConversionResponse:
        async with self._apply_lock:
            conversion = await self.get(conversion_id)
            if conversion.status != "paused":
                raise NamingConversionError("only paused conversions can be resumed")
            await self._ensure_no_active_conversion(exclude_id=conversion_id)
            await self._ensure_no_overlapping_tasks(conversion.preview.roots)
            await self._validate_resume_state(conversion)
            candidate = ProjectNamingConfiguration.model_validate_json(await self._candidate_json(conversion_id))
            await self._set_status(conversion_id, "queued")
            await self.events.publish(
                "naming.conversion.resumed",
                {"status": "queued"},
                resource="naming",
                resource_id=conversion_id,
            )
            self._start_conversion_worker(
                conversion_id,
                candidate,
                conversion.selected_creators,
            )
            return await self.get(conversion_id)

    async def cancel(self, conversion_id: str) -> NamingConversionResponse:
        conversion = await self.get(conversion_id)
        if conversion.status not in {"queued", "running", "pause_requested", "paused"}:
            raise NamingConversionError("only active or paused conversions can be cancelled")
        if conversion.status == "paused":
            await self._set_status(conversion_id, "rolling_back")
            worker = asyncio.create_task(
                self._rollback(conversion_id, "cancelled"),
                name=f"naming-conversion-rollback-{conversion_id}",
            )
            self._track_worker(conversion_id, worker)
            return await self.get(conversion_id)
        cancellation = self._cancellations.get(conversion_id)
        if cancellation is None:
            raise NamingConversionError("conversion worker is not active")
        cancellation.set()
        return await self.get(conversion_id)

    async def list_conversions(self) -> list[NamingConversionResponse]:
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            rows = await connection.execute_fetchall("SELECT * FROM naming_conversions ORDER BY created_at DESC")
        return [_conversion_from_row(row) for row in rows]

    async def get(self, conversion_id: str) -> NamingConversionResponse:
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                "SELECT * FROM naming_conversions WHERE id = ?",
                (conversion_id,),
            )
            row = await cursor.fetchone()
            await cursor.close()
        if row is None:
            raise LookupError(conversion_id)
        return _conversion_from_row(row)

    async def delete(self, conversion_id: str) -> None:
        conversion = await self.get(conversion_id)
        if conversion.status in {
            "queued",
            "running",
            "pause_requested",
            "paused",
            "rolling_back",
        }:
            raise NamingConversionError("active conversion history cannot be deleted")
        async with self.database.connect() as connection:
            await connection.execute(
                "DELETE FROM naming_conversions WHERE id = ?",
                (conversion_id,),
            )
            await connection.commit()

    async def notices(self) -> list[StartupNoticeResponse]:
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            rows = await connection.execute_fetchall(
                "SELECT * FROM startup_notices WHERE acknowledged_at IS NULL ORDER BY created_at"
            )
        return [_notice_from_row(row) for row in rows]

    async def acknowledge_notice(self, notice_id: str) -> StartupNoticeResponse:
        now = utc_now()
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            await connection.execute(
                """
                UPDATE startup_notices SET acknowledged_at = ?
                WHERE id = ? AND acknowledged_at IS NULL
                """,
                (now.isoformat(), notice_id),
            )
            await connection.commit()
            row = await (
                await connection.execute(
                    "SELECT * FROM startup_notices WHERE id = ?",
                    (notice_id,),
                )
            ).fetchone()
        if row is None:
            raise LookupError(notice_id)
        return _notice_from_row(row)

    async def resolve_notice(
        self,
        notice_id: str,
        action: StartupNoticeResolution,
    ) -> StartupNoticeResponse:
        now = utc_now()
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            await connection.execute(
                """
                UPDATE startup_notices
                SET resolution = ?, resolved_at = ?, acknowledged_at = ?
                WHERE id = ? AND kind = 'legacy_layout_conversion'
                  AND resolution IS NULL
                """,
                (action, now.isoformat(), now.isoformat(), notice_id),
            )
            await connection.commit()
            row = await (
                await connection.execute(
                    "SELECT * FROM startup_notices WHERE id = ?",
                    (notice_id,),
                )
            ).fetchone()
        if row is None or row["kind"] != "legacy_layout_conversion":
            raise LookupError(notice_id)
        notice = _notice_from_row(row)
        await self.events.publish(
            "naming.changed",
            {
                "layout_version": notice.id,
                "layout_resolution": action,
            },
            resource="naming",
            resource_id=notice.id,
        )
        return notice

    async def _record_layout_change(
        self,
        previous: ProjectNamingConfiguration,
        target: ProjectNamingConfiguration,
        *,
        create_prompt: bool = True,
        target_origin: NamingLayoutVersionOrigin = "project_change",
    ) -> None:
        now = utc_now().isoformat()
        async with self.database.connect() as connection:
            await self._store_layout_version(
                connection,
                previous,
                origin="project_change",
                created_at=now,
            )
            await self._store_layout_version(
                connection,
                target,
                origin=target_origin,
                created_at=now,
            )
            row = await (
                await connection.execute("SELECT sources_json FROM naming_layout_state WHERE id = 1")
            ).fetchone()
            sources = (
                [ProjectNamingConfiguration.model_validate(item) for item in json.loads(str(row[0]))]
                if row is not None
                else []
            )
            if previous not in sources:
                sources.append(previous)
            await connection.execute(
                """
                INSERT INTO naming_layout_state(id, sources_json, target_json, updated_at)
                VALUES (1, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    sources_json = excluded.sources_json,
                    target_json = excluded.target_json,
                    updated_at = excluded.updated_at
                """,
                (
                    json.dumps(
                        [item.model_dump(mode="json") for item in sources],
                        ensure_ascii=False,
                    ),
                    target.model_dump_json(),
                    now,
                ),
            )
            if create_prompt:
                await connection.execute(
                    """
                    UPDATE startup_notices
                    SET resolution = 'superseded', resolved_at = ?, acknowledged_at = ?
                    WHERE kind = 'legacy_layout_conversion'
                      AND resolution IS NULL
                    """,
                    (now, now),
                )
                version_id = f"naming-layout-{uuid4().hex}"
                await connection.execute(
                    """
                    INSERT INTO startup_notices(
                        id, kind, payload_json, created_at
                    ) VALUES (?, 'legacy_layout_conversion', ?, ?)
                    """,
                    (
                        version_id,
                        json.dumps(
                            {
                                "version": version_id,
                                "source": previous.model_dump(mode="json"),
                                "target": target.model_dump(mode="json"),
                            },
                            ensure_ascii=False,
                        ),
                        now,
                    ),
                )
            await connection.commit()

    async def _seed_layout_versions(self) -> None:
        current = self.project_store.load().naming
        now = utc_now().isoformat()
        recovered: list[ProjectNamingConfiguration] = []
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            state = await (
                await connection.execute("SELECT sources_json, target_json FROM naming_layout_state WHERE id = 1")
            ).fetchone()
            if state is not None:
                recovered.extend(
                    ProjectNamingConfiguration.model_validate(item) for item in json.loads(str(state["sources_json"]))
                )
                recovered.append(ProjectNamingConfiguration.model_validate_json(str(state["target_json"])))
            notices = await connection.execute_fetchall(
                """
                SELECT payload_json FROM startup_notices
                WHERE kind = 'legacy_layout_conversion'
                """
            )
            for notice in notices:
                try:
                    payload = json.loads(str(notice["payload_json"]))
                    recovered.extend(
                        ProjectNamingConfiguration.model_validate(payload[key])
                        for key in ("source", "target")
                        if payload.get(key) is not None
                    )
                except (TypeError, ValueError):
                    continue
            for naming in recovered:
                await self._store_layout_version(
                    connection,
                    naming,
                    origin="recovered",
                    created_at=now,
                )
            await self._store_layout_version(
                connection,
                current,
                origin="project_current",
                created_at=now,
            )
            await connection.commit()

    async def _store_layout_version(
        self,
        connection: aiosqlite.Connection,
        naming: ProjectNamingConfiguration,
        *,
        origin: NamingLayoutVersionOrigin,
        created_at: str,
    ) -> str:
        revision = _naming_revision(naming)
        version_id = f"naming-layout-{revision[:24]}"
        await connection.execute(
            """
            INSERT OR IGNORE INTO naming_layout_versions(
                id, revision, naming_json, origin, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                version_id,
                revision,
                _canonical_naming_json(naming),
                origin,
                created_at,
            ),
        )
        return version_id

    async def _resolve_layout_notices(
        self,
        target: ProjectNamingConfiguration,
        action: StartupNoticeResolution,
    ) -> None:
        target_data = target.model_dump(mode="json")
        now = utc_now().isoformat()
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            rows = await connection.execute_fetchall(
                """
                SELECT id, payload_json FROM startup_notices
                WHERE kind = 'legacy_layout_conversion'
                  AND resolution IS NULL
                """
            )
            matching = [
                str(row["id"]) for row in rows if json.loads(str(row["payload_json"])).get("target") == target_data
            ]
            if matching:
                placeholders = ",".join("?" for _ in matching)
                await connection.execute(
                    f"""
                    UPDATE startup_notices
                    SET resolution = ?, resolved_at = ?, acknowledged_at = ?
                    WHERE id IN ({placeholders})
                    """,
                    [action, now, now, *matching],
                )
                await connection.commit()

    async def _layout_snapshots(
        self,
        current: ProjectNamingConfiguration,
    ) -> tuple[list[ProjectNamingConfiguration], ProjectNamingConfiguration]:
        async with self.database.connect() as connection:
            row = await (
                await connection.execute("SELECT sources_json, target_json FROM naming_layout_state WHERE id = 1")
            ).fetchone()
        if row is None:
            return [current], current
        sources = [ProjectNamingConfiguration.model_validate(item) for item in json.loads(str(row[0]))]
        target = ProjectNamingConfiguration.model_validate_json(str(row[1]))
        return sources or [current], target

    async def _clear_layout_state(self, candidate: ProjectNamingConfiguration) -> None:
        async with self.database.connect() as connection:
            row = await (
                await connection.execute("SELECT target_json FROM naming_layout_state WHERE id = 1")
            ).fetchone()
            if row is not None:
                target = ProjectNamingConfiguration.model_validate_json(str(row[0]))
                if target != candidate:
                    raise NamingPreviewStaleError("naming layout changed during conversion; create a new preview")
                await connection.execute("DELETE FROM naming_layout_state WHERE id = 1")
                await connection.commit()

    async def _migrate_legacy_roots(self) -> None:
        if not self.project_store.path.is_file():
            return
        try:
            document = tomlkit.parse(self.project_store.load_text())
            naming = document.unwrap().get("naming")
            raw_roots = list(naming.get("download_roots", [])) if isinstance(naming, Mapping) else []
        except (OSError, ValueError, TypeError):
            return
        if not raw_roots:
            return
        now = utc_now().isoformat()
        async with self.database.connect() as connection:
            await connection.executemany(
                """
                INSERT OR IGNORE INTO naming_legacy_roots(path, created_at)
                VALUES (?, ?)
                """,
                [(str(root), now) for root in raw_roots],
            )
            await connection.commit()
        configuration = self.project_store.load()
        await anyio.to_thread.run_sync(self.project_store.save, configuration)

    async def _run_conversion(
        self,
        conversion_id: str,
        candidate: ProjectNamingConfiguration,
        selected: list[str],
        cancellation: asyncio.Event,
        pause: asyncio.Event,
    ) -> None:
        try:
            await self._set_status(conversion_id, "running", selected=selected)
            conversion = await self.get(conversion_id)
            all_operations = await self._operations(
                conversion_id,
                selected,
                reverse=False,
            )
            operations = [row for row in all_operations if row["status"] == "planned"]
            progress = NamingConversionProgress(
                completed_operations=sum(1 for row in all_operations if row["status"] == "completed"),
                total_operations=len(all_operations),
            )
            await self._set_progress(conversion_id, progress)
            for operation in operations:
                if cancellation.is_set():
                    raise asyncio.CancelledError
                if pause.is_set():
                    await self._set_status(conversion_id, "paused")
                    await self.events.publish(
                        "naming.conversion.paused",
                        {"status": "paused"},
                        resource="naming",
                        resource_id=conversion_id,
                    )
                    return
                source = Path(operation["source"])
                target = Path(operation["target"])
                if not await anyio.to_thread.run_sync(source.exists):
                    raise NamingConversionError(f"source changed since preview: {source}")
                if await anyio.to_thread.run_sync(target.exists):
                    raise NamingConversionError(f"target now exists: {target}")
                await anyio.to_thread.run_sync(target.parent.mkdir, 0o777, True, True)
                await anyio.to_thread.run_sync(os.replace, source, target)
                await anyio.to_thread.run_sync(
                    _remove_empty_ancestors,
                    source.parent,
                    conversion.preview.roots,
                )
                await self._mark_operation(int(operation["id"]), "completed")
                progress.completed_operations += 1
                progress.current_creator = str(operation["creator_key"])
                await self._set_progress(conversion_id, progress)
                if cancellation.is_set():
                    raise asyncio.CancelledError
                if pause.is_set():
                    await self._set_status(conversion_id, "paused")
                    await self.events.publish(
                        "naming.conversion.paused",
                        {"status": "paused"},
                        resource="naming",
                        resource_id=conversion_id,
                    )
                    return
            conversion = await self.get(conversion_id)
            if content_revision(self.project_store.load_text()) != conversion.preview.revision:
                raise NamingPreviewStaleError(
                    "project configuration changed during conversion; moved files will be rolled back"
                )
            await self._clear_layout_state(candidate)
            await self._set_status(conversion_id, "completed", selected=selected)
            await self.events.publish(
                "naming.changed",
                {"conversion_id": conversion_id, "converted": True},
                resource="naming",
                resource_id=conversion_id,
            )
        except asyncio.CancelledError:
            await self._rollback(conversion_id, "cancelled")
        except Exception as error:
            await self._rollback(conversion_id, "failed", error=str(error))
        finally:
            if self._cancellations.get(conversion_id) is cancellation:
                self._cancellations.pop(conversion_id, None)
            if self._pauses.get(conversion_id) is pause:
                self._pauses.pop(conversion_id, None)

    def _start_conversion_worker(
        self,
        conversion_id: str,
        candidate: ProjectNamingConfiguration,
        selected: list[str],
    ) -> None:
        cancellation = asyncio.Event()
        pause = asyncio.Event()
        self._cancellations[conversion_id] = cancellation
        self._pauses[conversion_id] = pause
        worker = asyncio.create_task(
            self._run_conversion(
                conversion_id,
                candidate,
                selected,
                cancellation,
                pause,
            ),
            name=f"naming-conversion-{conversion_id}",
        )
        self._track_worker(conversion_id, worker)

    def _track_worker(
        self,
        conversion_id: str,
        worker: asyncio.Task[None],
    ) -> None:
        self._workers[conversion_id] = worker

        def remove(completed: asyncio.Task[None]) -> None:
            if self._workers.get(conversion_id) is completed:
                self._workers.pop(conversion_id, None)

        worker.add_done_callback(remove)

    async def _rollback(
        self,
        conversion_id: str,
        final_status: str,
        *,
        error: str | None = None,
    ) -> None:
        await self._set_status(conversion_id, "rolling_back", error=error)
        conversion = await self.get(conversion_id)
        rollback_error: str | None = None
        for operation in await self._operations(conversion_id, [], reverse=True, completed_only=True):
            source = Path(operation["source"])
            target = Path(operation["target"])
            try:
                if await anyio.to_thread.run_sync(target.exists):
                    await anyio.to_thread.run_sync(source.parent.mkdir, 0o777, True, True)
                    if await anyio.to_thread.run_sync(source.exists):
                        raise NamingConversionError(f"rollback target already exists: {source}")
                    await anyio.to_thread.run_sync(os.replace, target, source)
                    await anyio.to_thread.run_sync(
                        _remove_empty_ancestors,
                        target.parent,
                        conversion.preview.roots,
                    )
                await self._mark_operation(int(operation["id"]), "rolled_back")
            except Exception as rollback_failure:
                rollback_error = str(rollback_failure)
                break
        await self._set_status(
            conversion_id,
            final_status,
            error=rollback_error or error,
        )

    async def _ensure_preview_current(self, preview: NamingPreviewResponse) -> None:
        if content_revision(self.project_store.load_text()) != preview.revision:
            raise NamingPreviewStaleError("project configuration changed; create a new preview")
        fingerprint = await anyio.to_thread.run_sync(
            _filesystem_fingerprint,
            preview.roots,
        )
        if fingerprint != preview.fingerprint:
            raise NamingPreviewStaleError("download directories changed; create a new preview")

    def _resolve_root(self, root: Path) -> Path:
        expanded = root.expanduser()
        if not expanded.is_absolute():
            expanded = self.project_root / expanded
        return expanded.resolve(strict=False)

    async def _ensure_no_overlapping_tasks(self, roots: list[Path]) -> None:
        active = [task for task in await self.tasks.list_tasks() if task.status in ACTIVE_TASK_STATUSES]
        for task in active:
            output = task.spec.output.expanduser()
            if not output.is_absolute():
                output = self.project_root / output
            if any(_paths_overlap(output, root) for root in roots):
                raise NamingConversionError(
                    f"task {task.id} overlaps a selected download root; stop it before converting"
                )

    async def _ensure_no_active_conversion(
        self,
        *,
        exclude_id: str | None = None,
    ) -> None:
        parameters: list[object] = []
        exclusion = ""
        if exclude_id is not None:
            exclusion = "AND id != ?"
            parameters.append(exclude_id)
        async with self.database.connect() as connection:
            row = await (
                await connection.execute(
                    f"""
                    SELECT id FROM naming_conversions
                    WHERE status IN (
                        'queued', 'running', 'pause_requested', 'paused', 'rolling_back'
                    )
                    {exclusion}
                    LIMIT 1
                    """,
                    parameters,
                )
            ).fetchone()
        if row is not None:
            raise NamingConversionError(
                "another naming conversion is already active; wait for it to finish or cancel it"
            )

    async def _validate_resume_state(
        self,
        conversion: NamingConversionResponse,
    ) -> None:
        if content_revision(self.project_store.load_text()) != conversion.preview.revision:
            raise NamingPreviewStaleError("project configuration changed while conversion was paused")
        operations = await self._operations(
            conversion.id,
            conversion.selected_creators,
            reverse=False,
        )
        await anyio.to_thread.run_sync(
            _validate_resume_filesystem,
            conversion.preview.roots,
            [
                (
                    str(operation["status"]),
                    Path(operation["source"]),
                    Path(operation["target"]),
                )
                for operation in operations
            ],
        )

    async def _candidate_json(self, conversion_id: str) -> str:
        async with self.database.connect() as connection:
            row = await (
                await connection.execute(
                    "SELECT candidate_json FROM naming_conversions WHERE id = ?",
                    (conversion_id,),
                )
            ).fetchone()
        if row is None:
            raise LookupError(conversion_id)
        return str(row[0])

    async def _operations(
        self,
        conversion_id: str,
        selected: list[str],
        *,
        reverse: bool,
        completed_only: bool = False,
    ) -> list[aiosqlite.Row]:
        query = "SELECT * FROM naming_operations WHERE conversion_id = ?"
        parameters: list[object] = [conversion_id]
        if selected:
            placeholders = ",".join("?" for _ in selected)
            query += f" AND creator_key IN ({placeholders})"
            parameters.extend(selected)
        if completed_only:
            query += " AND status = 'completed'"
        query += " ORDER BY sequence " + ("DESC" if reverse else "ASC")
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            rows = await connection.execute_fetchall(query, parameters)
        return list(rows)

    async def _mark_operation(self, operation_id: int, status: str) -> None:
        async with self.database.connect() as connection:
            await connection.execute(
                "UPDATE naming_operations SET status = ? WHERE id = ?",
                (status, operation_id),
            )
            await connection.commit()

    async def _set_progress(
        self,
        conversion_id: str,
        progress: NamingConversionProgress,
    ) -> None:
        async with self.database.connect() as connection:
            await connection.execute(
                "UPDATE naming_conversions SET progress_json = ?, updated_at = ? WHERE id = ?",
                (progress.model_dump_json(), utc_now().isoformat(), conversion_id),
            )
            await connection.commit()
        await self.events.publish(
            "naming.conversion.progress",
            {"progress": progress.model_dump(mode="json")},
            resource="naming",
            resource_id=conversion_id,
        )

    async def _set_status(
        self,
        conversion_id: str,
        status: str,
        *,
        selected: list[str] | None = None,
        error: str | None = None,
    ) -> None:
        updates = "status = ?, error = ?, updated_at = ?"
        parameters: list[object] = [status, error, utc_now().isoformat()]
        if selected is not None:
            updates += ", selected_json = ?"
            parameters.append(json.dumps(selected, ensure_ascii=False))
        parameters.append(conversion_id)
        async with self.database.connect() as connection:
            await connection.execute(
                f"UPDATE naming_conversions SET {updates} WHERE id = ?",
                parameters,
            )
            await connection.commit()
        await self.events.publish(
            "naming.conversion.finished"
            if status in {"completed", "failed", "cancelled"}
            else "naming.conversion.progress",
            {"status": status, "error": error},
            resource="naming",
            resource_id=conversion_id,
        )
        lifecycle_event = {
            "completed": "naming.conversion.completed",
            "failed": "naming.conversion.failed",
            "cancelled": "naming.conversion.cancelled",
        }.get(status)
        if lifecycle_event is not None:
            await self.events.publish(
                lifecycle_event,
                {"status": status, "has_error": error is not None},
                resource="naming",
                resource_id=conversion_id,
            )

    async def _set_status_if_current(
        self,
        conversion_id: str,
        allowed: set[str],
        status: str,
    ) -> bool:
        placeholders = ",".join("?" for _ in allowed)
        now = utc_now().isoformat()
        async with self.database.connect() as connection:
            cursor = await connection.execute(
                f"""
                UPDATE naming_conversions
                SET status = ?, error = NULL, updated_at = ?
                WHERE id = ? AND status IN ({placeholders})
                """,
                [status, now, conversion_id, *sorted(allowed)],
            )
            await connection.commit()
            changed = cursor.rowcount == 1
            await cursor.close()
        if changed:
            await self.events.publish(
                "naming.conversion.progress",
                {"status": status, "error": None},
                resource="naming",
                resource_id=conversion_id,
            )
        return changed

    async def _recover_incomplete(self) -> None:
        async with self.database.connect() as connection:
            rows = await connection.execute_fetchall(
                """
                SELECT id FROM naming_conversions
                WHERE status IN ('queued', 'running', 'pause_requested', 'rolling_back')
                """
            )
        for (conversion_id,) in rows:
            await self._rollback(
                str(conversion_id),
                "failed",
                error="WebUI stopped during naming conversion; completed moves were rolled back",
            )


def _validate_resume_filesystem(
    roots: list[Path],
    operations: list[tuple[str, Path, Path]],
) -> None:
    for root in roots:
        if not root.is_dir() or root.is_symlink():
            raise NamingPreviewStaleError(f"download location changed while conversion was paused: {root}")
        if shutil.disk_usage(root).free <= 0:
            raise NamingConversionError(f"download location has no free space: {root}")
    for status, source, target in operations:
        if status == "completed":
            if source.exists() or not target.exists():
                raise NamingPreviewStaleError("completed conversion paths changed while paused")
        elif status == "planned":
            if not source.exists() or target.exists():
                raise NamingPreviewStaleError("pending conversion paths changed while paused")
        else:
            raise NamingPreviewStaleError("conversion operation state changed while paused")


def _scan_download_roots(
    roots: list[Path],
    sources: list[ProjectNamingConfiguration],
    candidate: ProjectNamingConfiguration,
) -> list[_CreatorScan]:
    scans: list[_CreatorScan] = []
    for root in roots:
        metadata_paths = _outermost_metadata_paths(root)
        grouped: dict[tuple[str, str, Path], list[tuple[Path, Post]]] = {}
        skipped_by_creator: dict[Path, int] = {}
        for metadata in metadata_paths:
            if _has_symlink_component(metadata.relative_to(root), root):
                creator = root / metadata.relative_to(root).parts[0]
                skipped_by_creator[creator] = skipped_by_creator.get(creator, 0) + 1
                continue
            try:
                post = Post.model_validate_json(metadata.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                creator = root / metadata.relative_to(root).parts[0]
                skipped_by_creator[creator] = skipped_by_creator.get(creator, 0) + 1
                continue
            relative = metadata.relative_to(root)
            if len(relative.parts) < 2:
                continue
            creator = root / relative.parts[0]
            grouped.setdefault((post.service, post.user, creator), []).append((metadata.parent, post))

        _add_indexed_works(root, sources, grouped, skipped_by_creator)
        grouped_creators = {creator for _, _, creator in grouped}
        for (service, creator_id, source_creator), works in grouped.items():
            current = _source_naming_for_creator(
                source_creator,
                service,
                creator_id,
                works,
                sources,
            )
            name = _creator_name(source_creator.name, service, creator_id, current)
            identity = f"{service}:{creator_id}"
            selection_key = f"{identity}@{hashlib.sha1(str(source_creator).encode()).hexdigest()[:10]}"
            target_creator = root / generate_creator_path_name(
                service,
                creator_id,
                name,
                candidate,
            )
            moves: list[_Move] = []
            conflicts: list[str] = []
            for source_work, post in works:
                target_work = generate_grouped_post_path(post, target_creator, candidate) / generate_post_path_name(
                    post, candidate
                )
                work_base = source_work
                if source_work != target_work:
                    if target_work.exists():
                        conflicts.append(str(target_work))
                    else:
                        moves.append(_Move(selection_key, source_work, target_work))
                        work_base = target_work
                nested_moves, nested_conflicts = _work_structure_moves(
                    selection_key,
                    source_work,
                    work_base,
                    post,
                    current,
                    candidate,
                )
                moves.extend(nested_moves)
                conflicts.extend(nested_conflicts)

            index_source = source_creator / DataStorageNameEnum.CreatorIndicesData.value
            index_target = target_creator / DataStorageNameEnum.CreatorIndicesData.value
            if index_source.is_file() and index_source != index_target:
                if index_target.exists():
                    conflicts.append(str(index_target))
                else:
                    moves.append(_Move(selection_key, index_source, index_target))

            files, size, symlinks = _tree_stats(source_creator)
            scans.append(
                _CreatorScan(
                    selection_key=selection_key,
                    identity=identity,
                    name=name,
                    source=source_creator,
                    target=target_creator,
                    works=len(works),
                    files=files,
                    bytes=size,
                    skipped=skipped_by_creator.get(source_creator, 0) + symlinks,
                    conflicts=conflicts,
                    moves=moves,
                )
            )
        for source_creator in _direct_creator_directories(root):
            if source_creator in grouped_creators:
                continue
            parsed = next(
                (
                    (creator_identity, source)
                    for source in sources
                    if (
                        creator_identity := _creator_identity_from_directory(
                            source_creator,
                            source,
                        )
                    )
                    is not None
                ),
                None,
            )
            if parsed is None:
                continue
            parsed_identity, current = parsed
            service, creator_id, name = parsed_identity
            selection_key = f"{service}:{creator_id}@{hashlib.sha1(str(source_creator).encode()).hexdigest()[:10]}"
            target_creator = root / generate_creator_path_name(
                service,
                creator_id,
                name,
                candidate,
            )
            fallback_moves: list[_Move] = []
            fallback_conflicts: list[str] = []
            if source_creator != target_creator:
                if target_creator.exists():
                    fallback_conflicts.append(str(target_creator))
                else:
                    fallback_moves.append(_Move(selection_key, source_creator, target_creator))
            files, size, symlinks = _tree_stats(source_creator)
            scans.append(
                _CreatorScan(
                    selection_key=selection_key,
                    identity=f"{service}:{creator_id}",
                    name=name,
                    source=source_creator,
                    target=target_creator,
                    works=0,
                    files=files,
                    bytes=size,
                    skipped=files + symlinks,
                    conflicts=fallback_conflicts,
                    moves=fallback_moves,
                )
            )
    _mark_duplicate_targets(scans)
    return scans


def _add_indexed_works(
    root: Path,
    sources: list[ProjectNamingConfiguration],
    grouped: dict[tuple[str, str, Path], list[tuple[Path, Post]]],
    skipped_by_creator: dict[Path, int],
) -> None:
    known_posts = {
        (service, creator_id, creator, post.id)
        for (service, creator_id, creator), works in grouped.items()
        for _, post in works
    }
    for creator in _direct_creator_directories(root):
        index_path = creator / DataStorageNameEnum.CreatorIndicesData.value
        if not index_path.is_file() or index_path.is_symlink():
            continue
        try:
            index = CreatorIndices.model_validate_json(index_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            skipped_by_creator[creator] = skipped_by_creator.get(creator, 0) + 1
            continue
        for post in index.posts.values():
            key = (index.service, index.creator_id, creator, post.id)
            if key in known_posts:
                continue
            source_work = next(
                (
                    path
                    for source in sources
                    if not source.mix_posts
                    and (
                        path := generate_grouped_post_path(post, creator, source)
                        / generate_post_path_name(post, source)
                    ).is_dir()
                    and not path.is_symlink()
                ),
                None,
            )
            if source_work is not None:
                grouped.setdefault(
                    (index.service, index.creator_id, creator),
                    [],
                ).append((source_work, post))
                known_posts.add(key)
            else:
                skipped_by_creator[creator] = skipped_by_creator.get(creator, 0) + 1


def _source_naming_for_creator(
    creator: Path,
    service: str,
    creator_id: str,
    works: list[tuple[Path, Post]],
    sources: list[ProjectNamingConfiguration],
) -> ProjectNamingConfiguration:
    def score(source: ProjectNamingConfiguration) -> tuple[int, int]:
        matching_works = sum(
            1
            for work_path, post in works
            if generate_grouped_post_path(post, creator, source) / generate_post_path_name(post, source) == work_path
        )
        identity = _creator_identity_from_template(
            creator.name,
            source.creator_dirname_format,
        )
        matching_creator = int(
            identity is not None
            and identity[0].casefold() == service.casefold()
            and identity[1].casefold() == creator_id.casefold()
        )
        return matching_works, matching_creator

    return max(sources, key=score)


def _direct_creator_directories(root: Path) -> list[Path]:
    try:
        return sorted(
            (
                child
                for child in root.iterdir()
                if child.is_dir() and not child.is_symlink() and child.name != ".ktoolbox"
            ),
            key=str,
        )
    except OSError:
        return []


def _creator_identity_from_directory(
    path: Path,
    naming: ProjectNamingConfiguration,
) -> tuple[str, str, str] | None:
    index_path = path / DataStorageNameEnum.CreatorIndicesData.value
    if index_path.is_file() and not index_path.is_symlink():
        try:
            index = CreatorIndices.model_validate_json(index_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        else:
            return (
                index.service,
                index.creator_id,
                _creator_name(path.name, index.service, index.creator_id, naming),
            )
    template_identity = _creator_identity_from_template(
        path.name,
        naming.creator_dirname_format,
    )
    if template_identity is not None:
        return template_identity
    match = re.fullmatch(r"(.*?)\s*\[([A-Za-z0-9_]+)-(.+)]", path.name)
    if match is None:
        return None
    name, service, creator_id = match.groups()
    return service, creator_id, name.strip() or creator_id


def _mark_duplicate_targets(scans: list[_CreatorScan]) -> None:
    targets: dict[str, list[_CreatorScan]] = {}
    for scan in scans:
        for move in scan.moves:
            targets.setdefault(_normalized_path(move.target), []).append(scan)
    for normalized_target, duplicate_scans in targets.items():
        if len(duplicate_scans) < 2:
            continue
        target = next(
            move.target for move in duplicate_scans[0].moves if _normalized_path(move.target) == normalized_target
        )
        for scan in duplicate_scans:
            conflict = str(target)
            if conflict not in scan.conflicts:
                scan.conflicts.append(conflict)


def _outermost_metadata_paths(root: Path) -> list[Path]:
    candidates = sorted(
        root.rglob(DataStorageNameEnum.PostData.value),
        key=lambda path: len(path.parts),
    )
    selected: list[Path] = []
    selected_dirs: set[Path] = set()
    for candidate in candidates:
        if any(parent in selected_dirs for parent in candidate.parents):
            continue
        selected.append(candidate)
        selected_dirs.add(candidate.parent)
    return selected


def _work_structure_moves(
    creator_key: str,
    source_work: Path,
    work_base: Path,
    post: Post,
    current: ProjectNamingConfiguration,
    candidate: ProjectNamingConfiguration,
) -> tuple[list[_Move], list[str]]:
    moves: list[_Move] = []
    conflicts: list[str] = []

    def add(source_relative: Path, target_relative: Path) -> None:
        if source_relative == target_relative:
            return
        original_source = source_work / source_relative
        if not original_source.exists() or original_source.is_symlink():
            return
        source = work_base / source_relative
        target = work_base / target_relative
        original_target = source_work / target_relative
        if original_target.exists() and original_target != original_source:
            conflicts.append(str(target))
        else:
            moves.append(_Move(creator_key, source, target))

    primary = post.file
    if primary and primary.path:
        basic = (
            Path(primary.name)
            if primary.name and is_valid_filename(primary.name)
            else Path(urlparse(primary.path).path)
        )
        old_name = generate_filename(post, basic.name, current.post_structure.file)
        new_name = generate_filename(post, basic.name, candidate.post_structure.file)
        add(Path(old_name), Path(new_name))

    sequence = 1
    for attachment in post.attachments or []:
        if not attachment.path:
            continue
        basic_path = (
            Path(attachment.name)
            if attachment.name and is_valid_filename(attachment.name)
            else Path(urlparse(attachment.path).path)
        )
        old_basic, old_sequence = _attachment_basic_name(basic_path, current, sequence)
        new_basic, new_sequence = _attachment_basic_name(basic_path, candidate, sequence)
        old_name = generate_filename(post, old_basic, current.filename_format)
        new_name = generate_filename(post, new_basic, candidate.filename_format)
        add(
            current.post_structure.attachments / old_name,
            current.post_structure.attachments / new_name,
        )
        sequence = max(old_sequence, new_sequence)

    revision_root = source_work / current.post_structure.revisions
    if revision_root.is_dir() and not revision_root.is_symlink():
        for metadata in revision_root.rglob(DataStorageNameEnum.PostData.value):
            revision_source = metadata.parent
            if revision_source.parent != revision_root:
                continue
            try:
                revision = Post.model_validate_json(metadata.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            add(
                current.post_structure.revisions / revision_source.name,
                current.post_structure.revisions / generate_revision_path_name(revision, candidate),
            )

    add(current.post_structure.attachments, candidate.post_structure.attachments)
    add(current.post_structure.content, candidate.post_structure.content)
    add(current.post_structure.external_links, candidate.post_structure.external_links)
    add(current.post_structure.revisions, candidate.post_structure.revisions)
    return moves, conflicts


def _attachment_basic_name(
    path: Path,
    naming: ProjectNamingConfiguration,
    sequence: int,
) -> tuple[str, int]:
    if naming.sequential_filename and path.suffix.lower() not in naming.sequential_filename_excludes:
        return f"{sequence}{path.suffix}", sequence + 1
    return path.name, sequence


def _creator_name(
    dirname: str,
    service: str,
    creator_id: str,
    naming: ProjectNamingConfiguration,
) -> str:
    match = _match_creator_template(
        dirname,
        naming.creator_dirname_format,
        {"service": service, "creator_id": creator_id},
        {"creator_name"},
    )
    if match is not None and match.groupdict().get("creator_name"):
        return match.group("creator_name").strip() or creator_id
    suffix = re.compile(rf"\s*\[{re.escape(service)}-{re.escape(creator_id)}\]\s*$", re.IGNORECASE)
    name = suffix.sub("", dirname).strip()
    return name or creator_id


def _creator_identity_from_template(
    dirname: str,
    template: str,
) -> tuple[str, str, str] | None:
    match = _match_creator_template(
        dirname,
        template,
        {},
        {"creator_name", "service", "creator_id"},
    )
    if match is None:
        return None
    values = match.groupdict()
    service = values.get("service")
    creator_id = values.get("creator_id")
    if not service or not creator_id:
        return None
    return service, creator_id, values.get("creator_name") or creator_id


def _match_creator_template(
    dirname: str,
    template: str,
    known: dict[str, str],
    captured: set[str],
) -> re.Match[str] | None:
    pattern: list[str] = []
    groups: set[str] = set()
    try:
        parts = Formatter().parse(template)
        for literal, field_name, _format_spec, _conversion in parts:
            pattern.append(re.escape(literal))
            if field_name is None:
                continue
            if field_name in known:
                pattern.append(re.escape(known[field_name]))
            elif field_name not in captured:
                return None
            elif field_name in groups:
                pattern.append(rf"(?P={field_name})")
            else:
                pattern.append(rf"(?P<{field_name}>.+?)")
                groups.add(field_name)
    except ValueError:
        return None
    return re.fullmatch("".join(pattern), dirname, re.IGNORECASE)


def _tree_stats(root: Path) -> tuple[int, int, int]:
    files = 0
    size = 0
    symlinks = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            symlinks += 1
        elif path.is_file():
            files += 1
            try:
                size += path.stat().st_size
            except OSError:
                pass
    return files, size, symlinks


def _filesystem_fingerprint(roots: list[Path]) -> str:
    digest = hashlib.sha256()
    for root in sorted(roots, key=str):
        digest.update(str(root).encode())
        for path in sorted(root.rglob("*"), key=str):
            relative = path.relative_to(root)
            if relative.parts and relative.parts[0] == ".ktoolbox":
                continue
            digest.update(str(relative).encode())
            try:
                stat = path.lstat()
            except OSError:
                digest.update(b"missing")
                continue
            digest.update(str(stat.st_mode).encode())
            digest.update(str(stat.st_size).encode())
            digest.update(str(stat.st_mtime_ns).encode())
    return digest.hexdigest()


def _has_symlink_component(relative: Path, root: Path) -> bool:
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            return True
    return False


def _stored_root(path: Path, project_root: Path) -> Path:
    resolved = path.expanduser().resolve(strict=False)
    try:
        return resolved.relative_to(project_root)
    except ValueError:
        return resolved


def _unique_paths(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        normalized = os.path.normcase(os.path.normpath(str(path.expanduser())))
        if normalized not in seen:
            seen.add(normalized)
            unique.append(path)
    return unique


def _merge_naming_section(
    previous: ProjectNamingConfiguration,
    candidate: ProjectNamingConfiguration,
    section: NamingSection,
) -> ProjectNamingConfiguration:
    merged = previous.model_copy(deep=True)
    if section == "structure":
        for field in (
            "mix_posts",
            "sequential_filename",
            "sequential_filename_excludes",
            "group_by_year",
            "group_by_month",
        ):
            setattr(merged, field, getattr(candidate, field))
        for field in ("attachments", "content", "external_links", "revisions"):
            setattr(
                merged.post_structure,
                field,
                getattr(candidate.post_structure, field),
            )
    else:
        for field in (
            "creator_dirname_format",
            "post_dirname_format",
            "revision_dirname_format",
            "filename_format",
            "year_dirname_format",
            "month_dirname_format",
        ):
            setattr(merged, field, getattr(candidate, field))
        merged.post_structure.file = candidate.post_structure.file
    return ProjectNamingConfiguration.model_validate(merged)


def _normalized_path(path: Path) -> str:
    return os.path.normcase(os.path.normpath(str(path.expanduser().resolve(strict=False))))


def _paths_overlap(left: Path, right: Path) -> bool:
    left_resolved = left.resolve(strict=False)
    right_resolved = right.resolve(strict=False)
    return (
        left_resolved == right_resolved
        or left_resolved in right_resolved.parents
        or right_resolved in left_resolved.parents
    )


def _remove_empty_ancestors(start: Path, roots: list[Path]) -> None:
    current = start.resolve(strict=False)
    resolved_roots = [root.resolve(strict=False) for root in roots]
    matching_roots = [root for root in resolved_roots if root == current or root in current.parents]
    if not matching_roots:
        return
    boundary = max(matching_roots, key=lambda path: len(path.parts))
    while current != boundary:
        if current.is_symlink():
            return
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def _conversion_from_row(row: aiosqlite.Row) -> NamingConversionResponse:
    return NamingConversionResponse(
        id=row["id"],
        status=row["status"],
        preview=NamingPreviewResponse.model_validate_json(row["preview_json"]),
        selected_creators=json.loads(row["selected_json"]),
        progress=NamingConversionProgress.model_validate_json(row["progress_json"]),
        error=row["error"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _canonical_naming_json(naming: ProjectNamingConfiguration) -> str:
    return json.dumps(
        naming.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _naming_revision(naming: ProjectNamingConfiguration) -> str:
    return hashlib.sha256(_canonical_naming_json(naming).encode("utf-8")).hexdigest()


def _legacy_migration_response(
    preview: LegacyNamingPreview,
) -> LegacyNamingMigrationResponse:
    return LegacyNamingMigrationResponse(
        pending=preview.pending,
        project_revision=preview.project_revision,
        sources=[
            LegacyNamingSourceResponse(
                name=source.path.name,
                path=source.path,
                revision=source.revision,
                keys=list(source.keys),
            )
            for source in preview.sources
        ],
        fields=[
            LegacyNamingFieldResponse(
                path=field.path,
                env_key=field.env_key,
                legacy_value=field.legacy_value,
                current_value=field.current_value,
                sources=list(field.sources),
            )
            for field in preview.fields
        ],
        ignored_environment_keys=list(preview.ignored_environment_keys),
    )


def _legacy_migration_result_response(
    result: LegacyNamingApplyResult,
) -> LegacyNamingMigrationResultResponse:
    return LegacyNamingMigrationResultResponse(
        migrated=result.migrated,
        backup_paths=list(result.backup_paths),
        naming=result.naming,
        project_revision=result.project_revision,
        ignored_environment_keys=list(result.ignored_environment_keys),
    )


def _notice_from_row(row: aiosqlite.Row) -> StartupNoticeResponse:
    return StartupNoticeResponse(
        id=row["id"],
        kind=row["kind"],
        payload=json.loads(row["payload_json"]),
        created_at=row["created_at"],
        acknowledged_at=row["acknowledged_at"],
        resolution=row["resolution"],
        resolved_at=row["resolved_at"],
    )
