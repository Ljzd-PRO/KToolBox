from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import Literal

from loguru import logger

_MAX_AGE = 7 * 24 * 60 * 60
_Action = Literal["lookup", "record", "clear"]


class MissingFileHistory:
    """Project-local, best-effort history for ordinary CLI sync downloads."""

    def __init__(self, database: Path, *, skip: bool) -> None:
        self._database = database
        self._skip = skip
        self._unavailable = False
        self._started_at = time.time()

    @staticmethod
    def key(url: str, session_key: str) -> str:
        identity = json.dumps([url, session_key], ensure_ascii=True, separators=(",", ":"))
        return hashlib.sha256(identity.encode("ascii")).hexdigest()

    async def should_skip(self, key: str) -> bool:
        return self._skip and await self._apply("lookup", key)

    async def record(self, key: str) -> None:
        await self._apply("record", key)

    async def clear(self, key: str) -> None:
        await self._apply("clear", key)

    async def _apply(self, action: _Action, key: str) -> bool:
        if not self._unavailable:
            try:
                return await asyncio.to_thread(self._query, action, key, time.time())
            except (OSError, sqlite3.Error):
                if not self._unavailable:
                    self._unavailable = True
                    logger.warning("Could not use the project's missing-file history; continuing without it.")
        return False

    def _query(self, action: _Action, key: str, now: float) -> bool:
        if action == "record":
            self._database.parent.mkdir(parents=True, exist_ok=True)
        else:
            try:
                self._database.stat()
            except FileNotFoundError:
                return False
        with closing(sqlite3.connect(self._database, timeout=1)) as connection, connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS missing_files (key TEXT PRIMARY KEY, observed_at REAL NOT NULL)"
            )
            if action == "lookup":
                # Only use observations already available when this sync started.
                return (
                    connection.execute(
                        "SELECT 1 FROM missing_files WHERE key = ? AND observed_at > ? AND observed_at < ?",
                        (key, now - _MAX_AGE, self._started_at),
                    ).fetchone()
                    is not None
                )
            if action == "record":
                connection.execute("CREATE INDEX IF NOT EXISTS missing_files_age ON missing_files (observed_at)")
                connection.execute("DELETE FROM missing_files WHERE observed_at <= ?", (now - _MAX_AGE,))
                connection.execute(
                    "INSERT INTO missing_files (key, observed_at) VALUES (?, ?) "
                    "ON CONFLICT (key) DO UPDATE SET observed_at = MAX(missing_files.observed_at, excluded.observed_at)",
                    (key, now),
                )
            else:
                connection.execute("DELETE FROM missing_files WHERE key = ? AND observed_at <= ?", (key, now))
        return False
