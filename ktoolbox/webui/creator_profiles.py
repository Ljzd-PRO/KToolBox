from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

import aiosqlite
import anyio
from pydantic import ValidationError

from ktoolbox.api.errors import PawchiveError
from ktoolbox.api.generated import CreatorProfile
from ktoolbox.api.utils import create_pawchive_client
from ktoolbox.configuration import RuntimeContext
from ktoolbox.project_config import CreatorReference, ProjectConfigStore
from ktoolbox.webui.database import WebUIDatabase, utc_now
from ktoolbox.webui.models import CreatorRosterItemResponse


class CreatorProfileClient(Protocol):
    async def get_creator_profile(self, service: str, creator_id: str) -> CreatorProfile: ...


CreatorClientFactory = Callable[[], AbstractAsyncContextManager[CreatorProfileClient]]


@dataclass(frozen=True, slots=True)
class CachedCreatorProfile:
    service: str
    creator_id: str
    name: str
    fetched_at: datetime

    @property
    def key(self) -> str:
        return _creator_key(self.service, self.creator_id)


class CreatorProfileCache:
    def __init__(self, database: WebUIDatabase) -> None:
        self.database = database

    async def load(self) -> dict[str, CachedCreatorProfile]:
        async with self.database.connect() as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                "SELECT service, creator_id, name, fetched_at FROM creator_profile_cache"
            )
            rows = await cursor.fetchall()
            await cursor.close()
        entries = (
            CachedCreatorProfile(
                service=str(row["service"]),
                creator_id=str(row["creator_id"]),
                name=str(row["name"]),
                fetched_at=datetime.fromisoformat(str(row["fetched_at"])),
            )
            for row in rows
        )
        return {entry.key: entry for entry in entries}

    async def store(self, entry: CachedCreatorProfile) -> None:
        async with self.database.connect() as connection:
            await connection.execute(
                """
                INSERT INTO creator_profile_cache(service, creator_id, name, fetched_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(service, creator_id) DO UPDATE SET
                    name = excluded.name,
                    fetched_at = excluded.fetched_at
                """,
                (entry.service, entry.creator_id, entry.name, entry.fetched_at.isoformat()),
            )
            await connection.commit()

    async def delete(self, service: str, creator_id: str) -> None:
        async with self.database.connect() as connection:
            await connection.execute(
                "DELETE FROM creator_profile_cache WHERE service = ? AND creator_id = ?",
                (service, creator_id),
            )
            await connection.commit()


class CreatorRosterService:
    def __init__(
        self,
        project_store: ProjectConfigStore,
        cache: CreatorProfileCache,
        *,
        client_factory: CreatorClientFactory | None = None,
        cache_lifetime: timedelta = timedelta(hours=24),
        max_concurrency: int = 4,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.project_store = project_store
        self.cache = cache
        self.client_factory = client_factory or create_pawchive_client
        self.cache_lifetime = cache_lifetime
        self.max_concurrency = max_concurrency
        self.clock = clock

    async def list_creators(self, context: RuntimeContext) -> list[CreatorRosterItemResponse]:
        creators = self.project_store.load().creators
        cached = await self.cache.load()
        now = self.clock()
        refresh = [
            creator
            for creator in creators
            if (entry := cached.get(_creator_key(creator.service, creator.creator_id))) is None
            or now - entry.fetched_at >= self.cache_lifetime
        ]
        if refresh:
            cached.update(await self._refresh(context, refresh, now))

        return [
            CreatorRosterItemResponse(
                **creator.model_dump(),
                name=(
                    entry.name
                    if (entry := cached.get(_creator_key(creator.service, creator.creator_id)))
                    else None
                ),
            )
            for creator in creators
        ]

    async def delete(self, service: str, creator_id: str) -> None:
        await self.cache.delete(service, creator_id)

    async def _refresh(
        self,
        context: RuntimeContext,
        creators: list[CreatorReference],
        fetched_at: datetime,
    ) -> dict[str, CachedCreatorProfile]:
        refreshed: dict[str, CachedCreatorProfile] = {}
        limiter = anyio.CapacityLimiter(self.max_concurrency)

        async def fetch(client: CreatorProfileClient, creator: CreatorReference) -> None:
            async with limiter:
                try:
                    profile = await client.get_creator_profile(creator.service, creator.creator_id)
                except (PawchiveError, ValidationError):
                    return
                name = profile.name.strip()
                if not name:
                    return
                entry = CachedCreatorProfile(
                    service=creator.service,
                    creator_id=creator.creator_id,
                    name=name,
                    fetched_at=fetched_at,
                )
                refreshed[entry.key] = entry

        with context.activate():
            try:
                async with self.client_factory() as client:
                    async with anyio.create_task_group() as task_group:
                        for creator in creators:
                            task_group.start_soon(fetch, client, creator)
            except (PawchiveError, ValidationError):
                return {}
        for entry in refreshed.values():
            await self.cache.store(entry)
        return refreshed


def _creator_key(service: str, creator_id: str) -> str:
    return f"{service}:{creator_id}".casefold()
