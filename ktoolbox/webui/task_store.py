from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import aiosqlite
import anyio

from ktoolbox.webui.database import WebUIDatabase, utc_now
from ktoolbox.webui.task_models import (
    ACTIVE_TASK_STATUSES,
    RUNNING_TASK_STATUSES,
    TASK_SPEC_ADAPTER,
    TaskArtifact,
    TaskAttempt,
    TaskCleanupPreview,
    TaskEvent,
    TaskPresentationSnapshot,
    TaskProgress,
    TaskRecord,
    TaskSpec,
    TaskStatus,
)


class TaskNotFoundError(LookupError):
    pass


class DuplicateTaskError(ValueError):
    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"an equivalent active task already exists: {task_id}")


class InvalidTaskStateError(ValueError):
    pass


class TaskStore:
    def __init__(self, database: WebUIDatabase) -> None:
        self.database = database

    async def recover_interrupted(self) -> int:
        now = utc_now().isoformat()
        placeholders = ",".join("?" for _ in RUNNING_TASK_STATUSES)
        values = [status.value for status in RUNNING_TASK_STATUSES]
        async with self.database.connect() as connection:
            cursor = await connection.execute(
                f"UPDATE tasks SET status = ?, error = ?, updated_at = ? WHERE status IN ({placeholders})",
                [TaskStatus.interrupted.value, "WebUI stopped while this task was running", now, *values],
            )
            await connection.execute(
                f"""
                UPDATE task_attempts
                SET status = ?, error = ?, finished_at = ?
                WHERE finished_at IS NULL AND status IN ({placeholders})
                """,
                [TaskStatus.interrupted.value, "WebUI stopped while this task was running", now, *values],
            )
            await connection.commit()
            return cursor.rowcount

    async def create(
        self,
        spec: TaskSpec,
        presentation: TaskPresentationSnapshot | None = None,
    ) -> TaskRecord:
        spec_json = _spec_json(spec)
        duplicate = await self.find_duplicate(spec_json)
        if duplicate is not None:
            raise DuplicateTaskError(duplicate)
        task_id = uuid4().hex
        now = utc_now().isoformat()
        async with self.database.connect() as connection:
            cursor = await connection.execute("SELECT COALESCE(MAX(position), 0) + 1 FROM tasks")
            row = await cursor.fetchone()
            await cursor.close()
            if row is None:
                raise RuntimeError("failed to determine queue position")
            position = int(row[0])
            await connection.execute(
                """
                INSERT INTO tasks(
                    id, kind, status, spec_json, presentation_json, position, progress_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    spec.kind,
                    TaskStatus.queued.value,
                    spec_json,
                    _presentation_json(presentation),
                    position,
                    TaskProgress().model_dump_json(),
                    now,
                    now,
                ),
            )
            await connection.commit()
        await self.add_event(task_id, "task.created", {"status": TaskStatus.queued.value})
        return await self.get(task_id)

    async def find_duplicate(self, spec_json: str) -> str | None:
        placeholders = ",".join("?" for _ in ACTIVE_TASK_STATUSES)
        async with self.database.connect() as connection:
            cursor = await connection.execute(
                f"SELECT id FROM tasks WHERE spec_json = ? AND status IN ({placeholders}) LIMIT 1",
                [spec_json, *(status.value for status in ACTIVE_TASK_STATUSES)],
            )
            row = await cursor.fetchone()
            await cursor.close()
        return str(row[0]) if row is not None else None

    async def list_tasks(self) -> list[TaskRecord]:
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute("SELECT * FROM tasks ORDER BY position, created_at")
            rows = await cursor.fetchall()
            await cursor.close()
        return [_task_from_row(row) for row in rows]

    async def get(self, task_id: str) -> TaskRecord:
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = await cursor.fetchone()
            await cursor.close()
        if row is None:
            raise TaskNotFoundError(task_id)
        return _task_from_row(row)

    async def set_status(
        self,
        task_id: str,
        status: TaskStatus,
        *,
        error: str | None = None,
        blocked_by: str | None = None,
    ) -> TaskRecord:
        now = utc_now().isoformat()
        async with self.database.connect() as connection:
            cursor = await connection.execute(
                """
                UPDATE tasks
                SET status = ?, error = ?, blocked_by = ?, updated_at = ?
                WHERE id = ?
                """,
                (status.value, error, blocked_by, now, task_id),
            )
            await connection.commit()
            if cursor.rowcount == 0:
                raise TaskNotFoundError(task_id)
        await self.add_event(
            task_id,
            "task.status",
            {"status": status.value, "error": error, "blocked_by": blocked_by},
        )
        return await self.get(task_id)

    async def update_spec(
        self,
        task_id: str,
        spec: TaskSpec,
        presentation: TaskPresentationSnapshot | None = None,
    ) -> TaskRecord:
        task = await self.get(task_id)
        if task.status in RUNNING_TASK_STATUSES:
            raise InvalidTaskStateError("pause or stop a running task before editing it")
        spec_json = _spec_json(spec)
        duplicate = await self.find_duplicate(spec_json)
        if duplicate is not None and duplicate != task_id:
            raise DuplicateTaskError(duplicate)
        now = utc_now().isoformat()
        async with self.database.connect() as connection:
            await connection.execute(
                """
                UPDATE tasks
                SET kind = ?, spec_json = ?, presentation_json = ?, revision = revision + 1,
                    updated_at = ?, error = NULL, blocked_by = NULL
                WHERE id = ?
                """,
                (spec.kind, spec_json, _presentation_json(presentation), now, task_id),
            )
            await connection.commit()
        await self.add_event(task_id, "task.updated", {"kind": spec.kind})
        return await self.get(task_id)

    async def reorder(self, task_id: str, position: int) -> TaskRecord:
        await self.get(task_id)
        async with self.database.connect() as connection:
            await connection.execute(
                "UPDATE tasks SET position = ?, updated_at = ? WHERE id = ?",
                (position, utc_now().isoformat(), task_id),
            )
            await connection.commit()
        await self.add_event(task_id, "task.reordered", {"position": position})
        return await self.get(task_id)

    async def update_progress(self, task_id: str, progress: TaskProgress) -> None:
        async with self.database.connect() as connection:
            await connection.execute(
                "UPDATE tasks SET progress_json = ?, updated_at = ? WHERE id = ?",
                (progress.model_dump_json(), utc_now().isoformat(), task_id),
            )
            await connection.commit()

    async def queue_again(self, task_id: str) -> TaskRecord:
        now = utc_now().isoformat()
        async with self.database.connect() as connection:
            cursor = await connection.execute(
                """
                UPDATE tasks
                SET status = ?, progress_json = ?, error = NULL, blocked_by = NULL, updated_at = ?
                WHERE id = ?
                """,
                (TaskStatus.queued.value, TaskProgress().model_dump_json(), now, task_id),
            )
            await connection.commit()
            if cursor.rowcount == 0:
                raise TaskNotFoundError(task_id)
        await self.add_event(task_id, "task.status", {"status": TaskStatus.queued.value})
        return await self.get(task_id)

    async def start_attempt(
        self,
        task: TaskRecord,
        configuration: dict[str, object],
    ) -> TaskAttempt:
        now = utc_now().isoformat()
        async with self.database.connect() as connection:
            cursor = await connection.execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 FROM task_attempts WHERE task_id = ?",
                (task.id,),
            )
            row = await cursor.fetchone()
            await cursor.close()
            if row is None:
                raise RuntimeError("failed to determine attempt sequence")
            sequence = int(row[0])
            cursor = await connection.execute(
                """
                INSERT INTO task_attempts(
                    task_id, sequence, status, spec_json, configuration_json, started_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    task.id,
                    sequence,
                    TaskStatus.running.value,
                    _spec_json(task.spec),
                    json.dumps(configuration, ensure_ascii=False, sort_keys=True),
                    now,
                ),
            )
            await connection.commit()
            attempt_id = cursor.lastrowid
        if attempt_id is None:
            raise RuntimeError("failed to create task attempt")
        return TaskAttempt(
            id=attempt_id,
            task_id=task.id,
            sequence=sequence,
            status=TaskStatus.running,
            spec=task.spec,
            configuration=configuration,
            started_at=now,
        )

    async def finish_attempt(self, attempt_id: int, status: TaskStatus, error: str | None = None) -> None:
        async with self.database.connect() as connection:
            await connection.execute(
                """
                UPDATE task_attempts SET status = ?, error = ?, finished_at = ? WHERE id = ?
                """,
                (status.value, error, utc_now().isoformat(), attempt_id),
            )
            await connection.commit()

    async def attempts(self, task_id: str) -> list[TaskAttempt]:
        await self.get(task_id)
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                "SELECT * FROM task_attempts WHERE task_id = ? ORDER BY sequence DESC",
                (task_id,),
            )
            rows = await cursor.fetchall()
            await cursor.close()
        return [_attempt_from_row(row) for row in rows]

    async def add_event(self, task_id: str | None, event_type: str, data: dict[str, object]) -> TaskEvent:
        now = utc_now()
        async with self.database.connect() as connection:
            cursor = await connection.execute(
                "INSERT INTO task_events(task_id, event_type, data_json, created_at) VALUES (?, ?, ?, ?)",
                (task_id, event_type, json.dumps(data, ensure_ascii=False), now.isoformat()),
            )
            await connection.commit()
            event_id = cursor.lastrowid
        if event_id is None:
            raise RuntimeError("failed to persist task event")
        return TaskEvent(id=event_id, task_id=task_id, event_type=event_type, data=data, created_at=now)

    async def events(self, *, after: int = 0, task_id: str | None = None, limit: int = 200) -> list[TaskEvent]:
        query = "SELECT * FROM task_events WHERE id > ?"
        parameters: list[object] = [after]
        if task_id is not None:
            query += " AND task_id = ?"
            parameters.append(task_id)
        query += " ORDER BY id LIMIT ?"
        parameters.append(limit)
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(query, parameters)
            rows = await cursor.fetchall()
            await cursor.close()
        return [_event_from_row(row) for row in rows]

    async def add_artifact(self, task_id: str, path: Path) -> None:
        artifact = await anyio.to_thread.run_sync(_capture_artifact, path)
        if artifact is None:
            return
        async with self.database.connect() as connection:
            await connection.execute(
                """
                INSERT OR REPLACE INTO task_artifacts(task_id, path, size, mtime_ns)
                VALUES (?, ?, ?, ?)
                """,
                (task_id, str(artifact.path), artifact.size, artifact.mtime_ns),
            )
            await connection.commit()

    async def cleanup_preview(self, task_id: str) -> TaskCleanupPreview:
        await self.get(task_id)
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                "SELECT path, size, mtime_ns FROM task_artifacts WHERE task_id = ? ORDER BY path",
                (task_id,),
            )
            rows = await cursor.fetchall()
            await cursor.close()
        artifacts = [_artifact_from_row(row) for row in rows]
        removable = [artifact for artifact in artifacts if artifact.removable]
        return TaskCleanupPreview(
            task_id=task_id,
            artifacts=artifacts,
            removable_files=len(removable),
            removable_bytes=sum(artifact.size for artifact in removable),
        )

    async def delete(self, task_id: str, *, delete_output: bool = False) -> TaskCleanupPreview:
        task = await self.get(task_id)
        if task.status in RUNNING_TASK_STATUSES or task.status in {TaskStatus.queued, TaskStatus.blocked}:
            raise InvalidTaskStateError("stop the task before deleting it")
        preview = await self.cleanup_preview(task_id)
        if delete_output:
            for artifact in preview.artifacts:
                if artifact.removable:
                    await anyio.to_thread.run_sync(_unlink_artifact, artifact.path)
        async with self.database.connect() as connection:
            await connection.execute("PRAGMA foreign_keys=ON")
            await connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            await connection.commit()
        return preview


