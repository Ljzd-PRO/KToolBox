from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiosqlite


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class WebUISession:
    username: str
    csrf_token: str
    created_at: datetime
    last_seen_at: datetime


class WebUIDatabase:
    """Small project-local SQLite store shared by sessions and tasks."""

    def __init__(self, path: Path) -> None:
        self.path = path

    async def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        async with self._connect() as connection:
            await connection.execute("PRAGMA journal_mode=WAL")
            await connection.execute("PRAGMA foreign_keys=ON")
            await connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    csrf_token TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    spec_json TEXT NOT NULL,
                    presentation_json TEXT,
                    position INTEGER NOT NULL,
                    revision INTEGER NOT NULL DEFAULT 1,
                    progress_json TEXT NOT NULL DEFAULT '{}',
                    error TEXT,
                    blocked_by TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS task_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                    sequence INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    spec_json TEXT NOT NULL,
                    configuration_json TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    error TEXT,
                    UNIQUE(task_id, sequence)
                );

                CREATE TABLE IF NOT EXISTS task_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT REFERENCES tasks(id) ON DELETE CASCADE,
                    event_type TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS task_artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                    path TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    mtime_ns INTEGER NOT NULL,
                    UNIQUE(task_id, path)
                );

                CREATE TABLE IF NOT EXISTS creator_profile_cache (
                    service TEXT NOT NULL COLLATE NOCASE,
                    creator_id TEXT NOT NULL COLLATE NOCASE,
                    name TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    PRIMARY KEY(service, creator_id)
                );

                CREATE INDEX IF NOT EXISTS task_events_cursor ON task_events(id);
                CREATE INDEX IF NOT EXISTS tasks_queue ON tasks(status, position);
                """
            )
            await connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (1, utc_now().isoformat()),
            )
            await connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (2, utc_now().isoformat()),
            )
            await _ensure_column(connection, "tasks", "presentation_json", "TEXT")
            await connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (3, utc_now().isoformat()),
            )
            await connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (4, utc_now().isoformat()),
            )
            await connection.commit()

    async def create_session(self, token: str, username: str, csrf_token: str) -> WebUISession:
        now = utc_now()
        async with self._connect() as connection:
            await connection.execute(
                """
                INSERT INTO sessions(token_hash, username, csrf_token, created_at, last_seen_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (token_digest(token), username, csrf_token, now.isoformat(), now.isoformat()),
            )
            await connection.commit()
        return WebUISession(username, csrf_token, now, now)

    async def get_session(
        self,
        token: str,
        *,
        idle_lifetime: timedelta,
        absolute_lifetime: timedelta,
    ) -> WebUISession | None:
        now = utc_now()
        digest = token_digest(token)
        async with self._connect() as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                "SELECT username, csrf_token, created_at, last_seen_at FROM sessions WHERE token_hash = ?",
                (digest,),
            )
            row = await cursor.fetchone()
            await cursor.close()
            if row is None:
                return None
            created_at = datetime.fromisoformat(row["created_at"])
            last_seen_at = datetime.fromisoformat(row["last_seen_at"])
            if now - last_seen_at > idle_lifetime or now - created_at > absolute_lifetime:
                await connection.execute("DELETE FROM sessions WHERE token_hash = ?", (digest,))
                await connection.commit()
                return None
            await connection.execute(
                "UPDATE sessions SET last_seen_at = ? WHERE token_hash = ?",
                (now.isoformat(), digest),
            )
            await connection.commit()
        return WebUISession(row["username"], row["csrf_token"], created_at, now)

    async def delete_session(self, token: str) -> None:
        async with self._connect() as connection:
            await connection.execute("DELETE FROM sessions WHERE token_hash = ?", (token_digest(token),))
            await connection.commit()

    async def delete_all_sessions(self) -> None:
        async with self._connect() as connection:
            await connection.execute("DELETE FROM sessions")
            await connection.commit()

    def _connect(self) -> aiosqlite.Connection:
        return aiosqlite.connect(self.path)

    def connect(self) -> aiosqlite.Connection:
        return self._connect()


async def _ensure_column(
    connection: aiosqlite.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    cursor = await connection.execute(f"PRAGMA table_info({table})")
    rows = await cursor.fetchall()
    await cursor.close()
    if column not in {str(row[1]) for row in rows}:
        await connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
