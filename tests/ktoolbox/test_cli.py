import os
import tempfile
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import NamedTuple
from unittest.mock import AsyncMock, patch

import pytest
from allpairspy import AllPairs
from pydantic import ValidationError

from ktoolbox import __version__
from ktoolbox._enum import TextEnum, DataStorageNameEnum, RetCodeEnum
from ktoolbox.action import ActionRet
from ktoolbox.api import APIRet
from ktoolbox.api.model import Attachment, Creator, File, Post
from ktoolbox.cli import KToolBoxCli
from ktoolbox.configuration import config, JobConfiguration
from ktoolbox.model import SearchResult
from ktoolbox.utils import generate_msg
from tests.utils import settings


NOW = datetime(2025, 1, 1)
POST_PUBLISHED = datetime(2025, 3, 27)


def _creator(creator_id: str, name: str, service: str) -> Creator:
    return Creator(
        id=creator_id,
        name=name,
        service=service,
        favorited=0,
        indexed=NOW,
        updated=NOW,
    )


MOCK_CREATORS = [
    _creator("49494721", "soso", "fanbox"),
    _creator("9016", "bginga", "patreon"),
    _creator("24164271", "Mock Creator", "fanbox"),
]


def _mock_post(
        post_id: str = "9492291",
        creator_id: str = "3316400",
        service: str = "fanbox",
        title: str = "Mock Post",
) -> Post:
    return Post(
        id=post_id,
        user=creator_id,
        service=service,
        title=title,
        content="Mock content",
        published=POST_PUBLISHED,
        added=POST_PUBLISHED,
        edited=POST_PUBLISHED,
        attachments=[
            Attachment(name="image.jpg", path="/data/12/34/image.jpg"),
        ],
        file=File(name="cover.jpg", path="/data/56/78/cover.jpg"),
    )


MOCK_POSTS = [
    _mock_post(title="Monthly image pack"),
    _mock_post(post_id="6434459", title="Sketch archive"),
]


def _post_response(post: Post = None, props=None) -> APIRet:
    return APIRet(data=SimpleNamespace(post=post or _mock_post(), props=props))


def _filter_creators(creator_id: str = None, name: str = None, service: str = None):
    def matches(creator: Creator):
        if creator_id is not None and creator.id != creator_id:
            return False
        if name is not None and name not in creator.name:
            return False
        if service is not None and creator.service != service:
            return False
        return True

    return list(filter(matches, MOCK_CREATORS))


async def _search_creator_side_effect(id: str = None, name: str = None, service: str = None):
    return ActionRet(data=iter(_filter_creators(creator_id=id, name=name, service=service)))


async def _search_creator_post_side_effect(
        id: str = None,
        name: str = None,
        service: str = None,
        q: str = None,
        o: int = None
):
    creator_matches = _filter_creators(creator_id=id, name=name, service=service)
    if service == "KToolBox" or (any([id, name, service]) and not creator_matches):
        return ActionRet(data=[])

    posts = MOCK_POSTS
    if q:
        posts = [post for post in posts if q.lower() in (post.title or "").lower()]
    if o:
        posts = posts[o:]
    return ActionRet(data=posts)


@pytest.fixture(autouse=True)
def isolate_cli_state():
    original_job = config.job
    config.job = JobConfiguration()
    KToolBoxCli._update_checked = False
    with patch("ktoolbox.cli.check_for_updates", new_callable=AsyncMock) as mock_update_check:
        yield mock_update_check
    KToolBoxCli._update_checked = False
    config.job = original_job


@pytest.mark.asyncio
async def test_version(isolate_cli_state):
    assert await KToolBoxCli.version() == __version__
    isolate_cli_state.assert_awaited_once()


@pytest.mark.asyncio
async def test_site_version():
    mock_version = "a" * settings.cli_conf.commit_hash_length
    with patch("ktoolbox.cli.get_app_version", new_callable=AsyncMock) as mock_get_app_version:
        mock_get_app_version.return_value = APIRet(data=mock_version)

        assert len(await KToolBoxCli.site_version()) == settings.cli_conf.commit_hash_length
        mock_get_app_version.assert_awaited_once_with()


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
    with patch(
            "ktoolbox.cli.search_creator_action",
            new_callable=AsyncMock,
            side_effect=_search_creator_side_effect
    ) as mock_search_creator:
        ret = await KToolBoxCli.search_creator(**parameters._asdict())

    if len(ret) == 1:
        assert isinstance(ret[0], Creator)
    elif isinstance(ret, str):
        assert ret == settings.cli_conf.search_empty_text
    else:
        assert all(isinstance(creator, Creator) for creator in ret)
    if dump := parameters.__getattribute__("dump"):
        await _test_dump(dump)
    mock_search_creator.assert_awaited_once_with(
        id=parameters.id,
        name=parameters.name,
        service=parameters.service,
    )


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
    with patch(
            "ktoolbox.cli.search_creator_post_action",
            new_callable=AsyncMock,
            side_effect=_search_creator_post_side_effect
    ) as mock_search_creator_post:
        ret = await KToolBoxCli.search_creator_post(**parameters._asdict())

    if len(ret) == 1:
        assert isinstance(ret[0], Post)
    elif isinstance(ret, str):
        assert ret == settings.cli_conf.search_empty_text
    else:
        assert all(isinstance(post, Post) for post in ret)
    if dump := parameters.__getattribute__("dump"):
        await _test_dump(dump)
    mock_search_creator_post.assert_awaited_once_with(
        id=parameters.id,
        name=parameters.name,
        service=parameters.service,
        q=parameters.q,
        o=parameters.o,
    )


