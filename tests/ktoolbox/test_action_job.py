from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from ktoolbox._enum import PostFileTypeEnum, RetCodeEnum
from ktoolbox.action.fetch import FetchInterruptError
from ktoolbox.action.job import create_job_from_creator, create_job_from_post
from ktoolbox.api.errors import PawchiveHTTPError, PawchiveNotFoundError
from ktoolbox.api.generated import FileReference, Post, Revision
from ktoolbox.blocker import BlockerEngine, BlockerSpec
from ktoolbox.configuration import config
from ktoolbox.job import Job


def post(
    post_id: str = "post",
    *,
    title: str = "Title",
    content: str | None = None,
    substring: str | None = None,
    published: datetime | None = None,
) -> Post:
    return Post(
        id=post_id,
        user="creator",
        service="fanbox",
        title=title,
        content=content,
        substring=substring,
        published=published,
    )


def api_error(status: int = 500) -> PawchiveHTTPError:
    request = httpx.Request("GET", "https://example.test/resource")
    response = httpx.Response(status, request=request)
    if status == 404:
        return PawchiveNotFoundError(response)
    return PawchiveHTTPError(response)


@pytest.mark.asyncio
async def test_create_post_jobs_filters_names_and_extracts_content(tmp_path: Path) -> None:
    config.job.sequential_filename = True
    config.job.sequential_filename_excludes = {".zip"}
    config.job.block_list = {"blocked*"}
    config.job.extract_content = True
    config.job.extract_external_links = True
    config.job.extract_content_images = True
    config.job.external_link_patterns = [r"https?://files\.example\.test/[^\s<]+"]

    item = post(
        content=(
            "Download https://files.example.test/archive.zip\n"
            '<img src="/content/one.png"><img src="https://cdn.example.test/two.jpg">'
            '<img src="//cdn.example.test/skip.png"><img src="data:image/png;base64,x"><img src="">'
        )
    )
    item.attachments = [
        FileReference(name="first.jpg", path="/aa/first.jpg"),
        FileReference(name="archive.zip", path="/aa/archive.zip"),
        FileReference(name=None, path="/aa/fallback.png"),
        FileReference(name="blocked.txt", path="/aa/blocked.txt"),
        FileReference(name="missing.txt", path=None),
    ]
    item.file = FileReference(name="cover.jpg", path="/aa/cover.jpg")

    jobs = await create_job_from_post(item, tmp_path / "post")

    assert [job.alt_filename for job in jobs] == [
        "1.jpg",
        "archive.zip",
        "2.png",
        "post_cover.jpg",
        "3.png",
        "4.jpg",
    ]
    assert [job.type for job in jobs].count(PostFileTypeEnum.File) == 1
    assert all(job.post == item for job in jobs[:4])
    assert (tmp_path / "post/post.json").is_file()
    assert (tmp_path / "post/content.txt").read_text(encoding="utf-8") == item.content
    assert (tmp_path / "post/external_links.txt").read_text(encoding="utf-8").strip() == (
        "https://files.example.test/archive.zip"
    )


@pytest.mark.asyncio
async def test_create_post_jobs_respects_allow_list_and_flat_mode(tmp_path: Path) -> None:
    config.job.allow_list = {"*.png"}
    item = post(content="<img src='/one.png'>")
    item.attachments = [
        FileReference(name="keep.png", path="/keep.png"),
        FileReference(name="skip.zip", path="/skip.zip"),
    ]
    item.file = FileReference(name="cover.jpg", path="/cover.jpg")

    config.job.extract_content_images = True
    jobs = await create_job_from_post(item, tmp_path, post_dir=False, dump_post_data=False)
    assert [job.alt_filename for job in jobs] == ["keep.png"]
    assert jobs[0].path == tmp_path
    assert not (tmp_path / "post.json").exists()


