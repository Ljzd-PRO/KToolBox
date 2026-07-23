from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping

import aiosqlite

from ktoolbox.webui.database import WebUIDatabase, utc_now
from ktoolbox.webui.task_models import TaskEvent

_REDACTED = "[redacted]"
_SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "password",
    "password_hash",
    "session_key",
    "token",
    "token_hash",
}


class WebUIEventStore:
    """Persist WebUI change events and wake in-process SSE subscribers."""

    def __init__(self, database: WebUIDatabase) -> None:
        self.database = database
        self._condition = asyncio.Condition()
        self._generation = 0

    async def publish(
        self,
        event_type: str,
        data: Mapping[str, object] | None = None,
        *,
        task_id: str | None = None,
        resource: str | None = None,
        resource_id: str | None = None,
    ) -> TaskEvent:
        now = utc_now()
        safe_data = _sanitize_mapping(data or {})
        async with self.database.connect() as connection:
            cursor = await connection.execute(
                """
                INSERT INTO task_events(
                    task_id, event_type, resource, resource_id, data_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    event_type,
                    resource,
                    resource_id,
                    json.dumps(safe_data, ensure_ascii=False),
                    now.isoformat(),
                ),
            )
            await connection.commit()
            event_id = cursor.lastrowid
        if event_id is None:
            raise RuntimeError("failed to persist WebUI event")
        async with self._condition:
            self._generation += 1
            self._condition.notify_all()
        return TaskEvent(
            id=event_id,
            task_id=task_id,
            event_type=event_type,
            resource=resource,
            resource_id=resource_id,
            data=safe_data,
            created_at=now,
        )

    async def latest_id(self) -> int:
        async with self.database.connect() as connection:
            cursor = await connection.execute("SELECT COALESCE(MAX(id), 0) FROM task_events")
            row = await cursor.fetchone()
            await cursor.close()
        return int(row[0]) if row is not None else 0

    async def events(
        self,
        *,
        after: int = 0,
        task_id: str | None = None,
        limit: int = 200,
    ) -> list[TaskEvent]:
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

    async def wait_for_events(
        self,
        *,
        after: int,
        task_id: str | None = None,
        limit: int = 200,
        timeout: float = 15.0,
    ) -> list[TaskEvent]:
        generation = self._generation
        records = await self.events(after=after, task_id=task_id, limit=limit)
        if records:
            return records
        async with self._condition:
            try:
                await asyncio.wait_for(
                    self._condition.wait_for(lambda: self._generation != generation),
                    timeout=timeout,
                )
            except TimeoutError:
                return []
        return await self.events(after=after, task_id=task_id, limit=limit)


def _event_from_row(row: aiosqlite.Row) -> TaskEvent:
    keys = set(row.keys())
    return TaskEvent(
        id=row["id"],
        task_id=row["task_id"],
        event_type=row["event_type"],
        resource=row["resource"] if "resource" in keys else None,
        resource_id=row["resource_id"] if "resource_id" in keys else None,
        data=json.loads(row["data_json"]),
        created_at=row["created_at"],
    )


def _sanitize_mapping(value: Mapping[str, object]) -> dict[str, object]:
    return {str(key): _sanitize_value(str(key), item) for key, item in value.items()}


def _sanitize_value(key: str, value: object) -> object:
    if key.casefold() in _SENSITIVE_KEYS:
        return _REDACTED
    if isinstance(value, Mapping):
        return _sanitize_mapping(value)
    if isinstance(value, list):
        return [_sanitize_value("", item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_value("", item) for item in value]
    return value
