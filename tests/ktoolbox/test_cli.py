import os
import tempfile
from collections import OrderedDict
from pathlib import Path
from typing import NamedTuple

import pytest
from allpairspy import AllPairs
from pydantic import ValidationError

from ktoolbox import __version__
from ktoolbox.api.model import Creator, Post
from ktoolbox.cli import KToolBoxCli
from ktoolbox.configuration import config
from ktoolbox._enum import TextEnum, DataStorageNameEnum
from ktoolbox.model import SearchResult
from ktoolbox.utils import generate_msg
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
        validate_result = SearchResult.parse_raw(json_text)
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


@pytest.mark.asyncio
async def test_download_post():
    # Test invalid input
    invalid = await KToolBoxCli.download_post(url="")
    assert invalid == generate_msg(
        TextEnum.MissingParams.value,
        use_at_lease_one=[
            ["url"],
            ["service", "creator_id", "post_id"]
        ]
    )

    # Test post.json existed or not
    with tempfile.TemporaryDirectory() as td:
        dir_path = Path(td)
        url_only = await KToolBoxCli.download_post(
            url="https://kemono.su/fanbox/user/9016/post/6622968",
            path=dir_path
        )
        assert url_only is None
        assert (dir_new := next(dir_path.iterdir(), None)) is not None
        assert (dir_new / DataStorageNameEnum.PostData.value).is_file()

    # Test manually input post information and `dump_post_data`
    no_url_and_no_dump = await KToolBoxCli.download_post(
        service="fanbox",
        creator_id="9016",
        post_id="6622968",
        dump_post_data=False
    )
    assert no_url_and_no_dump is None

    # Test `post_id_as_path`
    with tempfile.TemporaryDirectory() as td:
        dir_path = Path(td)
        config.job.post_id_as_path = True
        await KToolBoxCli.download_post(
            url="https://kemono.su/fanbox/user/9016/post/6622968",
            path=dir_path
        )
        assert (dir_path / "6622968").is_dir()
        config.job.post_id_as_path = False


@pytest.mark.asyncio
async def test_sync_creator():
    # noinspection SpellCheckingInspection
    service = "fanbox"
    creator_id = "76712"
    creator_url = f"https://kemono.su/{service}/user/{creator_id}"

    # Test invalid params input
    invalid = await KToolBoxCli.sync_creator(url="")
    assert invalid == generate_msg(
        TextEnum.MissingParams.value,
        use_at_lease_one=[
            ["url"],
            ["service", "creator_id"]
        ]
    )

    with tempfile.TemporaryDirectory() as td:
        dir_path = Path(td)

        # Test url only
        url_only = await KToolBoxCli.sync_creator(
            url=creator_url,
            path=dir_path
        )
        assert url_only is None

    # Test `mix_posts`
    with tempfile.TemporaryDirectory() as td:
        dir_path = Path(td)
        await KToolBoxCli.sync_creator(
            url=creator_url,
            path=dir_path,
            mix_posts=True
        )
        assert (dir_new := next(dir_path.iterdir(), None)) is not None
        sub_dirs = list(filter(lambda x: x.is_dir(), dir_new.iterdir()))
        assert len(sub_dirs) == 0

    # Test `start_time`, `end_time`

    await KToolBoxCli.sync_creator(
        url=creator_url,
        start_time="2022-06-05"
    )

    with tempfile.TemporaryDirectory() as td:
        dir_path = Path(td)
        await KToolBoxCli.sync_creator(
            url=creator_url,
            path=dir_path,
            start_time="2022-06-05",
            end_time="2022-06-24"
        )
        assert (dir_new := next(dir_path.iterdir(), None)) is not None
        posts = list(filter(lambda x: x.is_dir(), dir_new.iterdir()))
        assert len(posts) == 4

    with tempfile.TemporaryDirectory() as td:
        dir_path = Path(td)
        await KToolBoxCli.sync_creator(
            url=creator_url,
            path=dir_path,
            end_time="2022-06-23"
        )
        assert (dir_new := next(dir_path.iterdir(), None)) is not None
        posts = list(filter(lambda x: x.is_dir(), dir_new.iterdir()))
        assert len(posts) == 3
