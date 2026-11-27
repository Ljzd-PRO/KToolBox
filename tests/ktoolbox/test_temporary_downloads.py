from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

import httpx
import pytest
import respx

from ktoolbox._enum import RetCodeEnum
from ktoolbox.action.job import create_job_from_post
from ktoolbox.api.client import PawchiveClient
from ktoolbox.api.generated import Post
from ktoolbox.configuration import config
from ktoolbox.downloader import Downloader
from ktoolbox.downloader.temporary import TemporaryDownloader, TemporaryOutputConflict
from ktoolbox.job.runner import JobRunner
from ktoolbox.project_config import CreatorReference, ProjectNamingConfiguration
from ktoolbox.sync import SyncCoordinator, SyncOptions

WORK = {"id": "42", "user": "1", "service": "fanbox", "title": "Fixture"}
DETAIL_URL = "https://pawchive.pw/api/v1/fanbox/user/1/post/42"


@pytest.fixture(autouse=True)
def deterministic_downloads() -> None:
    config.downloader.tps_limit = 1000
    config.downloader.retry_times = 2
    config.downloader.retry_interval = 0
    config.downloader.retry_stop_never = False
    config.job.count = 1
    config.job.download_attachments = True
    config.job.include_revisions = False
    config.job.allow_list = set()
    config.job.block_list = set()


@respx.mock
async def test_sync_downloads_deferred_files_after_permanent_numbering_and_refreshes_once(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    config.downloader.use_bucket = True
    config.downloader.bucket_path = tmp_path / "bucket"
    config.downloader.reverse_proxy = "https://proxy.example.test/?url={}"
    config.downloader.session_key = "do-not-send-this"
    directory = tmp_path / "Fixture Creator [fanbox-1]" / "Fixture [42]" / "attachments"
    directory.mkdir(parents=True)
    first = {"name": "large.zip", "deferred": True}
    next_file = {"name": "next.zip", "deferred": True}
    missing = {"name": "missing.zip", "deferred": True}
    normal = {"name": "normal.zip", "path": "/fixture/normal.zip"}
    normal_bucket = config.downloader.bucket_path / "fixture/normal.zip"
    normal_bucket.parent.mkdir(parents=True)
    normal_bucket.write_bytes(b"normal")
    old = "https://t2.pawchive.pw/d/fixture/first.zip?signed=secret-old"
    current = "https://t3.pawchive.pw/d/fixture/first.zip?signed=secret-new%2Fmore"
    current_next = "https://t3.pawchive.pw/f/fixture/next.zip?signed=secret-next"
    respx.get("https://pawchive.pw/api/v1/fanbox/user/1/profile").respond(
        200, json={"id": "1", "service": "fanbox", "name": "Fixture Creator"}
    )
    respx.get("https://pawchive.pw/api/v1/fanbox/user/1", params={"o": "0"}).respond(
        200, json=[{**WORK, "attachments": [first, normal, next_file, missing]}]
    )
    detail = respx.get(DETAIL_URL).mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    **WORK,
                    "attachments": [
                        {**first, "temp_download_url": old},
                        {**next_file, "path": current_next},
                        missing,
                    ],
                },
            ),
            httpx.Response(
                200,
                json={
                    **WORK,
                    "attachments": [
                        {**first, "temp_download_url": current},
                        {**next_file, "path": current_next},
                        missing,
                    ],
                },
            ),
        ]
    )
    stale = respx.get(old).respond(403)

    def transfer(request: httpx.Request) -> httpx.Response:
        assert "cookie" not in request.headers
        assert "authorization" not in request.headers
        assert "range" not in request.headers
        assert request.headers["user-agent"].startswith("KToolBox/")
        return httpx.Response(200, stream=Chunks(b"complete ", b"file"))

    fresh = respx.get(current).mock(side_effect=transfer)
    fresh_next = respx.get(current_next).mock(side_effect=transfer)
    with caplog.at_level(logging.INFO, logger="httpx"):
        async with PawchiveClient() as client:
            summary = await SyncCoordinator(client).run(
                [CreatorReference(service="fanbox", creator_id="1")], SyncOptions(output=tmp_path)
            )

    assert summary.downloads.completed == 2
    assert summary.downloads.existed == 1
    assert summary.downloads.failed == 1
    assert summary.downloads.failures[0].operation == "download_temporary_file"
    assert summary.downloads.failures[0].file_name == "4.zip"
    assert detail.call_count == 2
    assert stale.call_count == fresh.call_count == fresh_next.call_count == 1
    assert (directory / "1.zip").read_bytes() == b"normal"
    assert (directory / "2.zip").read_bytes() == (directory / "3.zip").read_bytes() == b"complete file"
    assert not (directory / "4.zip").exists()
    assert list(config.downloader.bucket_path.rglob("*.zip")) == [normal_bucket]
    assert "secret-" not in caplog.text
    assert "secret-" not in (directory.parent / "post.json").read_text()


