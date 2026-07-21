from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from ktoolbox.api.generated import CreatorSummary, Post, Revision
from ktoolbox.configuration import Configuration, RuntimeContext
from ktoolbox.webui.app import create_app


class ClientContext(AbstractAsyncContextManager[object]):
    def __init__(self, client: object) -> None:
        self.client = client

    async def __aenter__(self) -> object:
        return self.client

    async def __aexit__(self, *args: object) -> None:
        return None


@pytest.mark.asyncio
async def test_pawchive_query_routes_use_typed_client(tmp_path: Path) -> None:
    creator = CreatorSummary(
        id="42",
        name="Example",
        service="fanbox",
        favorited=0,
        indexed=0,
        updated=0,
    )
    post = Post(id="99", user="42", service="fanbox", title="Fixture post")
    revision = Revision(id="99", user="42", service="fanbox", revision_id=7)
    api_client = SimpleNamespace(
        list_creators=AsyncMock(return_value=[creator]),
        list_creator_posts=AsyncMock(return_value=[post]),
        get_post=AsyncMock(return_value=post),
        list_post_revisions=AsyncMock(return_value=[revision]),
        get_app_version=AsyncMock(return_value="2026.07"),
    )
    app = create_app(
        RuntimeContext(
            tmp_path,
            Configuration(_env_file=None, webui={"username": "owner", "password": "secret"}),
        )
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            login = await client.post(
                "/api/v1/session/login",
                json={"username": "owner", "password": "secret"},
            )
            assert login.status_code == 200
            with patch(
                "ktoolbox.webui.pawchive_routes.create_pawchive_client",
                return_value=ClientContext(api_client),
            ):
                creators = await client.get("/api/v1/pawchive/creators?name=Example")
                assert creators.json()[0]["id"] == "42"
                posts = await client.get("/api/v1/pawchive/posts?service=fanbox&creator_id=42")
                assert posts.json()[0]["id"] == "99"
                details = await client.get("/api/v1/pawchive/posts/fanbox/42/99")
                assert details.json()["title"] == "Fixture post"
                selected = await client.get("/api/v1/pawchive/posts/fanbox/42/99?revision_id=7")
                assert selected.json()["revision_id"] == 7
                revisions = await client.get("/api/v1/pawchive/posts/fanbox/42/99/revisions")
                assert revisions.json()[0]["revision_id"] == 7
                missing = await client.get("/api/v1/pawchive/posts/fanbox/42/99?revision_id=8")
                assert missing.status_code == 404
                version = await client.get("/api/v1/pawchive/site-version")
                assert version.json() == {"version": "2026.07"}

            invalid = await client.get("/api/v1/pawchive/posts")
            assert invalid.status_code == 422