# noinspection SpellCheckingInspection
@pytest.mark.asyncio
async def test_get_post():
    failure = APIRet(code=RetCodeEnum.NetWorkError, message="mocked API failure")
    post = _mock_post(post_id="6434459")

    with patch("ktoolbox.cli.get_post_api", new_callable=AsyncMock) as mock_get_post:
        mock_get_post.side_effect = [failure, _post_response(post)]

        invalid = await KToolBoxCli.get_post("", "", "")
        assert invalid == "mocked API failure"

        normal = await KToolBoxCli.get_post("fanbox", "3316400", "6434459")
        assert normal == post


@pytest.mark.asyncio
async def test_download_post():
    with patch("ktoolbox.cli.get_post_api", new_callable=AsyncMock) as mock_get_post, \
            patch("ktoolbox.cli.JobRunner") as mock_job_runner:
        mock_get_post.return_value = _post_response()
        mock_job_runner.return_value.start = AsyncMock(return_value=0)

        # Test invalid input
        with tempfile.TemporaryDirectory() as td:
            dir_path = Path(td)
            invalid = await KToolBoxCli.download_post(url="", path=dir_path)
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
                url="https://kemono.cr/fanbox/user/3316400/post/9492291",
                path=dir_path
            )
            assert url_only is None
            assert (dir_new := next(dir_path.iterdir(), None)) is not None
            assert (dir_new / DataStorageNameEnum.PostData.value).is_file()

        # Test manually input post information and `dump_post_data`
        with tempfile.TemporaryDirectory() as td:
            dir_path = Path(td)
            no_url_and_no_dump = await KToolBoxCli.download_post(
                service="fanbox",
                creator_id="3316400",
                post_id="9492291",
                path=dir_path,
                dump_post_data=False
            )
            assert no_url_and_no_dump is None
            assert not list(dir_path.rglob(DataStorageNameEnum.PostData.value))

        # Test `post_dirname_format`
        with tempfile.TemporaryDirectory() as td:
            dir_path = Path(td)
            config.job.post_dirname_format = "[{published}]{id}"
            await KToolBoxCli.download_post(
                url="https://kemono.cr/fanbox/user/3316400/post/9492291",
                path=dir_path
            )
            assert (dir_path / "[2025-03-27]9492291").is_dir()

    assert mock_get_post.await_count == 3
    assert mock_job_runner.call_count == 3
    assert mock_job_runner.return_value.start.await_count == 3


@pytest.mark.asyncio
async def test_sync_creator():
    # noinspection SpellCheckingInspection
    service = "fanbox"
    creator_id = "24164271"
    creator_url = f"https://kemono.cr/{service}/user/{creator_id}"
    creator_name = "Mock Creator"

    async def sync_search_creator_side_effect(id: str = None, name: str = None, service: str = None):
        return ActionRet(data=iter([_creator(id, creator_name, service)]))

    with patch(
            "ktoolbox.cli.search_creator_action",
            new_callable=AsyncMock,
            side_effect=sync_search_creator_side_effect
    ) as mock_search_creator, \
            patch("ktoolbox.cli.create_job_from_creator", new_callable=AsyncMock) as mock_create_jobs, \
            patch("ktoolbox.cli.JobRunner") as mock_job_runner:
        mock_create_jobs.return_value = ActionRet(data=[])
        mock_job_runner.return_value.start = AsyncMock(return_value=0)

        # Test invalid params input
        with tempfile.TemporaryDirectory() as td:
            dir_path = Path(td)
            invalid = await KToolBoxCli.sync_creator(url="", path=dir_path)
            assert invalid == generate_msg(
                TextEnum.MissingParams.value,
                use_at_lease_one=[
                    ["url"],
                    ["service", "creator_id"]
                ]
            )

        # Test url only
        with tempfile.TemporaryDirectory() as td:
            dir_path = Path(td)
            url_only = await KToolBoxCli.sync_creator(
                url=creator_url,
                path=dir_path,
                length=3
            )
            assert url_only is None
            assert (dir_path / creator_name).is_dir()
            kwargs = mock_create_jobs.await_args.kwargs
            assert kwargs["service"] == service
            assert kwargs["creator_id"] == creator_id
            assert kwargs["path"] == dir_path / creator_name
            assert kwargs["all_pages"] is False
            assert kwargs["length"] == 3

        # Test `mix_posts`
        with tempfile.TemporaryDirectory() as td:
            dir_path = Path(td)
            await KToolBoxCli.sync_creator(
                url=creator_url,
                path=dir_path,
                length=3,
                mix_posts=True
            )
            kwargs = mock_create_jobs.await_args.kwargs
            assert kwargs["mix_posts"] is True

        # Test `start_time`, `end_time`
        with tempfile.TemporaryDirectory() as td:
            dir_path = Path(td)
            await KToolBoxCli.sync_creator(
                url=creator_url,
                path=dir_path,
                start_time="2025-07-25",
                end_time="2025-08-10"
            )
            kwargs = mock_create_jobs.await_args.kwargs
            assert kwargs["start_time"] == datetime(2025, 7, 25)
            assert kwargs["end_time"] == datetime(2025, 8, 10)
            assert kwargs["all_pages"] is True

    assert mock_search_creator.await_count == 3
    assert mock_create_jobs.await_count == 3
    assert mock_job_runner.call_count == 3
    assert mock_job_runner.return_value.start.await_count == 3
