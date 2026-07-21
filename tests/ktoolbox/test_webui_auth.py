from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest
from argon2 import PasswordHasher

from ktoolbox.configuration import Configuration, RuntimeContext
from ktoolbox.webui.app import create_app
from ktoolbox.webui.auth import CSRF_HEADER, LoginRateLimiter


@asynccontextmanager
async def web_client(tmp_path: Path, *, webui: dict[str, object]) -> AsyncIterator[httpx.AsyncClient]:
    configuration = Configuration(_env_file=None, webui=webui)
    app = create_app(RuntimeContext(tmp_path, configuration))
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 1234))
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client


@pytest.mark.asyncio
async def test_plaintext_login_session_project_and_logout(tmp_path: Path) -> None:
    async with web_client(tmp_path, webui={"username": "owner", "password": "correct horse"}) as client:
        assert (await client.get("/api/v1/health")).json() == {"status": "ok"}
        assert (await client.get("/api/v1/project")).status_code == 401
        frontend = await client.get("/")
        assert frontend.status_code == 200
        assert "KToolBox" in frontend.text
        assert frontend.headers["content-security-policy"].startswith("default-src 'self'")

        response = await client.post(
            "/api/v1/session/login",
            json={"username": "owner", "password": "correct horse"},
        )
        assert response.status_code == 200
        assert response.json()["username"] == "owner"
        assert "HttpOnly" in response.headers["set-cookie"]
        assert "SameSite=strict" in response.headers["set-cookie"]
        assert "Secure" not in response.headers["set-cookie"]
        assert response.headers["x-frame-options"] == "DENY"
        csrf = response.json()["csrf_token"]

        session = await client.get("/api/v1/session")
        assert session.status_code == 200
        project = await client.get("/api/v1/project")
        assert project.json()["root"] == str(tmp_path)
        assert project.headers["cache-control"] == "no-store"

        assert (await client.post("/api/v1/session/logout")).status_code == 403
        logout = await client.post("/api/v1/session/logout", headers={CSRF_HEADER: csrf})
        assert logout.status_code == 204
        assert (await client.get("/api/v1/session")).status_code == 401


@pytest.mark.asyncio
async def test_argon_hash_takes_precedence_and_https_cookie_is_secure(tmp_path: Path) -> None:
    password_hash = PasswordHasher().hash("hashed secret")
    configuration = Configuration(
        _env_file=None,
        webui={
            "username": "owner",
            "password": "plaintext fallback",
            "password_hash": password_hash,
        },
    )
    app = create_app(RuntimeContext(tmp_path, configuration))
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 1234))
        async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
            rejected = await client.post(
                "/api/v1/session/login",
                json={"username": "owner", "password": "plaintext fallback"},
            )
            assert rejected.status_code == 401
            accepted = await client.post(
                "/api/v1/session/login",
                json={"username": "owner", "password": "hashed secret"},
            )
            assert accepted.status_code == 200
            assert "Secure" in accepted.headers["set-cookie"]


@pytest.mark.asyncio
async def test_login_rate_limit_and_origin_check(tmp_path: Path) -> None:
    async with web_client(tmp_path, webui={"username": "owner", "password": "secret"}) as client:
        app = client._transport.app
        app.state.auth.rate_limiter = LoginRateLimiter(maximum=2, window_seconds=60)
        for expected in (401, 401, 429):
            response = await client.post(
                "/api/v1/session/login",
                json={"username": "owner", "password": "wrong"},
            )
            assert response.status_code == expected

        app.state.auth.rate_limiter = LoginRateLimiter()
        login = await client.post(
            "/api/v1/session/login",
            json={"username": "owner", "password": "secret"},
        )
        response = await client.post(
            "/api/v1/session/logout",
            headers={CSRF_HEADER: login.json()["csrf_token"], "Origin": "http://attacker.test"},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_missing_or_invalid_credentials_fail_startup(tmp_path: Path) -> None:
    missing = create_app(RuntimeContext(tmp_path, Configuration(_env_file=None)))
    with pytest.raises(ValueError, match="USERNAME"):
        async with missing.router.lifespan_context(missing):
            pass

    invalid = create_app(
        RuntimeContext(
            tmp_path,
            Configuration(
                _env_file=None,
                webui={"username": "owner", "password_hash": "not-a-hash"},
            ),
        )
    )
    with pytest.raises(ValueError, match="valid Argon2"):
        async with invalid.router.lifespan_context(invalid):
            pass