@respx.mock
async def test_direct_work_temporary_cover_and_output_collision(tmp_path: Path) -> None:
    cover = {"name": "shared.zip", "deferred": True, "temp_download_url": "https://t1.pawchive.pw/d/fixture/cover.zip"}
    post = Post.model_validate({**WORK, "file": cover, "attachments": [{"name": "shared.zip", "path": "/a/ordinary"}]})
    naming = ProjectNamingConfiguration(
        sequential_filename=False,
        post_structure={"file": "{}", "attachments": "."},  # type: ignore[arg-type]
    )
    output = tmp_path / "collision"
    jobs = await create_job_from_post(post, output, naming=naming, download_file=True)
    assert len(jobs) == 2
    assert jobs[1].temporary and jobs[1].temporary.output_conflict
    regular = respx.get("https://file.pawchive.pw/data/a/ordinary").respond(
        206, headers={"Content-Range": "bytes 0-7/8"}, content=b"ordinary"
    )
    runner = JobRunner(job_list=jobs, progress=False)
    assert await runner.start() == 1
    assert regular.called and (output / "shared.zip").read_bytes() == b"ordinary"
    assert runner.summary.failures[0].operation == "temporary_file_conflict"

    direct = Post.model_validate({**WORK, "file": cover})
    disabled = await create_job_from_post(direct, tmp_path / "disabled", download_file=False)
    assert not disabled
    config.job.allow_list = {"*.png"}
    filtered = await create_job_from_post(direct, tmp_path / "filtered", download_file=True)
    assert not filtered
    config.job.allow_list = set()
    route = respx.get("https://t1.pawchive.pw/d/fixture/cover.zip").respond(200, content=b"cover")
    jobs = await create_job_from_post(direct, tmp_path / "allowed", naming=naming, download_file=True)
    assert await JobRunner(job_list=jobs, progress=False).start() == 0
    assert route.call_count == 1
    assert (tmp_path / "allowed" / "shared.zip").read_bytes() == b"cover"


@pytest.mark.parametrize("status", [400, 404, 416, 302, 200])
@respx.mock
async def test_temporary_errors_are_safe_and_do_not_follow_redirects(tmp_path: Path, status: int) -> None:
    url = "https://t2.pawchive.pw/d/fixture/zip?signed=never-persist"
    post = Post.model_validate({**WORK, "attachments": [{"name": "fixture.zip", "temp_download_url": url}]})
    blocked = respx.get(url).respond(
        status,
        headers={
            "Location": "https://other.example.test/",
            "Content-Type": "text/html",
        },
    )
    # A rejected URL may be refreshed, but a returned identical URL is not retried.
    detail = respx.get(DETAIL_URL).respond(
        200,
        json={
            **WORK,
            "attachments": [{"name": "fixture.zip", "temp_download_url": url}],
        },
    )
    runner = JobRunner(job_list=await create_job_from_post(post, tmp_path), progress=False)
    assert await runner.start() == 1
    assert blocked.call_count == 1
    assert detail.call_count == (1 if status == 404 else 0)
    assert runner.summary.failures[0].http_status == status
    assert "never-persist" not in runner.summary.failures[0].model_dump_json()
    assert not (tmp_path / "attachments" / "1.zip").exists()


async def test_unknown_length_stream_is_bounded_and_partial_file_is_removed(tmp_path: Path) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, stream=Chunks(b"abc", b"def")))
    ) as client:
        download = make_downloader(tmp_path, client)
        config.job.max_file_size = 4
        assert (await download.run()).code == RetCodeEnum.FileExisted
        assert _entries(tmp_path) == set()
        config.job.max_file_size = None
        config.job.min_file_size = 7
        assert (await download.run()).code == RetCodeEnum.FileExisted
        assert _entries(tmp_path) == set()


