from __future__ import annotations

import json
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

import aiosqlite

from ktoolbox.webui.database import WebUIDatabase, token_digest, utc_now
from ktoolbox.webui.event_store import WebUIEventStore

READ_SCOPE = "mcp:read"
WRITE_SCOPE = "mcp:write"


@dataclass(frozen=True, slots=True)
class MCPTokenRecord:
    id: str
    name: str
    username: str
    scopes: tuple[str, ...]
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None
    revoked_at: datetime | None

    @property
    def permission(self) -> Literal["read", "manage"]:
        return "manage" if WRITE_SCOPE in self.scopes else "read"

    @property
    def active(self) -> bool:
        return self.revoked_at is None and (self.expires_at is None or self.expires_at > utc_now())


@dataclass(frozen=True, slots=True)
class CreatedMCPToken:
    token: str
    record: MCPTokenRecord


class MCPTokenStore:
    def __init__(self, database: WebUIDatabase, events: WebUIEventStore | None = None) -> None:
        self.database = database
        self.events = events

    async def create(
        self,
        *,
        name: str,
        username: str,
        permission: str,
        expires_in_days: int | None,
    ) -> CreatedMCPToken:
        now = utc_now()
        expires_at = None if expires_in_days is None else now + timedelta(days=expires_in_days)
        scopes = (READ_SCOPE, WRITE_SCOPE) if permission == "manage" else (READ_SCOPE,)
        raw_token = f"ktmcp_{secrets.token_urlsafe(36)}"
        record = MCPTokenRecord(
            id=str(uuid.uuid4()),
            name=name,
            username=username,
            scopes=scopes,
            created_at=now,
            expires_at=expires_at,
            last_used_at=None,
            revoked_at=None,
        )
        async with self.database.connect() as connection:
            await connection.execute(
                """
                INSERT INTO mcp_tokens(
                    id, name, username, token_hash, scopes_json, created_at, expires_at, last_used_at, revoked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL)
                """,
                (
                    record.id,
                    record.name,
                    record.username,
                    token_digest(raw_token),
                    json.dumps(record.scopes),
                    record.created_at.isoformat(),
                    record.expires_at.isoformat() if record.expires_at else None,
                ),
            )
            await connection.commit()
        if self.events is not None:
            await self.events.publish(
                "mcp.tokens.changed",
                {"action": "created"},
                resource="mcp_token",
                resource_id=record.id,
            )
        return CreatedMCPToken(raw_token, record)

    async def list(self, username: str) -> list[MCPTokenRecord]:
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                """
                SELECT id, name, username, scopes_json, created_at, expires_at, last_used_at, revoked_at
                FROM mcp_tokens
                WHERE username = ?
                ORDER BY created_at DESC
                """,
                (username,),
            )
            rows = await cursor.fetchall()
            await cursor.close()
        return [_record(row) for row in rows]

    async def revoke(self, token_id: str, username: str) -> MCPTokenRecord | None:
        now = utc_now()
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                """
                UPDATE mcp_tokens
                SET revoked_at = COALESCE(revoked_at, ?)
                WHERE id = ? AND username = ?
                RETURNING id, name, username, scopes_json, created_at, expires_at, last_used_at, revoked_at
                """,
                (now.isoformat(), token_id, username),
            )
            row = await cursor.fetchone()
            await cursor.close()
            await connection.commit()
        record = _record(row) if row is not None else None
        if record is not None and self.events is not None:
            await self.events.publish(
                "mcp.tokens.changed",
                {"action": "revoked"},
                resource="mcp_token",
                resource_id=record.id,
            )
        return record

    async def verify(self, token: str) -> MCPTokenRecord | None:
        now = utc_now()
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                """
                SELECT id, name, username, scopes_json, created_at, expires_at, last_used_at, revoked_at
                FROM mcp_tokens
                WHERE token_hash = ?
                """,
                (token_digest(token),),
            )
            row = await cursor.fetchone()
            await cursor.close()
            if row is None:
                return None
            record = _record(row)
            if not record.active:
                return None
            should_update = record.last_used_at is None or now - record.last_used_at >= timedelta(minutes=1)
            if should_update:
                await connection.execute(
                    "UPDATE mcp_tokens SET last_used_at = ? WHERE id = ?",
                    (now.isoformat(), record.id),
                )
                await connection.commit()
        if should_update and self.events is not None:
            await self.events.publish(
                "mcp.tokens.changed",
                {"action": "used"},
                resource="mcp_token",
                resource_id=record.id,
            )
        return MCPTokenRecord(
            id=record.id,
            name=record.name,
            username=record.username,
            scopes=record.scopes,
            created_at=record.created_at,
            expires_at=record.expires_at,
            last_used_at=now if should_update else record.last_used_at,
            revoked_at=record.revoked_at,
        )


def _record(row: aiosqlite.Row) -> MCPTokenRecord:
    return MCPTokenRecord(
        id=str(row["id"]),
        name=str(row["name"]),
        username=str(row["username"]),
        scopes=tuple(json.loads(row["scopes_json"])),
        created_at=datetime.fromisoformat(row["created_at"]),
        expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
        last_used_at=datetime.fromisoformat(row["last_used_at"]) if row["last_used_at"] else None,
        revoked_at=datetime.fromisoformat(row["revoked_at"]) if row["revoked_at"] else None,
    )
