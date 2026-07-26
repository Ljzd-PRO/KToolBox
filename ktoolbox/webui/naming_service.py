from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import aiosqlite
import anyio
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
from ktoolbox.naming_migration import MIGRATION_NOTICE_PATH
from ktoolbox.project_config import (
    ProjectConfigStore,
    ProjectNamingConfiguration,
)
from ktoolbox.webui.config_store import content_revision
from ktoolbox.webui.database import WebUIDatabase, utc_now
from ktoolbox.webui.event_store import WebUIEventStore
from ktoolbox.webui.naming_models import (
    NamingConversionProgress,
    NamingConversionResponse,
    NamingCreatorPreview,
    NamingPreviewResponse,
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

    async def start(self) -> None:
        await self._import_startup_notice()
        await self._recover_incomplete()

    async def stop(self) -> None:
        for cancellation in self._cancellations.values():
            cancellation.set()
        if self._workers:
            await asyncio.gather(*self._workers.values(), return_exceptions=True)
        self._workers.clear()
        self._cancellations.clear()

    async def suggested_download_roots(self) -> list[Path]:
        project = self.project_store.load()
        roots = list(project.naming.download_roots)
        seen = {_normalized_path(self._resolve_root(root)) for root in roots}
        for task in await self.tasks.list_tasks():
            resolved = task.spec.output.expanduser()
            if not resolved.is_absolute():
                resolved = self.project_root / resolved
            normalized = _normalized_path(resolved)
            if normalized not in seen:
                seen.add(normalized)
                roots.append(_stored_root(resolved, self.project_root))
        return roots

    async def preview(self, candidate: ProjectNamingConfiguration) -> NamingPreviewResponse:
        current = self.project_store.load()
        revision = content_revision(self.project_store.load_text())
        roots = [self._resolve_root(root) for root in candidate.download_roots]
        if not roots:
            raise NamingConversionError("add at least one download root before scanning")
        for root in roots:
            if not root.is_dir():
                raise NamingConversionError(f"download root is not a directory: {root}")
            if root.is_symlink():
                raise NamingConversionError(f"download root cannot be a symbolic link: {root}")

        fingerprint = await anyio.to_thread.run_sync(_filesystem_fingerprint, roots)
        scans = await anyio.to_thread.run_sync(
            _scan_download_roots,
            roots,
            current.naming,
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
            roots=roots,
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
        *,
        convert_existing: bool,
    ) -> NamingConversionResponse:
        conversion = await self.get(preview_id)
        if conversion.status != "preview":
            raise NamingConversionError("this preview has already been applied")
        await self._ensure_preview_current(conversion.preview)
        selected = selected_creators
        allowed = {creator.key for creator in conversion.preview.creators if creator.selectable}
        if unknown := sorted(set(selected) - allowed):
            raise NamingConversionError("selected creators are unavailable: " + ", ".join(unknown))
        if conversion.preview.conflict_count:
            raise NamingConversionError("resolve every target path conflict before applying this preview")

        candidate = ProjectNamingConfiguration.model_validate_json(
            await self._candidate_json(preview_id)
        )
        if not convert_existing:
            configuration = self.project_store.load()
            configuration.naming = candidate
            self.project_store.save(configuration)
            await self._set_status(preview_id, "completed", selected=[])
            await self.events.publish(
                "naming.changed",
                {"conversion_id": preview_id, "converted": False},
                resource="naming",
                resource_id=preview_id,
            )
            return await self.get(preview_id)

        if not selected:
            raise NamingConversionError("select at least one downloaded creator to convert")
        await self._ensure_no_overlapping_tasks(conversion.preview.roots)
        await self._set_status(preview_id, "queued", selected=selected)
        cancellation = asyncio.Event()
        self._cancellations[preview_id] = cancellation
        worker = asyncio.create_task(
            self._run_conversion(preview_id, candidate, selected, cancellation),
            name=f"naming-conversion-{preview_id}",
        )
        self._workers[preview_id] = worker
        worker.add_done_callback(lambda _: self._workers.pop(preview_id, None))
        return await self.get(preview_id)

    async def cancel(self, conversion_id: str) -> NamingConversionResponse:
        conversion = await self.get(conversion_id)
        if conversion.status not in {"queued", "running"}:
            raise NamingConversionError("only queued or running conversions can be cancelled")
        cancellation = self._cancellations.get(conversion_id)
        if cancellation is None:
            raise NamingConversionError("conversion worker is not active")
        cancellation.set()
        return await self.get(conversion_id)

    async def list_conversions(self) -> list[NamingConversionResponse]:
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            rows = await connection.execute_fetchall(
                "SELECT * FROM naming_conversions ORDER BY created_at DESC"
            )
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
        if conversion.status in {"queued", "running", "rolling_back"}:
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
            cursor = await connection.execute(
                """
                UPDATE startup_notices SET acknowledged_at = ?
                WHERE id = ? AND acknowledged_at IS NULL
                """,
                (now.isoformat(), notice_id),
            )
            await connection.commit()
            if cursor.rowcount == 0:
                raise LookupError(notice_id)
            connection.row_factory = aiosqlite.Row
            row = await (
                await connection.execute(
                    "SELECT * FROM startup_notices WHERE id = ?",
                    (notice_id,),
                )
            ).fetchone()
        if row is None:
            raise LookupError(notice_id)
        return _notice_from_row(row)

    async def _run_conversion(
        self,
        conversion_id: str,
        candidate: ProjectNamingConfiguration,
        selected: list[str],
        cancellation: asyncio.Event,
    ) -> None:
        try:
            await self._set_status(conversion_id, "running", selected=selected)
            operations = await self._operations(conversion_id, selected, reverse=False)
            progress = NamingConversionProgress(total_operations=len(operations))
            await self._set_progress(conversion_id, progress)
            for operation in operations:
                if cancellation.is_set():
                    raise asyncio.CancelledError
                source = Path(operation["source"])
                target = Path(operation["target"])
                if not await anyio.to_thread.run_sync(source.exists):
                    raise NamingConversionError(f"source changed since preview: {source}")
                if await anyio.to_thread.run_sync(target.exists):
                    raise NamingConversionError(f"target now exists: {target}")
                await anyio.to_thread.run_sync(target.parent.mkdir, 0o777, True, True)
                await anyio.to_thread.run_sync(os.replace, source, target)
                await self._mark_operation(int(operation["id"]), "completed")
                progress.completed_operations += 1
                progress.current_creator = str(operation["creator_key"])
                await self._set_progress(conversion_id, progress)
            conversion = await self.get(conversion_id)
            if content_revision(self.project_store.load_text()) != conversion.preview.revision:
                raise NamingPreviewStaleError(
                    "project configuration changed during conversion; moved files will be rolled back"
                )
            configuration = self.project_store.load()
            configuration.naming = candidate
            await anyio.to_thread.run_sync(self.project_store.save, configuration)
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
            self._cancellations.pop(conversion_id, None)

    async def _rollback(
        self,
        conversion_id: str,
        final_status: str,
        *,
        error: str | None = None,
    ) -> None:
        await self._set_status(conversion_id, "rolling_back", error=error)
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

    async def _recover_incomplete(self) -> None:
        async with self.database.connect() as connection:
            rows = await connection.execute_fetchall(
                """
                SELECT id FROM naming_conversions
                WHERE status IN ('queued', 'running', 'rolling_back')
                """
            )
        for (conversion_id,) in rows:
            await self._rollback(
                str(conversion_id),
                "failed",
                error="WebUI stopped during naming conversion; completed moves were rolled back",
            )

    async def _import_startup_notice(self) -> None:
        path = self.project_root / MIGRATION_NOTICE_PATH
        if not path.is_file():
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        now = utc_now().isoformat()
        async with self.database.connect() as connection:
            await connection.execute(
                """
                INSERT OR IGNORE INTO startup_notices(id, kind, payload_json, created_at)
                VALUES (?, 'naming_migrated', ?, ?)
                """,
                (str(payload.get("id", "project-naming-v2")), json.dumps(payload), now),
            )
            await connection.commit()
        path.unlink(missing_ok=True)


def _scan_download_roots(
    roots: list[Path],
    current: ProjectNamingConfiguration,
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

        _add_indexed_works(root, current, grouped, skipped_by_creator)
        grouped_creators = {creator for _, _, creator in grouped}
        for (service, creator_id, source_creator), works in grouped.items():
            name = _creator_name(source_creator.name, service, creator_id)
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
                target_work = (
                    generate_grouped_post_path(post, target_creator, candidate)
                    / generate_post_path_name(post, candidate)
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
            parsed_identity = _creator_identity_from_directory(source_creator)
            if parsed_identity is None:
                continue
            service, creator_id, name = parsed_identity
            selection_key = (
                f"{service}:{creator_id}@"
                f"{hashlib.sha1(str(source_creator).encode()).hexdigest()[:10]}"
            )
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
    current: ProjectNamingConfiguration,
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
        if current.mix_posts:
            continue
        for post in index.posts.values():
            key = (index.service, index.creator_id, creator, post.id)
            if key in known_posts:
                continue
            source_work = (
                generate_grouped_post_path(post, creator, current)
                / generate_post_path_name(post, current)
            )
            if source_work.is_dir() and not source_work.is_symlink():
                grouped.setdefault(
                    (index.service, index.creator_id, creator),
                    [],
                ).append((source_work, post))
                known_posts.add(key)
            else:
                skipped_by_creator[creator] = skipped_by_creator.get(creator, 0) + 1


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


def _creator_identity_from_directory(path: Path) -> tuple[str, str, str] | None:
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
                _creator_name(path.name, index.service, index.creator_id),
            )
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
            move.target
            for move in duplicate_scans[0].moves
            if _normalized_path(move.target) == normalized_target
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


def _creator_name(dirname: str, service: str, creator_id: str) -> str:
    suffix = re.compile(rf"\s*\[{re.escape(service)}-{re.escape(creator_id)}\]\s*$", re.IGNORECASE)
    name = suffix.sub("", dirname).strip()
    return name or creator_id


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


def _notice_from_row(row: aiosqlite.Row) -> StartupNoticeResponse:
    return StartupNoticeResponse(
        id=row["id"],
        kind=row["kind"],
        payload=json.loads(row["payload_json"]),
        created_at=row["created_at"],
        acknowledged_at=row["acknowledged_at"],
    )