async def test_temporary_429_updates_shared_download_pause(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Downloader, "_paused_until", 0.0)
    monkeypatch.setattr(Downloader, "_rate_limit_generation", 0)
    monkeypatch.setattr(Downloader, "_rate_limit_strikes", 0)
    config.downloader.retry_times = 1

    def limited(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "1"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(limited)) as client:
        assert (await make_downloader(tmp_path, client).run()).status_code == 429
    assert Downloader._paused_until > time.monotonic()
    assert Downloader._rate_limit_generation == 1


@respx.mock
async def test_temporary_url_is_refreshed_only_once_after_rejection(tmp_path: Path) -> None:
    old = "https://t1.pawchive.pw/d/fixture/zip?signed=old"
    new = "https://t2.pawchive.pw/d/fixture/zip?signed=new"
    ref = {"name": "fixture.zip", "deferred": True}
    post = Post.model_validate({**WORK, "attachments": [{**ref, "temp_download_url": old}]})
    first = respx.get(old).respond(403)
    second = respx.get(new).respond(410)
    detail = respx.get(DETAIL_URL).respond(200, json={**WORK, "attachments": [{**ref, "temp_download_url": new}]})
    runner = JobRunner(job_list=await create_job_from_post(post, tmp_path), progress=False)

    assert await runner.start() == 1
    assert first.call_count == second.call_count == detail.call_count == 1
    assert runner.summary.failures[0].http_status == 410
    assert runner.summary.failures[0].operation == "download_temporary_file"


async def test_temporary_retries_restart_and_do_not_replace_existing_different_file(tmp_path: Path) -> None:
    attempts = 0

    def transfer(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(200, stream=Chunks(b"fixture", fail=attempts == 1))

    async with httpx.AsyncClient(transport=httpx.MockTransport(transfer)) as client:
        download = make_downloader(tmp_path, client)
        assert (await download.run()).data == "fixture.zip"
        assert attempts == 2
        assert (tmp_path / "fixture.zip").read_bytes() == b"fixture"
        assert (await download.run()).code == RetCodeEnum.FileExisted
        (tmp_path / "fixture.zip").write_bytes(b"different")
        with pytest.raises(TemporaryOutputConflict):
            await download.run()
    assert (tmp_path / "fixture.zip").read_bytes() == b"different"
    assert _entries(tmp_path) == {"fixture.zip"}


async def test_temporary_cancellation_removes_unfinished_file(tmp_path: Path) -> None:
    started = asyncio.Event()

    class BlockingStream(Chunks):
        async def __aiter__(self):
            yield b"partial"
            started.set()
            await asyncio.Event().wait()

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, stream=BlockingStream()))
    ) as client:
        task = asyncio.create_task(make_downloader(tmp_path, client).run())
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    assert _entries(tmp_path) == set()


class Chunks(httpx.AsyncByteStream):
    def __init__(self, *chunks: bytes, fail: bool = False) -> None:
        self.chunks = chunks
        self.fail = fail

    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk
        if self.fail:
            raise httpx.ReadError("synthetic interrupted stream")


async def test_temporary_attachments_do_not_change_inline_image_numbers(tmp_path: Path) -> None:
    config.job.extract_content_images = True
    normal = {"name": "normal.png", "path": "/fixture/normal.png"}
    deferred = {"name": "temporary.png", "deferred": True}
    work = {**WORK, "content": '<img src="/fixture/inline.png">'}
    old_post = Post.model_validate({**work, "attachments": [normal]})
    new_post = Post.model_validate({**work, "attachments": [deferred, normal]})
    old_jobs = await create_job_from_post(old_post, tmp_path / "old")
    new_jobs = await create_job_from_post(new_post, tmp_path / "new")
    assert [job.alt_filename for job in old_jobs] == ["1.png", "2.png"]
    assert [job.alt_filename for job in new_jobs] == ["1.png", "2.png", "3.png"]
    assert new_jobs[-1].temporary is not None


def make_downloader(path: Path, client: httpx.AsyncClient) -> TemporaryDownloader:
    return TemporaryDownloader(
        "https://t2.pawchive.pw/d/fixture/zip",
        path,
        client,
        designated_filename="fixture.zip",
        server_path="",
        chunk_size=3,
    )


def _entries(path: Path) -> set[str]:
    return {item.name for item in path.iterdir()}
