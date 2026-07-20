from __future__ import annotations

from unittest.mock import patch

import pytest

from ktoolbox.api.client import PawchiveClient
from ktoolbox.api.utils import (
    SEARCH_STEP,
    create_pawchive_client,
    get_creator_banner,
    get_creator_icon,
    get_file_url,
    pawchive_client_scope,
)
from ktoolbox.configuration import config


def test_pawchive_urls_follow_configuration_and_escape_segments() -> None:
    config.api.scheme = "http"
    config.api.statics_netloc = "static.example.test"
    config.downloader.scheme = "https"
    config.downloader.files_netloc = "files.example.test"
    config.downloader.file_path_prefix = "/data/"

    assert SEARCH_STEP == 50
    assert get_creator_icon("creator id", "fan/box") == "http://static.example.test/icons/fan%2Fbox/creator%20id"
    assert get_creator_banner("creator id", "fan/box") == "http://static.example.test/banners/fan%2Fbox/creator%20id"
    assert get_file_url("/aa/file.jpg?download=1") == "https://files.example.test/data/aa/file.jpg?download=1"
    assert get_file_url("/data/aa/file.jpg") == "https://files.example.test/data/aa/file.jpg"
    assert get_file_url("/data") == "https://files.example.test/data"


@pytest.mark.asyncio
async def test_client_factory_and_scopes() -> None:
    config.api.scheme = "https"
    config.api.netloc = "example.test"
    config.api.path = "/custom/"
    config.api.timeout = 9
    config.api.retry_times = 2
    config.api.retry_interval = 0.5

    client = create_pawchive_client()
    assert isinstance(client, PawchiveClient)
    assert str(client._base_url) == "https://example.test/custom"
    assert client._timeout == 9
    await client.aclose()

    injected = PawchiveClient(base_url="https://example.test")
    async with pawchive_client_scope(injected) as scoped:
        assert scoped is injected
    assert not injected._closed
    await injected.aclose()

    events: list[str] = []

    class OwnedScope:
        async def __aenter__(self) -> object:
            events.append("enter")
            return self

        async def __aexit__(self, *args: object) -> None:
            events.append("exit")

    with patch("ktoolbox.api.utils.create_pawchive_client", return_value=OwnedScope()):
        async with pawchive_client_scope(None) as scoped:
            assert isinstance(scoped, OwnedScope)
    assert events == ["enter", "exit"]