@pytest.mark.asyncio
async def test_create_post_jobs_fetches_missing_post_and_revision_content(tmp_path: Path) -> None:
    config.job.download_attachments = False
    config.job.download_file = False
    config.job.extract_content = True
    preview = post(substring="preview")
    full = post(content="full content")
    client = SimpleNamespace(get_post=AsyncMock(return_value=full), list_post_revisions=AsyncMock())

    assert await create_job_from_post(preview, tmp_path / "post", client=client) == []
    assert (tmp_path / "post/content.txt").read_text() == "full content"
    client.get_post.assert_awaited_once_with("fanbox", "creator", "post")

    revision = Revision(
        id="post",
        user="creator",
        service="fanbox",
        title="Revision",
        substring="preview",
        revision_id=7,
    )
    full_revision = revision.model_copy(update={"content": "revision content"})
    client.list_post_revisions.return_value = [full_revision]
    await create_job_from_post(revision, tmp_path / "revision", client=client)
    assert (tmp_path / "revision/content.txt").read_text() == "revision content"


@pytest.mark.asyncio
async def test_create_post_jobs_wraps_content_fetch_failures(tmp_path: Path) -> None:
    config.job.download_attachments = False
    config.job.download_file = False
    config.job.extract_content = True
    preview = post(substring="preview")
    client = SimpleNamespace(
        get_post=AsyncMock(side_effect=api_error()), list_post_revisions=AsyncMock(return_value=[])
    )

    with pytest.raises(FetchInterruptError):
        await create_job_from_post(preview, tmp_path / "post", client=client)

    revision = Revision(
        id="post",
        user="creator",
        service="fanbox",
        title="Revision",
        substring="preview",
        revision_id=7,
    )
    with pytest.raises(FetchInterruptError, match="Revision 7"):
        await create_job_from_post(revision, tmp_path / "revision", client=client)


def page_source(*batches: list[Post], error: Exception | None = None, calls: list[dict[str, object]] | None = None):
    async def source(**kwargs: object) -> AsyncIterator[list[Post]]:
        if calls is not None:
            calls.append(kwargs)
        if error is not None:
            raise FetchInterruptError(error)
        for batch in batches:
            yield batch

    return source


@pytest.mark.asyncio
async def test_create_creator_jobs_slices_filters_saves_indices_and_revisions(tmp_path: Path) -> None:
    first = post("first", title="Keep Alpha", published=datetime(2025, 1, 1))
    second = post("second", title="Keep Block", published=datetime(2025, 1, 2))
    third = post("third", title="Old Alpha", published=datetime(2023, 1, 1))
    revision = Revision(id="first", user="creator", service="fanbox", title="Revision", revision_id=1)
    client = SimpleNamespace(list_post_revisions=AsyncMock(return_value=[revision]))
    generated_job = Job(path=tmp_path, server_path="/file")
    calls: list[dict[str, object]] = []

    config.job.include_revisions = True
    config.job.extract_content = True
    with (
        patch("ktoolbox.action.job.fetch_creator_posts", page_source([first, second, third], calls=calls)),
        patch(
            "ktoolbox.action.job.create_job_from_post", new_callable=AsyncMock, return_value=[generated_job]
        ) as create,
    ):
        result = await create_job_from_creator(
            "fanbox",
            "creator",
            tmp_path,
            offset=0,
            length=3,
            save_creator_indices=True,
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2026, 1, 1),
            keywords={"alpha"},
            keywords_exclude={"block"},
            client=client,
        )

    assert result.data == [generated_job, generated_job]
    assert calls[0]["offset"] == 0
    assert create.await_count == 2
    client.list_post_revisions.assert_awaited_once_with("fanbox", "creator", "first")
    indices = json.loads((tmp_path / "creator-indices.ktoolbox").read_text())
    assert set(indices["posts"]) == {"first"}


@pytest.mark.asyncio
async def test_create_creator_jobs_offset_all_pages_mix_and_owned_scope(tmp_path: Path) -> None:
    batch = [post("zero"), post("selected")]
    client = SimpleNamespace(list_post_revisions=AsyncMock())
    generated_job = Job(path=tmp_path, server_path="/file")

    class Scope:
        async def __aenter__(self) -> object:
            return client

        async def __aexit__(self, *args: object) -> None:
            return None

    calls: list[dict[str, object]] = []
    with (
        patch("ktoolbox.action.job.pawchive_client_scope", return_value=Scope()),
        patch("ktoolbox.action.job.fetch_creator_posts", page_source(batch, calls=calls)),
        patch(
            "ktoolbox.action.job.create_job_from_post", new_callable=AsyncMock, return_value=[generated_job]
        ) as create,
    ):
        result = await create_job_from_creator(
            "fanbox",
            "creator",
            tmp_path,
            all_pages=True,
            offset=51,
            length=None,
            save_creator_indices=True,
            mix_posts=True,
            start_time=None,
            end_time=None,
            client=None,
        )

    assert result.data == [generated_job]
    assert calls[0]["offset"] == 50
    assert create.await_args.kwargs["post"] == batch[1]
    assert create.await_args.kwargs["post_path"] == tmp_path
    assert create.await_args.kwargs["post_dir"] is False
    assert not (tmp_path / "creator-indices.ktoolbox").exists()


