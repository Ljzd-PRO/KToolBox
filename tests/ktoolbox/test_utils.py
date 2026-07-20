from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import pytest

from ktoolbox.api.generated import Post
from ktoolbox.configuration import config
from ktoolbox.utils import (
    check_for_updates,
    dump_search,
    extract_external_links,
    generate_msg,
    logger_init,
    parse_webpage_url,
    uvloop_init,
)


def test_message_and_webpage_url_parsing() -> None:
    assert generate_msg() == ""
    assert generate_msg("Title") == "Title"
    assert generate_msg(key="value") == "key: value"
    assert generate_msg("Title", key="value") == "Title - key: value"
    assert parse_webpage_url("https://pawchive.pw/fanbox/user/6570768/post/1836570") == (
        "fanbox",
        "6570768",
        "1836570",
        None,
    )
    assert parse_webpage_url("https://pawchive.pw/fanbox/user/6570768/post/1836570/revision/7") == (
        "fanbox",
        "6570768",
        "1836570",
        "7",
    )
    assert parse_webpage_url("https://pawchive.pw/fanbox/user/6570768") == ("fanbox", "6570768", None, None)


@pytest.mark.asyncio
async def test_dump_search_is_structured_and_offline(tmp_path: Path) -> None:
    path = tmp_path / "search.json"
    await dump_search([Post(id="post", user="creator", service="fanbox")], path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["result"][0]["id"] == "post"
    assert "SearchResult" in data["type"]


def test_external_link_extraction() -> None:
    pattern = r"https?://files\.example\.test/[^\s]+"
    content = 'Use https://files.example.test/a.zip, and https://files.example.test/a.zip. <a href="x">'
    assert extract_external_links("", [pattern]) == set()
    assert extract_external_links(content, [pattern]) == {"https://files.example.test/a.zip"}
    assert extract_external_links(content) == set()


def test_uvloop_initialization_paths(monkeypatch) -> None:
    config.use_uvloop = False
    assert uvloop_init() is False

    config.use_uvloop = True
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "winloop", None)
    assert uvloop_init() is False

    policy = object()
    monkeypatch.setitem(sys.modules, "winloop", SimpleNamespace(EventLoopPolicy=lambda: policy))
    with patch("ktoolbox.utils.asyncio.set_event_loop_policy") as setter:
        assert uvloop_init() is True
    setter.assert_called_once_with(policy)

    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setitem(sys.modules, "uvloop", None)
    assert uvloop_init() is False
    monkeypatch.setitem(sys.modules, "uvloop", SimpleNamespace(EventLoopPolicy=lambda: policy))
    with patch("ktoolbox.utils.asyncio.set_event_loop_policy") as setter:
        assert uvloop_init() is True
    setter.assert_called_once_with(policy)


def test_logger_initialization(tmp_path: Path) -> None:
    config.logger.path = tmp_path / "logs"
    with patch("ktoolbox.utils.logger.remove") as remove, patch("ktoolbox.utils.logger.add") as add:
        logger_init(cli_use=True)
    remove.assert_called_once_with()
    assert add.call_count == 2
    assert config.logger.path.is_dir()

    with patch("ktoolbox.utils.logger.remove") as remove:
        logger_init(disable_stdout=True)
    remove.assert_called_once_with()


class FakeAsyncClient:
    responses: list[object] = []

    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs

    async def __aenter__(self) -> FakeAsyncClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def get(self, url: str) -> httpx.Response:
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        assert isinstance(item, httpx.Response)
        return item


def json_response(payload: object, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=payload, request=httpx.Request("GET", "https://example.test"))


@pytest.mark.asyncio
async def test_update_check_github_and_pypi_fallbacks() -> None:
    with patch("httpx.AsyncClient", FakeAsyncClient):
        FakeAsyncClient.responses = [json_response({"tag_name": "v99.0.0", "html_url": "https://release.test"})]
        await check_for_updates()

        FakeAsyncClient.responses = [json_response({"tag_name": "v1.0.0", "html_url": "https://release.test"})]
        await check_for_updates()

        FakeAsyncClient.responses = [
            httpx.ConnectError("offline"),
            json_response({"info": {"version": "99.0.0"}}),
        ]
        await check_for_updates()

        FakeAsyncClient.responses = [json_response({}, 500), json_response({"info": {"version": "1.0.0"}})]
        await check_for_updates()

        FakeAsyncClient.responses = [httpx.ConnectError("offline"), httpx.ConnectError("offline")]
        await check_for_updates()
