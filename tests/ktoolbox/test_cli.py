import os
from collections import OrderedDict
from pathlib import Path
from typing import NamedTuple

import pytest
from allpairspy import AllPairs
from pydantic import ValidationError

from ktoolbox import __version__
from ktoolbox.api.model import Creator, Post
from ktoolbox.cli import KToolBoxCli
from ktoolbox.model import SearchResult
from tests.utils import settings


@pytest.mark.asyncio
async def test_version():
    assert await KToolBoxCli.version() == __version__


@pytest.mark.asyncio
async def test_site_version():
    assert len(await KToolBoxCli.site_version()) == settings.cli_conf.commit_hash_length


# noinspection SpellCheckingInspection
search_creator_cases = OrderedDict({
    "id": ["49494721", "9016", None],
    "name": ["soso", "bginga", None],
    "service": ["fanbox", "patreon", "KToolBox", None],
    "dump": [None, "./test_search_creator.json"]
})


async def _test_dump(dump: Path):
    with open(dump, encoding="utf-8") as f:
        json_text = f.read()
    os.remove(str(dump))
    try:
        validate_result = SearchResult.model_validate_json(json_text)
    except ValidationError as e:
        validate_result = e
    assert isinstance(validate_result, SearchResult)


@pytest.mark.asyncio
@pytest.mark.parametrize("parameters", AllPairs(search_creator_cases), ids=str)
async def test_search_creator(parameters: NamedTuple):
    ret = await KToolBoxCli.search_creator(**parameters._asdict())
    if len(ret) == 1:
        assert isinstance(ret[0], Creator)
    elif isinstance(ret, str):
        assert ret == settings.cli_conf.search_empty_text
    else:
        assert all(isinstance(creator, Creator) for creator in ret)
    if dump := parameters.__getattribute__("dump"):
        await _test_dump(dump)


# noinspection SpellCheckingInspection
search_creator_post_cases = OrderedDict({
    "id": ["49494721", "9016", None],
    "name": ["soso", "bginga", None],
    "service": ["fanbox", "patreon", "KToolBox", None],
    "q": ["月", None],
    "o": [50, None],
    "dump": ["./test_search_creator_post.json", None]
})


@pytest.mark.asyncio
@pytest.mark.parametrize("parameters", AllPairs(search_creator_post_cases), ids=str)
async def test_search_creator_post(parameters: NamedTuple):
    ret = await KToolBoxCli.search_creator_post(**parameters._asdict())
    if len(ret) == 1:
        assert isinstance(ret[0], Post)
    elif isinstance(ret, str):
        assert ret == settings.cli_conf.search_empty_text
    else:
        assert all(isinstance(post, Post) for post in ret)
    if dump := parameters.__getattribute__("dump"):
        await _test_dump(dump)


# noinspection SpellCheckingInspection
@pytest.mark.asyncio
async def test_get_post():
    invalid = await KToolBoxCli.get_post("", "", "")
    assert isinstance(invalid, str)

    normal = await KToolBoxCli.get_post("fanbox", "3316400", "6434459")
    assert isinstance(normal, Post)
