from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path

import aiosqlite
import httpx
import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from ktoolbox.configuration import Configuration, RuntimeContext
from ktoolbox.project_config import ProjectConfigStore, ProjectConfiguration
from ktoolbox.webui.app import create_app
from ktoolbox.webui.database import utc_now


def _app(project_root: Path):
    ProjectConfigStore(project_root / "ktoolbox.toml").save(ProjectConfiguration())
    configuration = Configuration(
        _env_file=None,
        webui={"username": "owner", "password": "correct horse battery staple"},
    )
    return create_app(RuntimeContext(project_root, configuration))


async def _login(client: httpx.AsyncClient) -> str:
    response = await client.post(
        "/api/v1/session/login",
        json={"username": "owner", "password": "correct horse battery staple"},
    )
    assert response.status_code == 200
    return str(response.json()["csrf_token"])


async def _create_token(
    client: httpx.AsyncClient,
    csrf: str,
    *,
    permission: str = "read",
    expires_in_days: int | None = None,
) -> dict[str, object]:
    response = await client.post(
        "/api/v1/mcp/tokens",
        json={
            "name": "Test client",
            "password": "correct horse battery staple",
            "permission": permission,
            "expires_in_days": expires_in_days,
        },
        headers={"X-CSRF-Token": csrf, "Origin": "http://test"},
    )
    assert response.status_code == 201
    return response.json()


@asynccontextmanager
async def _mcp_session(
    app: object,
    token: str,
) -> AsyncIterator[ClientSession]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        async with streamable_http_client("http://test/mcp", http_client=client) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session


@pytest.mark.asyncio
async def test_password_issued_tokens_are_hashed_listed_and_revoked(tmp_path: Path) -> None:
    app = _app(tmp_path)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            csrf = await _login(client)
            invalid = await client.post(
                "/api/v1/mcp/tokens",
                json={
                    "name": "Invalid",
                    "password": "wrong",
                    "permission": "read",
                    "expires_in_days": None,
                },
                headers={"X-CSRF-Token": csrf, "Origin": "http://test"},
            )
            assert invalid.status_code == 401

            created = await _create_token(client, csrf, permission="manage")
            raw_token = str(created["token"])
            assert raw_token.startswith("ktmcp_")
            assert created["expires_at"] is None
            assert created["permission"] == "manage"
            assert created["scopes"] == ["mcp:read", "mcp:write"]

            listed = await client.get("/api/v1/mcp/tokens")
            assert listed.status_code == 200
            assert "token" not in listed.json()[0]
            assert listed.json()[0]["active"] is True

            async with aiosqlite.connect(tmp_path / ".ktoolbox" / "webui.sqlite3") as connection:
                cursor = await connection.execute(
                    "SELECT token_hash, expires_at FROM mcp_tokens WHERE id = ?",
                    (created["id"],),
                )
                stored_hash, expires_at = await cursor.fetchone()
                await cursor.close()
            assert stored_hash != raw_token
            assert raw_token not in stored_hash
            assert expires_at is None

            revoked = await client.post(
                f"/api/v1/mcp/tokens/{created['id']}/revoke",
                headers={"X-CSRF-Token": csrf, "Origin": "http://test"},
            )
            assert revoked.status_code == 200
            assert revoked.json()["active"] is False
            assert await app.state.mcp_token_store.verify(raw_token) is None
            events = await app.state.event_store.events()
            token_events = [event.data["action"] for event in events if event.event_type == "mcp.tokens.changed"]
            assert token_events == ["created", "revoked"]


@pytest.mark.asyncio
async def test_read_token_filters_write_tools_and_revocation_stops_protocol_access(tmp_path: Path) -> None:
    app = _app(tmp_path)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            csrf = await _login(client)
            created = await _create_token(client, csrf, permission="read", expires_in_days=30)
            token = str(created["token"])

            async with _mcp_session(app, token) as session:
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                assert "get_project_summary" in names
                assert "search_works" in names
                assert "create_task" not in names
                assert "add_creator" not in names
                assert "delete_task_record" not in names

                result = await session.call_tool("get_project_summary", {})
                assert result.isError is False
                assert result.structuredContent is not None
                assert result.structuredContent["root"] == str(tmp_path)

            tokens = await client.get("/api/v1/mcp/tokens")
            assert tokens.json()[0]["last_used_at"] is not None
            token_events = [
                event for event in await app.state.event_store.events() if event.event_type == "mcp.tokens.changed"
            ]
            assert [event.data["action"] for event in token_events] == ["created", "used"]
            assert await app.state.mcp_token_store.verify(token) is not None
            token_events = [
                event for event in await app.state.event_store.events() if event.event_type == "mcp.tokens.changed"
            ]
            assert [event.data["action"] for event in token_events] == ["created", "used"]
            await client.post(
                f"/api/v1/mcp/tokens/{created['id']}/revoke",
                headers={"X-CSRF-Token": csrf, "Origin": "http://test"},
            )
            initialize = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1"},
                },
            }
            denied = await client.post(
                "/mcp",
                json=initialize,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json, text/event-stream"},
            )
            assert denied.status_code == 401


@pytest.mark.asyncio
async def test_limited_token_expires_and_permanent_token_does_not(tmp_path: Path) -> None:
    app = _app(tmp_path)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            csrf = await _login(client)
            limited = await _create_token(client, csrf, expires_in_days=7)
            permanent = await _create_token(client, csrf, expires_in_days=None)

        async with app.state.database.connect() as connection:
            await connection.execute(
                "UPDATE mcp_tokens SET expires_at = ? WHERE id = ?",
                ((utc_now() - timedelta(seconds=1)).isoformat(), limited["id"]),
            )
            await connection.commit()

        assert await app.state.mcp_token_store.verify(str(limited["token"])) is None
        assert await app.state.mcp_token_store.verify(str(permanent["token"])) is not None


@pytest.mark.asyncio
async def test_mcp_metadata_and_openapi_download_are_authenticated(tmp_path: Path) -> None:
    app = _app(tmp_path)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            assert (await client.get("/api/v1/mcp/status")).status_code == 401
            csrf = await _login(client)

            status_response = await client.get("/api/v1/mcp/status")
            tools_response = await client.get("/api/v1/mcp/tools")
            schema_response = await client.get("/api/v1/openapi.yaml")
            page_response = await client.get("/mcp", headers={"Accept": "text/html"})
            assert status_response.status_code == 200
            assert status_response.json()["endpoint_path"] == "/mcp"
            assert status_response.json()["tool_count"] == len(tools_response.json())
            assert schema_response.status_code == 200
            assert schema_response.headers["content-type"].startswith("application/yaml")
            assert "x-ktoolbox-mcp:" in schema_response.text
            assert page_response.status_code == 200
            assert page_response.headers["content-type"].startswith("text/html")
            assert '<div id="root"></div>' in page_response.text

            created = await _create_token(client, csrf, permission="manage")
            async with _mcp_session(app, str(created["token"])) as session:
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                assert {
                    "browse_project_files",
                    "patch_mcp_configuration",
                    "delete_task_record",
                    "get_work",
                } <= names
