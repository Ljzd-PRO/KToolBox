from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import aiosqlite

from ktoolbox.project_config import AutomaticSyncPlan
from ktoolbox.webui.auto_sync_models import (
    ACTIVE_AUTOMATIC_RUN_STATUSES,
    AutomaticSyncRunRecord,
    AutomaticSyncRunStatus,
    AutomaticSyncRunTrigger,
    AutomaticSyncUpdateSummary,
)
from ktoolbox.webui.database import WebUIDatabase, utc_now
from ktoolbox.webui.event_store import WebUIEventStore
from ktoolbox.webui.task_models import TaskExecutionResult, TaskRecord, TaskStatus


class AutomaticSyncRunNotFoundError(LookupError):
    pass


class AutomaticSyncStore:
    """Persist automatic runs, per-creator checkpoints, and project-wide work observations."""

    def __init__(self, database: WebUIDatabase, event_store: WebUIEventStore) -> None:
        self.database = database
        self.event_store = event_store

    async def create_run(
        self,
        plan: AutomaticSyncPlan,
        trigger: AutomaticSyncRunTrigger,
        cutoff_at: datetime,
        *,
        scheduled_for: datetime | None = None,
    ) -> AutomaticSyncRunRecord:
        run_id = uuid4().hex
        now = utc_now()
        async with self.database.connect() as connection:
            await connection.execute(
                """
                INSERT INTO automatic_sync_runs(
                    id, plan_id, plan_name, trigger, status, scheduled_for,
                    cutoff_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    plan.id,
                    plan.name,
                    trigger.value,
                    AutomaticSyncRunStatus.queued.value,
                    scheduled_for.isoformat() if scheduled_for is not None else None,
                    cutoff_at.isoformat(),
                    now.isoformat(),
                ),
            )
            await connection.commit()
        await self._publish(
            "auto_sync.run.created",
            plan.id,
            {"run_id": run_id, "trigger": trigger.value},
        )
        return await self.get_run(run_id)

    async def attach_task(self, run_id: str, task_id: str) -> AutomaticSyncRunRecord:
        async with self.database.connect() as connection:
            cursor = await connection.execute(
                "UPDATE automatic_sync_runs SET task_id = ? WHERE id = ?",
                (task_id, run_id),
            )
            await connection.commit()
            if cursor.rowcount == 0:
                raise AutomaticSyncRunNotFoundError(run_id)
        return await self.get_run(run_id)

    async def mark_skipped(
        self,
        plan: AutomaticSyncPlan,
        cutoff_at: datetime,
        *,
        scheduled_for: datetime,
        reason: str,
    ) -> AutomaticSyncRunRecord:
        record = await self.create_run(
            plan,
            AutomaticSyncRunTrigger.scheduled,
            cutoff_at,
            scheduled_for=scheduled_for,
        )
        await self._set_run_status(record.id, AutomaticSyncRunStatus.skipped, error=reason)
        await self._publish(
            "auto_sync.run.skipped",
            plan.id,
            {"run_id": record.id, "reason": reason},
        )
        return await self.get_run(record.id)

    async def mark_failed(self, run_id: str, error: str) -> AutomaticSyncRunRecord:
        await self._set_run_status(run_id, AutomaticSyncRunStatus.failed, error=error)
        run = await self.get_run(run_id)
        await self._publish(
            "auto_sync.run.finished",
            run.plan_id,
            {"run_id": run.id, "status": run.status.value},
        )
        return run

    async def active_run(self, plan_id: str) -> AutomaticSyncRunRecord | None:
        placeholders = ",".join("?" for _ in ACTIVE_AUTOMATIC_RUN_STATUSES)
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                f"""
                SELECT *
                FROM automatic_sync_runs
                WHERE plan_id = ? AND status IN ({placeholders})
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (plan_id, *(status.value for status in ACTIVE_AUTOMATIC_RUN_STATUSES)),
            )
            row = await cursor.fetchone()
            await cursor.close()
        return _run_from_row(row) if row is not None else None

    async def get_run(self, run_id: str) -> AutomaticSyncRunRecord:
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                "SELECT * FROM automatic_sync_runs WHERE id = ?",
                (run_id,),
            )
            row = await cursor.fetchone()
            await cursor.close()
        if row is None:
            raise AutomaticSyncRunNotFoundError(run_id)
        return _run_from_row(row)

    async def list_runs(self, *, limit: int = 100) -> list[AutomaticSyncRunRecord]:
        bounded_limit = max(1, min(limit, 200))
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                "SELECT * FROM automatic_sync_runs ORDER BY created_at DESC LIMIT ?",
                (bounded_limit,),
            )
            rows = await cursor.fetchall()
            await cursor.close()
        return [_run_from_row(row) for row in rows]

    async def checkpoint(self, plan_id: str, creator_key: str) -> datetime | None:
        async with self.database.connect() as connection:
            cursor = await connection.execute(
                """
                SELECT checkpoint_at
                FROM automatic_sync_checkpoints
                WHERE plan_id = ? AND creator_key = ?
                """,
                (plan_id, creator_key),
            )
            row = await cursor.fetchone()
            await cursor.close()
        return datetime.fromisoformat(row[0]) if row is not None else None

    async def reconcile_task(
        self,
        task: TaskRecord,
        *,
        result: TaskExecutionResult | None,
    ) -> AutomaticSyncRunRecord | None:
        origin = task.automatic_origin
        if origin is None:
            return None
        run = await self.get_run(origin.run_id)
        if task.status in {TaskStatus.queued, TaskStatus.blocked}:
            if run.status is AutomaticSyncRunStatus.paused:
                await self._set_run_status(run.id, AutomaticSyncRunStatus.queued)
                return await self.get_run(run.id)
            return run
        if task.status in {TaskStatus.running, TaskStatus.pause_requested, TaskStatus.stop_requested}:
            if run.status in {AutomaticSyncRunStatus.queued, AutomaticSyncRunStatus.paused}:
                await self._set_run_status(run.id, AutomaticSyncRunStatus.running)
                await self._publish("auto_sync.run.started", run.plan_id, {"run_id": run.id, "task_id": task.id})
            return await self.get_run(run.id)
        if run.status not in ACTIVE_AUTOMATIC_RUN_STATUSES:
            return run

        if task.status is TaskStatus.paused:
            await self._set_run_status(run.id, AutomaticSyncRunStatus.paused)
            return await self.get_run(run.id)

        mapped_status = {
            TaskStatus.completed: AutomaticSyncRunStatus.completed,
            TaskStatus.failed: AutomaticSyncRunStatus.failed,
            TaskStatus.interrupted: AutomaticSyncRunStatus.interrupted,
            TaskStatus.stopped: AutomaticSyncRunStatus.interrupted,
        }[task.status]
        if result is not None:
            await self._persist_successful_creators(run, task, result)
        await self._set_run_status(run.id, mapped_status, error=task.error)
        await self._publish(
            "auto_sync.run.finished",
            run.plan_id,
            {"run_id": run.id, "task_id": task.id, "status": mapped_status.value},
        )
        return await self.get_run(run.id)

    async def recent_updates(self, *, since: datetime | None) -> list[AutomaticSyncUpdateSummary]:
        where = "WHERE observed.is_baseline = 0"
        values: list[object] = []
        if since is not None:
            where += " AND observed.first_seen_at >= ?"
            values.append(since.isoformat())
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                f"""
                SELECT
                    observed.service,
                    observed.creator_id,
                    profiles.name AS creator_name,
                    COUNT(*) AS new_posts,
                    MAX(observed.first_seen_at) AS last_discovered_at
                FROM automatic_sync_observed_posts AS observed
                LEFT JOIN creator_profile_cache AS profiles
                    ON profiles.service = observed.service
                    AND profiles.creator_id = observed.creator_id
                {where}
                GROUP BY observed.service, observed.creator_id, profiles.name
                ORDER BY last_discovered_at DESC, observed.service, observed.creator_id
                """,
                values,
            )
            rows = await cursor.fetchall()
            await cursor.close()
        return [
            AutomaticSyncUpdateSummary(
                service=row["service"],
                creator_id=row["creator_id"],
                creator_name=row["creator_name"],
                new_posts=row["new_posts"],
                last_discovered_at=row["last_discovered_at"],
            )
            for row in rows
        ]

    async def delete_plan_state(self, plan_id: str) -> None:
        async with self.database.connect() as connection:
            await connection.execute(
                "DELETE FROM automatic_sync_checkpoints WHERE plan_id = ?",
                (plan_id,),
            )
            await connection.commit()

    async def _persist_successful_creators(
        self,
        run: AutomaticSyncRunRecord,
        task: TaskRecord,
        result: TaskExecutionResult,
    ) -> None:
        origin = task.automatic_origin
        if origin is None:
            return
        windows = {window.creator_key.casefold(): window for window in origin.windows}
        now = utc_now().isoformat()
        async with self.database.connect() as connection:
            for creator in result.creators:
                if not creator.successful:
                    continue
                window = windows.get(creator.creator_key.casefold())
                if window is None:
                    continue
                await connection.execute(
                    """
                    INSERT INTO automatic_sync_checkpoints(plan_id, creator_key, checkpoint_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(plan_id, creator_key) DO UPDATE SET
                        checkpoint_at = excluded.checkpoint_at,
                        updated_at = excluded.updated_at
                    """,
                    (run.plan_id, creator.creator_key, window.end_at.isoformat(), now),
                )
                service, separator, creator_id = creator.creator_key.partition(":")
                if not separator:
                    continue
                for post_id in dict.fromkeys(creator.accepted_post_ids):
                    await connection.execute(
                        """
                        INSERT OR IGNORE INTO automatic_sync_observed_posts(
                            service, creator_id, post_id, first_seen_at,
                            plan_id, run_id, is_baseline
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            service,
                            creator_id,
                            post_id,
                            window.end_at.isoformat(),
                            run.plan_id,
                            run.id,
                            int(window.baseline),
                        ),
                    )
            await connection.commit()
        await self._publish("auto_sync.updates.changed", run.plan_id, {"run_id": run.id})

    async def _set_run_status(
        self,
        run_id: str,
        status: AutomaticSyncRunStatus,
        *,
        error: str | None = None,
    ) -> None:
        now = utc_now().isoformat()
        started_at = now if status is AutomaticSyncRunStatus.running else None
        finished_at = (
            now
            if status
            in {
                AutomaticSyncRunStatus.completed,
                AutomaticSyncRunStatus.failed,
                AutomaticSyncRunStatus.skipped,
                AutomaticSyncRunStatus.interrupted,
            }
            else None
        )
        async with self.database.connect() as connection:
            cursor = await connection.execute(
                """
                UPDATE automatic_sync_runs
                SET status = ?,
                    started_at = COALESCE(started_at, ?),
                    finished_at = COALESCE(?, finished_at),
                    error = ?
                WHERE id = ?
                """,
                (status.value, started_at, finished_at, error, run_id),
            )
            await connection.commit()
            if cursor.rowcount == 0:
                raise AutomaticSyncRunNotFoundError(run_id)

    async def _publish(self, event_type: str, plan_id: str, data: dict[str, object]) -> None:
        await self.event_store.publish(
            event_type,
            data,
            resource="auto_sync",
            resource_id=plan_id,
        )


def update_range_days(value: str) -> timedelta | None:
    return {
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90),
        "all": None,
    }[value]


def _run_from_row(row: aiosqlite.Row) -> AutomaticSyncRunRecord:
    return AutomaticSyncRunRecord(
        id=row["id"],
        plan_id=row["plan_id"],
        plan_name=row["plan_name"],
        trigger=row["trigger"],
        status=row["status"],
        task_id=row["task_id"],
        scheduled_for=row["scheduled_for"],
        cutoff_at=row["cutoff_at"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        error=row["error"],
    )
