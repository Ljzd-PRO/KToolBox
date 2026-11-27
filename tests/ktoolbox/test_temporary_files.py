import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import httpx
import pytest

from ktoolbox.api.client import PawchiveClient
from ktoolbox.api.generated import FileReference, Post, Revision
from ktoolbox.api.temporary_files import active_temporary_url, validated_temporary_url
from ktoolbox.job.temporary import TemporaryFile, TemporaryFileSource, TemporaryFileUnavailable


@pytest.mark.parametrize(
    "url",
    [
        "https://t2.pawchive.pw/d/fixture/demo.zip?signed=example%2Fvalue&limit=123",
        "https://t1.pawchive.pw/f/fixture/demo.zip?signed=example",
    ],
)
def test_temporary_download_url_preserves_signature(url: str) -> None:
    assert validated_temporary_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "https://t2.pawchive.pw/v/fixture/demo.zip",
        "http://t2.pawchive.pw/d/demo.zip",
        "https://example.test/d/demo.zip",
        "https://t2.pawchive.pw.example.test/d/demo.zip",
        "https://t2.pawchive.pw:1234/d/demo.zip",
        "https://example.test@t2.pawchive.pw/d/demo.zip",
        "https://t2.pawchive.pw/d/%2e%2e/data/demo.zip",
        "https://t2.pawchive.pw/d/demo.zip#fragment",
        "//t2.pawchive.pw/d/demo.zip",
    ],
)
def test_temporary_download_url_rejects_untrusted_destinations(url: str) -> None:
    assert validated_temporary_url(url) is None


async def test_file_details_protect_temporary_fields_including_direct_paths() -> None:
    def transport(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "42",
                "user": "creator",
                "service": "fanbox",
                "file": {"name": "normal.png", "path": "/aa/bb/normal.png"},
                "attachments": [
                    {"name": "pending.zip", "deferred": True},
                    {
                        "name": "available.zip",
                        "deferred": True,
                        "temp_download_url": "https://t3.pawchive.pw/d/fixture/demo.zip?signed=secret-fixture",
                        "temp_url": "https://t3.pawchive.pw/v/fixture/demo.zip?preview=secret-fixture",
                        "temp_expires": "2026-12-01T12:00:00Z",
                    },
                    {"name": "direct.zip", "path": "https://t1.pawchive.pw/f/fixture/demo.zip?signed=secret-fixture"},
                ],
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        async with PawchiveClient(http_client=http) as api:
            post = await api.get_post("fanbox", "creator", "42")
    assert post.file and post.file.path == "/aa/bb/normal.png"
    assert post.attachments is not None
    pending, available, direct = post.attachments
    before = datetime(2026, 12, 1, tzinfo=timezone.utc)
    after = datetime(2026, 12, 2, tzinfo=timezone.utc)
    assert pending.deferred and pending.path is None and active_temporary_url(pending, before) is None
    assert active_temporary_url(available, before) is not None
    assert active_temporary_url(available, after) is None
    assert direct.deferred and direct.path is None
    assert active_temporary_url(direct, before) is not None
    for rendered in (repr(post), post.model_dump_json()):
        assert "secret-fixture" not in rendered
        assert "temp_download_url" not in rendered
        assert "temp_url" not in rendered
    preview = FileReference.model_validate(
        {
            "preview_only": True,
            "temp_download_url": "https://t2.pawchive.pw/d/fixture/demo.zip",
        }
    )
    assert active_temporary_url(preview, before) is None


async def test_deferred_files_share_detail_lookup_and_do_not_guess_duplicate_names() -> None:
    identity = {"service": "fanbox", "user": "creator", "id": "42"}
    pending = [
        FileReference(id="first", name="same.zip", deferred=True),
        FileReference(id="second", name="same.zip", deferred=True),
        FileReference(name="same.zip", deferred=True),
    ]
    first_url = "https://t2.pawchive.pw/d/fixture/first.zip"
    second_url = "https://t2.pawchive.pw/d/fixture/second.zip"
    detail = Post(
        **identity,
        attachments=[
            _file_with_url("second", "same.zip", second_url),
            _file_with_url("first", "renamed.zip", first_url),
            _file_with_url("third", "same.zip", second_url),
        ],
    )
    api = AsyncMock(spec=PawchiveClient)
    api.get_post.return_value = detail
    source = TemporaryFileSource(Post(**identity, attachments=pending))
    first, second, ambiguous = (TemporaryFile(source, file, primary=False) for file in pending)

    assert await asyncio.gather(source.resolve(first, api), source.resolve(second, api)) == [first_url, second_url]
    with pytest.raises(TemporaryFileUnavailable):
        await source.resolve(ambiguous, api)
    api.get_post.assert_awaited_once_with("fanbox", "creator", "42")


async def test_expired_primary_uses_only_the_requested_revision() -> None:
    old_url = "https://t2.pawchive.pw/f/fixture/original.zip?signed=old"
    new_url = "https://t2.pawchive.pw/d/fixture/original.zip?signed=new"
    seed = _file_with_url("main", "original.zip", old_url)
    seed.temp_expires = datetime(2000, 1, 1, tzinfo=timezone.utc)
    identity = {"service": "fanbox", "user": "creator", "id": "42"}
    revision = Revision(**identity, revision_id=1, file=seed)
    source = TemporaryFileSource(revision)
    file = TemporaryFile(source, seed, primary=True)
    api = AsyncMock(spec=PawchiveClient)
    api.list_post_revisions.return_value = [
        Revision(**identity, revision_id=2, file=_file_with_url("main", "original.zip", old_url)),
        Revision(**identity, revision_id=1, file=_file_with_url("main", "original.zip", new_url)),
    ]

    assert await source.resolve(file, api) == new_url
    api.list_post_revisions.assert_awaited_once_with("fanbox", "creator", "42")
    api.get_post.assert_not_awaited()


def _file_with_url(file_id: str, name: str, url: str) -> FileReference:
    return FileReference.model_validate({"id": file_id, "name": name, "deferred": True, "temp_download_url": url})
