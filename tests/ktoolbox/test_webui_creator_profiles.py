from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from ktoolbox.api.errors import PawchiveError
from ktoolbox.api.generated import CreatorProfile
from ktoolbox.configuration import Configuration, RuntimeContext
from ktoolbox.project_config import CreatorReference, ProjectConfigStore, ProjectConfiguration
from ktoolbox.webui.creator_profiles import (
    CachedCreatorProfile,
    CreatorProfileCache,
    CreatorRosterService,
)
from ktoolbox.webui.database import WebUIDatabase


class TrackingCreatorClient:
    active = 0
    maximum = 0
    calls: list[str] = []

    async def __aenter__(self) -> TrackingCreatorClient:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def get_creator_profile(self, service: str, creator_id: str) -> CreatorProfile:
        key = f"{service}:{creator_id}"
        self.calls.append(key)
        self.active += 1
        type(self).maximum = max(type(self).maximum, self.active)
        try:
            await asyncio.sleep(0.01)
            if creator_id.startswith("missing"):
                raise PawchiveError("fixture failure")
            return CreatorProfile(id=creator_id, service=service, name=f"Name {creator_id}")
        finally:
            self.active -= 1


@pytest.mark.asyncio
async def test_creator_profile_cache_migration_is_idempotent(tmp_path: Path) -> None:
    database = WebUIDatabase(tmp_path / "webui.sqlite3")
    await database.initialize()
    await database.initialize()

    async with database.connect() as connection:
        migration = await connection.execute_fetchall("SELECT version FROM schema_migrations WHERE version = 4")
        table = await connection.execute_fetchall(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'creator_profile_cache'"
        )
    assert migration == [(4,)]
    assert table == [("creator_profile_cache",)]


@pytest.mark.asyncio
async def test_roster_refreshes_profiles_with_bounded_concurrency_and_stale_fallback(tmp_path: Path) -> None:
    now = datetime(2026, 7, 22, tzinfo=timezone.utc)
    creators = [CreatorReference(service="fanbox", creator_id=str(index)) for index in range(6)]
    creators.extend(
        [
            CreatorReference(service="patreon", creator_id="fresh"),
            CreatorReference(service="pixiv", creator_id="missing-stale"),
            CreatorReference(service="pixiv", creator_id="missing-empty"),
        ]
    )
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration(creators=creators))
    database = WebUIDatabase(tmp_path / "webui.sqlite3")
    await database.initialize()
    cache = CreatorProfileCache(database)
    await cache.store(CachedCreatorProfile("patreon", "fresh", "Fresh cache", now))
    await cache.store(CachedCreatorProfile("pixiv", "missing-stale", "Stale cache", now - timedelta(days=2)))
    TrackingCreatorClient.calls = []
    TrackingCreatorClient.maximum = 0
    service = CreatorRosterService(
        store,
        cache,
        client_factory=TrackingCreatorClient,
        clock=lambda: now,
    )

    roster = await service.list_creators(RuntimeContext(tmp_path, Configuration(_env_file=None)))

    names = {f"{creator.service}:{creator.creator_id}": creator.name for creator in roster}
    assert names["patreon:fresh"] == "Fresh cache"
    assert names["pixiv:missing-stale"] == "Stale cache"
    assert names["pixiv:missing-empty"] is None
    assert names["fanbox:0"] == "Name 0"
    assert "patreon:fresh" not in TrackingCreatorClient.calls
    assert TrackingCreatorClient.maximum == 4

    TrackingCreatorClient.calls = []
    await service.list_creators(RuntimeContext(tmp_path, Configuration(_env_file=None)))
    assert sorted(TrackingCreatorClient.calls) == ["pixiv:missing-empty", "pixiv:missing-stale"]


@pytest.mark.asyncio
async def test_creator_profile_cache_delete_removes_entry(tmp_path: Path) -> None:
    database = WebUIDatabase(tmp_path / "webui.sqlite3")
    await database.initialize()
    cache = CreatorProfileCache(database)
    await cache.store(
        CachedCreatorProfile(
            service="fanbox",
            creator_id="42",
            name="Example",
            fetched_at=datetime.now(timezone.utc),
        )
    )
    await cache.delete("FANBOX", "42")
    assert await cache.load() == {}
