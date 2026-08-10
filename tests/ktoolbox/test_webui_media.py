from __future__ import annotations

import io
from pathlib import Path

import httpx
import pytest
from PIL import Image

from ktoolbox.configuration import Configuration, RuntimeContext
from ktoolbox.webui.app import create_app
from ktoolbox.webui.media import MAX_MEDIA_BYTES, MediaProxyService


def image_bytes(format_name: str = "JPEG", *, size: tuple[int, int] = (1200, 630)) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", size, (48, 112, 172)).save(output, format=format_name)
    return output.getvalue()


@pytest.mark.asyncio
async def test_media_routes_require_login_and_proxy_validated_images(tmp_path: Path) -> None:
    seen: list[httpx.Request] = []
    source = image_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, content=source, headers={"Content-Type": "application/octet-stream"})

    upstream = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    proxy = MediaProxyService(upstream)
    app = create_app(
        RuntimeContext(
            tmp_path,
            Configuration(
                _env_file=None,
                downloader={"session_key": "download-cookie"},
                webui={"username": "owner", "password": "secret"},
            ),
        ),
        media_proxy=proxy,
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            denied = await client.get("/api/v1/media/creators/fanbox/42/avatar?variant=thumbnail")
            assert denied.status_code == 401
            login = await client.post(
                "/api/v1/session/login",
                json={"username": "owner", "password": "secret"},
            )
            assert login.status_code == 200

            avatar = await client.get("/api/v1/media/creators/fanbox/42/avatar?variant=thumbnail")
            assert avatar.status_code == 200
            assert avatar.headers["Content-Type"] == "image/webp"
            assert avatar.headers["Cache-Control"] == "private, no-store"
            assert avatar.headers["Cross-Origin-Resource-Policy"] == "same-origin"
            with Image.open(io.BytesIO(avatar.content)) as rendered:
                assert max(rendered.size) == 480

            file_response = await client.get(
                "/api/v1/media/files",
                params={"path": "/aa/bb/example.jpg", "variant": "original"},
            )
            assert file_response.status_code == 200
            assert file_response.headers["Content-Type"] == "image/jpeg"

    assert seen[0].url.host == "pawchive.pw"
    assert "Cookie" not in seen[0].headers
    assert seen[1].url.host == "file.pawchive.pw"
    assert seen[1].headers["Cookie"] == "session=download-cookie"
    await upstream.aclose()


@pytest.mark.asyncio
async def test_media_proxy_rejects_unsafe_non_image_and_large_sources(tmp_path: Path) -> None:
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        if request.url.path.endswith("large.jpg"):
            return httpx.Response(200, headers={"Content-Length": str(MAX_MEDIA_BYTES + 1)})
        if request.url.path.endswith("redirect.jpg"):
            return httpx.Response(302, headers={"Location": "https://example.test/image.jpg"})
        return httpx.Response(200, content=b"<svg xmlns='http://www.w3.org/2000/svg'></svg>")

    upstream = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    app = create_app(
        RuntimeContext(
            tmp_path,
            Configuration(_env_file=None, webui={"username": "owner", "password": "secret"}),
        ),
        media_proxy=MediaProxyService(upstream),
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            await client.post("/api/v1/session/login", json={"username": "owner", "password": "secret"})

            unsafe = await client.get(
                "/api/v1/media/files",
                params={"path": "https://example.test/image.jpg", "variant": "thumbnail"},
            )
            traversal = await client.get(
                "/api/v1/media/files",
                params={"path": "/aa/../secret.jpg", "variant": "thumbnail"},
            )
            assert unsafe.status_code == 415
            assert traversal.status_code == 415
            assert requests == 0

            unsupported = await client.get(
                "/api/v1/media/files",
                params={"path": "/aa/image.svg", "variant": "thumbnail"},
            )
            too_large = await client.get(
                "/api/v1/media/files",
                params={"path": "/aa/large.jpg", "variant": "thumbnail"},
            )
            redirected = await client.get(
                "/api/v1/media/files",
                params={"path": "/aa/redirect.jpg", "variant": "thumbnail"},
            )
            assert unsupported.status_code == 415
            assert too_large.status_code == 413
            assert redirected.status_code == 502

    await upstream.aclose()


@pytest.mark.asyncio
async def test_thumbnail_cache_does_not_cache_originals(tmp_path: Path) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, content=image_bytes("PNG", size=(32, 24)))

    upstream = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    app = create_app(
        RuntimeContext(
            tmp_path,
            Configuration(_env_file=None, webui={"username": "owner", "password": "secret"}),
        ),
        media_proxy=MediaProxyService(upstream),
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            await client.post("/api/v1/session/login", json={"username": "owner", "password": "secret"})
            params = {"path": "/aa/cache.png", "variant": "thumbnail"}
            assert (await client.get("/api/v1/media/files", params=params)).status_code == 200
            assert (await client.get("/api/v1/media/files", params=params)).status_code == 200
            assert calls == 1

            params["variant"] = "original"
            assert (await client.get("/api/v1/media/files", params=params)).status_code == 200
            assert (await client.get("/api/v1/media/files", params=params)).status_code == 200
            assert calls == 3

    await upstream.aclose()