@pytest.mark.asyncio
async def test_create_creator_jobs_blocks_before_generation_and_indices(tmp_path: Path) -> None:
    client = SimpleNamespace(list_post_revisions=AsyncMock())
    blocker = BlockerSpec(
        id="daily-life",
        options={
            "rule": {
                "kind": "group",
                "mode": "any",
                "conditions": [
                    {
                        "kind": "field",
                        "field": "content",
                        "operator": "contains",
                        "values": ["daily"],
                    }
                ],
            }
        },
    )
    with (
        patch("ktoolbox.action.job.fetch_creator_posts", page_source([post(content="Daily notes")])),
        patch("ktoolbox.action.job.create_job_from_post", new_callable=AsyncMock) as create,
    ):
        result = await create_job_from_creator(
            "fanbox",
            "creator",
            tmp_path,
            length=1,
            save_creator_indices=True,
            start_time=None,
            end_time=None,
            blocker_engine=BlockerEngine.from_specs([blocker]),
            client=client,
        )

    assert result.data == []
    create.assert_not_awaited()
    indices = json.loads((tmp_path / "creator-indices.ktoolbox").read_text())
    assert indices["posts"] == {}


@pytest.mark.asyncio
async def test_create_creator_jobs_maps_fetch_and_generation_failures(tmp_path: Path) -> None:
    failure = api_error()
    client = SimpleNamespace(list_post_revisions=AsyncMock())

    with patch("ktoolbox.action.job.fetch_creator_posts", page_source(error=failure)):
        result = await create_job_from_creator(
            "fanbox",
            "creator",
            tmp_path,
            start_time=None,
            end_time=None,
            client=client,
        )
    assert result.code == RetCodeEnum.GeneralFailure

    with (
        patch("ktoolbox.action.job.fetch_creator_posts", page_source([post()])),
        patch(
            "ktoolbox.action.job.create_job_from_post",
            new_callable=AsyncMock,
            side_effect=FetchInterruptError(failure),
        ),
    ):
        result = await create_job_from_creator(
            "fanbox",
            "creator",
            tmp_path,
            start_time=None,
            end_time=None,
            client=client,
        )
    assert result.code == RetCodeEnum.GeneralFailure


@pytest.mark.asyncio
@pytest.mark.parametrize("revision_error", [api_error(404), api_error()])
async def test_create_creator_jobs_tolerates_revision_api_failures(tmp_path: Path, revision_error: Exception) -> None:
    config.job.include_revisions = True
    client = SimpleNamespace(list_post_revisions=AsyncMock(side_effect=revision_error))
    with (
        patch("ktoolbox.action.job.fetch_creator_posts", page_source([post()])),
        patch("ktoolbox.action.job.create_job_from_post", new_callable=AsyncMock, return_value=[]),
    ):
        result = await create_job_from_creator(
            "fanbox",
            "creator",
            tmp_path,
            start_time=None,
            end_time=None,
            client=client,
        )
    assert result


@pytest.mark.asyncio
async def test_create_creator_jobs_maps_revision_generation_failure(tmp_path: Path) -> None:
    config.job.include_revisions = True
    failure = api_error()
    revision = Revision(id="post", user="creator", service="fanbox", title="Revision", revision_id=1)
    client = SimpleNamespace(list_post_revisions=AsyncMock(return_value=[revision]))
    create = AsyncMock(side_effect=[[], FetchInterruptError(failure)])
    with (
        patch("ktoolbox.action.job.fetch_creator_posts", page_source([post()])),
        patch("ktoolbox.action.job.create_job_from_post", create),
    ):
        result = await create_job_from_creator(
            "fanbox",
            "creator",
            tmp_path,
            start_time=None,
            end_time=None,
            client=client,
        )
    assert result.code == RetCodeEnum.GeneralFailure
