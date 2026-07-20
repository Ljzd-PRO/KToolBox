from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import ValidationError

from ktoolbox._enum import RetCodeEnum
from ktoolbox.action.base import action_error
from ktoolbox.action.fetch import FetchInterruptError, fetch_creator_posts
from ktoolbox.action.search import search_creator, search_creator_post
from ktoolbox.api.errors import (
    PawchiveHTTPError,
    PawchiveNotFoundError,
    PawchiveResponseValidationError,
    PawchiveTransportError,
)
from ktoolbox.api.generated import CreatorSummary, Post


def response(status: int = 500) -> httpx.Response:
    request = httpx.Request("GET", "https://example.test/resource")
    return httpx.Response(status, request=request)


def creator(creator_id: str, name: str, service: str = "fanbox") -> CreatorSummary:
    return CreatorSummary(
        favorited=0,
        id=creator_id,
        indexed=0,
        name=name,
        service=service,
        updated=0,
    )


def posts(count: int, *, prefix: str = "post") -> list[Post]:
    return [Post(id=f"{prefix}-{index}", user="creator", service="fanbox") for index in range(count)]


def test_action_error_maps_typed_failures() -> None:
    request = httpx.Request("GET", "https://example.test")
    transport = PawchiveTransportError("GET", request.url, httpx.ConnectError("offline", request=request))
    validation = PawchiveResponseValidationError("get_post", response(200), ValueError("bad"))
    general = PawchiveHTTPError(response())

    assert action_error(transport).code == RetCodeEnum.NetWorkError
    assert action_error(validation).code == RetCodeEnum.ValidationError
    assert action_error(general).code == RetCodeEnum.GeneralFailure
    assert action_error(general).exception is general


@pytest.mark.asyncio
async def test_fetch_creator_posts_paginates_and_stops_on_short_page() -> None:
    first = posts(50, prefix="first")
    second = posts(2, prefix="second")
    client = SimpleNamespace(list_creator_posts=AsyncMock(side_effect=[first, second]))

    pages = [page async for page in fetch_creator_posts("fanbox", "creator", client=client)]

    assert pages == [first, second]
    assert client.list_creator_posts.await_args_list[0].kwargs == {"offset": 0}
    assert client.list_creator_posts.await_args_list[1].kwargs == {"offset": 50}


@pytest.mark.asyncio
async def test_fetch_creator_posts_handles_not_found_and_api_failure() -> None:
    not_found = PawchiveNotFoundError(response(404))
    client = SimpleNamespace(list_creator_posts=AsyncMock(side_effect=not_found))
    assert [page async for page in fetch_creator_posts("fanbox", "creator", client=client)] == []

    failure = PawchiveHTTPError(response())
    client.list_creator_posts.side_effect = failure
    with pytest.raises(FetchInterruptError) as caught:
        [page async for page in fetch_creator_posts("fanbox", "creator", client=client)]
    assert caught.value.error is failure
    assert str(caught.value) == str(failure)


@pytest.mark.asyncio
async def test_creator_search_filters_and_maps_failures() -> None:
    creators = [creator("one", "Alice"), creator("two", "Bob"), creator("one", "Alice", "patreon")]
    client = SimpleNamespace(list_creators=AsyncMock(return_value=creators))

    result = await search_creator(id="one", name="Alice", service="fanbox", client=client)
    assert [item.service for item in result.data or ()] == ["fanbox"]
    assert list((await search_creator(name="Missing", client=client)).data or ()) == []

    client.list_creators.side_effect = PawchiveHTTPError(response())
    failure = await search_creator(client=client)
    assert not failure
    assert list(failure.data or ()) == []


@pytest.mark.asyncio
async def test_post_search_direct_indirect_missing_and_error_paths() -> None:
    direct_posts = posts(1)
    client = SimpleNamespace(
        list_creator_posts=AsyncMock(return_value=direct_posts),
        list_creators=AsyncMock(return_value=[creator("one", "Alice"), creator("two", "Bob")]),
    )

    missing = await search_creator_post(client=client)
    assert missing.code == RetCodeEnum.MissingParameter

    direct = await search_creator_post(id="one", service="fanbox", q="term", o=50, client=client)
    assert direct.data == direct_posts
    client.list_creator_posts.assert_awaited_with("fanbox", "one", query="term", offset=50)

    client.list_creator_posts.reset_mock()
    client.list_creator_posts.side_effect = [posts(1, prefix="one"), posts(1, prefix="two")]
    indirect = await search_creator_post(name="", service="fanbox", client=client)
    assert [item.id for item in indirect.data or []] == ["one-0", "two-0"]

    client.list_creators.side_effect = PawchiveHTTPError(response())
    propagated = await search_creator_post(name="Alice", client=client)
    assert not propagated

    client.list_creators.side_effect = None
    client.list_creator_posts.side_effect = ValidationError.from_exception_data("Query", [])
    invalid = await search_creator_post(id="one", service="fanbox", client=client)
    assert invalid.code == RetCodeEnum.GeneralFailure
