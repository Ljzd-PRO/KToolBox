from __future__ import annotations

import logging
from collections.abc import Callable
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import ValidationError

from ktoolbox.api.client import PawchiveClient, ResponseDrift
from ktoolbox.api.errors import (
    PawchiveAuthenticationError,
    PawchiveConflictError,
    PawchiveHTTPError,
    PawchiveNotFoundError,
    PawchiveResponseValidationError,
    PawchiveTransportError,
)
from ktoolbox.api.generated import (
    Announcement,
    Comment,
    CreatorProfile,
    CreatorSummary,
    Fancard,
    FileSearchResult,
    Post,
    Revision,
)

BASE_URL = "https://example.test/api/v1"
FILE_HASH = "a" * 64
POST_DATA = {
    "id": "post",
    "user": "creator",
    "service": "fanbox",
    "title": "Example",
    "attachments": [],
}


def response(
    request: httpx.Request,
    status: int = 200,
    *,
    json: object | None = None,
    text: str | None = None,
) -> httpx.Response:
    if text is not None:
        return httpx.Response(status, text=text, request=request)
    return httpx.Response(status, json=json, request=request)


@pytest.mark.asyncio
async def test_all_fourteen_public_operations_and_request_contract() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["accept"] == "application/json"
        assert "cookie" not in request.headers
        assert request.extensions["timeout"]["read"] == 7.0
        path = request.url.path.removeprefix("/api/v1")
        if path == "/creators":
            payload = [
                {"favorited": 1, "id": "creator", "indexed": 0, "name": "Name", "service": "fanbox", "updated": 1}
            ]
        elif path == "/posts" or path == "/fanbox/user/creator":
            payload = [POST_DATA]
        elif path.endswith("/profile"):
            payload = {"id": "creator", "name": "Name", "service": "fanbox"}
        elif path.endswith("/announcements"):
            payload = [{"service": "fanbox", "user_id": "creator"}]
        elif path.endswith("/fancards"):
            payload = [{"id": 1, "user_id": "creator"}]
        elif path.endswith("/links"):
            payload = [{"id": "linked", "name": "Linked", "service": "patreon"}]
        elif path.endswith("/revisions"):
            payload = [POST_DATA | {"revision_id": 7}]
        elif path.endswith("/comments"):
            payload = [{"id": "comment", "commenter_name": "User"}]
        elif path == "/fanbox/user/creator/post/post/flag":
            return response(request, 201 if request.method == "POST" else 200)
        elif path == "/fanbox/user/creator/post/post":
            payload = POST_DATA
        elif path == f"/search_hash/{FILE_HASH}":
            payload = {"hash": FILE_HASH, "posts": [], "discord_posts": []}
        elif path == "/app_version":
            return response(request, text=" custom \n")
        else:  # pragma: no cover - the assertion provides a useful failure path
            raise AssertionError(f"Unexpected path: {path}")
        return response(request, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        async with PawchiveClient(base_url=BASE_URL, timeout=7, http_client=http_client) as client:
            creators = await client.list_creators()
            recent = await client.list_recent_posts(query="term", offset=50)
            profile = await client.get_creator_profile("fanbox", "creator")
            creator_posts = await client.list_creator_posts("fanbox", "creator")
            announcements = await client.list_announcements("fanbox", "creator")
            fancards = await client.list_fancards("fanbox", "creator")
            links = await client.list_creator_links("fanbox", "creator")
            post = await client.get_post("fanbox", "creator", "post")
            file_result = await client.search_file_by_hash(FILE_HASH)
            await client.flag_post("fanbox", "creator", "post")
            flagged = await client.is_post_flagged("fanbox", "creator", "post")
            revisions = await client.list_post_revisions("fanbox", "creator", "post")
            comments = await client.list_post_comments("fanbox", "creator", "post")
            app_version = await client.get_app_version()

    assert isinstance(creators[0], CreatorSummary)
    assert isinstance(recent[0], Post)
    assert isinstance(profile, CreatorProfile)
    assert isinstance(creator_posts[0], Post)
    assert isinstance(announcements[0], Announcement)
    assert isinstance(fancards[0], Fancard)
    assert isinstance(links[0], CreatorProfile)
    assert isinstance(post, Post)
    assert isinstance(file_result, FileSearchResult)
    assert flagged is True
    assert isinstance(revisions[0], Revision)
    assert isinstance(comments[0], Comment)
    assert app_version == "custom"
    assert len(requests) == 14
    recent_request = next(item for item in requests if item.url.path.endswith("/posts"))
    assert dict(recent_request.url.params) == {"q": "term", "o": "50"}
    creator_request = next(item for item in requests if item.url.path.endswith("/fanbox/user/creator"))
    assert not creator_request.url.query


@pytest.mark.asyncio
async def test_path_segments_are_escaped() -> None:
    seen: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.raw_path)
        return response(request, json=POST_DATA | {"service": "fan/box", "user": "creator id", "id": "post/id"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = PawchiveClient(base_url=BASE_URL, http_client=http_client)
        await client.get_post("fan/box", "creator id", "post/id")
    assert seen == [b"/api/v1/fan%2Fbox/user/creator%20id/post/post%2Fid"]


@pytest.mark.parametrize(
    ("call"),
    [
        lambda client: client.list_recent_posts(query="ab"),
        lambda client: client.list_recent_posts(offset=-50),
        lambda client: client.list_recent_posts(offset=1),
        lambda client: client.get_post("", "creator", "post"),
        lambda client: client.get_post("fanbox", "", "post"),
        lambda client: client.get_post("fanbox", "creator", ""),
        lambda client: client.search_file_by_hash("a" * 63),
        lambda client: client.search_file_by_hash("z" * 64),
    ],
)
@pytest.mark.asyncio
async def test_invalid_parameters_fail_before_request(call: Callable[[PawchiveClient], object]) -> None:
    transport = httpx.MockTransport(lambda request: response(request, json={}))
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = PawchiveClient(base_url=BASE_URL, http_client=http_client)
        with pytest.raises(ValidationError):
            await call(client)


@pytest.mark.parametrize(
    ("status", "exception_type"),
    [
        (400, PawchiveHTTPError),
        (401, PawchiveAuthenticationError),
        (403, PawchiveAuthenticationError),
        (404, PawchiveNotFoundError),
        (409, PawchiveConflictError),
    ],
)
@pytest.mark.asyncio
async def test_status_to_typed_exception(status: int, exception_type: type[PawchiveHTTPError]) -> None:
    transport = httpx.MockTransport(lambda request: response(request, status, json={}))
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = PawchiveClient(base_url=BASE_URL, http_client=http_client, max_retries=0)
        with pytest.raises(exception_type) as caught:
            await client.get_post("fanbox", "creator", "post")
    assert caught.value.status_code == status
    assert "fanbox/user/creator/post/post" in str(caught.value)


@pytest.mark.asyncio
async def test_redirect_is_not_followed() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(302, headers={"location": "/redirected"}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True) as http_client:
        client = PawchiveClient(base_url=BASE_URL, http_client=http_client, max_retries=0)
        with pytest.raises(PawchiveHTTPError):
            await client.get_app_version()
    assert calls == 1


@pytest.mark.asyncio
async def test_retries_transport_429_and_server_errors() -> None:
    calls = 0
    sleep = AsyncMock()

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ConnectError("offline", request=request)
        if calls == 2:
            return response(request, 429)
        if calls == 3:
            return response(request, 503)
        return response(request, json=[])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = PawchiveClient(
            base_url=BASE_URL,
            http_client=http_client,
            max_retries=3,
            retry_interval=0.25,
            sleep=sleep,
        )
        assert await client.list_recent_posts() == []
    assert calls == 4
    assert sleep.await_count == 3
    sleep.assert_awaited_with(0.25)


@pytest.mark.asyncio
async def test_exhausted_transport_and_server_status() -> None:
    def disconnected(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(disconnected)) as http_client:
        client = PawchiveClient(base_url=BASE_URL, http_client=http_client, max_retries=0)
        with pytest.raises(PawchiveTransportError) as caught:
            await client.list_recent_posts()
    assert caught.value.method == "GET"
    assert caught.value.url.path.endswith("/posts")
    assert isinstance(caught.value.cause, httpx.ConnectError)

    transport = httpx.MockTransport(lambda request: response(request, 500))
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = PawchiveClient(base_url=BASE_URL, http_client=http_client, max_retries=0)
        with pytest.raises(PawchiveHTTPError):
            await client.list_recent_posts()


@pytest.mark.asyncio
async def test_invalid_json_and_model_are_validation_errors() -> None:
    payloads = iter(["not-json", "{}"])

    def handler(request: httpx.Request) -> httpx.Response:
        return response(request, text=next(payloads))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = PawchiveClient(base_url=BASE_URL, http_client=http_client, max_retries=0)
        for _ in range(2):
            with pytest.raises(PawchiveResponseValidationError) as caught:
                await client.get_post("fanbox", "creator", "post")
            assert caught.value.operation == "get_post"
            assert caught.value.response.status_code == 200
            assert isinstance(caught.value.cause, ValueError)


@pytest.mark.asyncio
async def test_response_drift_is_preserved_and_reported() -> None:
    reports: list[ResponseDrift] = []
    payload = POST_DATA | {
        "future": {"enabled": True},
        "attachments": [{"name": "file", "path": "/hash", "checksum": "abc"}],
    }
    transport = httpx.MockTransport(lambda request: response(request, json=payload))
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = PawchiveClient(base_url=BASE_URL, http_client=http_client, drift_reporter=reports.append)
        post = await client.get_post("fanbox", "creator", "post")
    assert post.model_extra == {"future": {"enabled": True}}
    assert post.attachments and post.attachments[0].model_extra == {"checksum": "abc"}
    assert reports == [
        ResponseDrift(
            operation="get_post",
            fields=("$.attachments[].checksum", "$.future"),
        )
    ]


@pytest.mark.asyncio
async def test_default_drift_reporter_logs_only_field_names(caplog: pytest.LogCaptureFixture) -> None:
    transport = httpx.MockTransport(lambda request: response(request, json=POST_DATA | {"unknown": "secret"}))
    with caplog.at_level(logging.WARNING, logger="ktoolbox.api.client"):
        async with httpx.AsyncClient(transport=transport) as http_client:
            client = PawchiveClient(base_url=BASE_URL, http_client=http_client)
            await client.get_post("fanbox", "creator", "post")
    assert "$.unknown" in caplog.text
    assert "secret" not in caplog.text


@pytest.mark.asyncio
async def test_flag_status_and_client_lifecycle() -> None:
    statuses = iter([404, 409])
    transport = httpx.MockTransport(lambda request: response(request, next(statuses)))
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = PawchiveClient(base_url=BASE_URL, http_client=http_client, max_retries=0)
        assert await client.is_post_flagged("fanbox", "creator", "post") is False
        with pytest.raises(PawchiveConflictError):
            await client.flag_post("fanbox", "creator", "post")
        await client.aclose()
        await client.aclose()
        assert not http_client.is_closed
        with pytest.raises(RuntimeError, match="closed"):
            await client.list_creators()

    owned = PawchiveClient(base_url=BASE_URL)
    owned_http_client = owned._http_client
    async with owned:
        pass
    assert owned_http_client.is_closed


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"base_url": "/relative"}, "absolute"),
        ({"max_retries": -1}, "max_retries"),
        ({"retry_interval": -1}, "retry_interval"),
    ],
)
def test_invalid_client_configuration(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        PawchiveClient(**kwargs)