def _spec_json(spec: TaskSpec) -> str:
    return json.dumps(spec.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _presentation_json(presentation: TaskPresentationSnapshot | None) -> str | None:
    return presentation.model_dump_json() if presentation is not None else None


def _task_from_row(row: aiosqlite.Row) -> TaskRecord:
    return TaskRecord(
        id=row["id"],
        kind=row["kind"],
        status=TaskStatus(row["status"]),
        spec=TASK_SPEC_ADAPTER.validate_json(row["spec_json"]),
        presentation=(
            TaskPresentationSnapshot.model_validate_json(row["presentation_json"])
            if row["presentation_json"] is not None
            else None
        ),
        position=row["position"],
        revision=row["revision"],
        progress=TaskProgress.model_validate_json(row["progress_json"]),
        error=row["error"],
        blocked_by=row["blocked_by"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _attempt_from_row(row: aiosqlite.Row) -> TaskAttempt:
    return TaskAttempt(
        id=row["id"],
        task_id=row["task_id"],
        sequence=row["sequence"],
        status=TaskStatus(row["status"]),
        spec=TASK_SPEC_ADAPTER.validate_json(row["spec_json"]),
        configuration=json.loads(row["configuration_json"]),
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        error=row["error"],
    )


def _event_from_row(row: aiosqlite.Row) -> TaskEvent:
    return TaskEvent(
        id=row["id"],
        task_id=row["task_id"],
        event_type=row["event_type"],
        data=json.loads(row["data_json"]),
        created_at=row["created_at"],
    )


def _artifact_from_row(row: aiosqlite.Row) -> TaskArtifact:
    path = Path(row["path"])
    reason: str | None = None
    try:
        stat = path.lstat()
        if path.is_symlink():
            reason = "symbolic links are never removed"
        elif not path.is_file():
            reason = "file no longer exists"
        elif stat.st_size != row["size"] or stat.st_mtime_ns != row["mtime_ns"]:
            reason = "file changed after the task completed"
    except OSError:
        reason = "file no longer exists"
    return TaskArtifact(
        path=path,
        size=row["size"],
        mtime_ns=row["mtime_ns"],
        removable=reason is None,
        reason=reason,
    )


def _capture_artifact(path: Path) -> TaskArtifact | None:
    try:
        stat = path.lstat()
        if path.is_symlink() or not path.is_file():
            return None
        resolved = path.resolve()
    except OSError:
        return None
    return TaskArtifact(
        path=resolved,
        size=stat.st_size,
        mtime_ns=stat.st_mtime_ns,
        removable=True,
    )


def _unlink_artifact(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass
