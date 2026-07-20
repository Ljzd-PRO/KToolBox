from __future__ import annotations

import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from ktoolbox._enum import RetCodeEnum
from ktoolbox.api.generated import Post
from ktoolbox.configuration import config
from ktoolbox.downloader import Downloader


class RecordingProgress:
    instances: list[RecordingProgress] = []

    def __init__(self) -> None:
        self.started: tuple[str, int | None, int] | None = None
        self.updates: list[int] = []
        self.instances.append(self)

    def start(self, filename: str, total: int | None, completed: int) -> None:
        self.started = (filename, total, completed)

    def advance(self, size: int) -> None:
        self.updates.append(size)


async def run_once(downloader: Downloader, **kwargs: object):
    return await Downloader.run.__wrapped__(downloader, **kwargs)


def partial_response(
    request: httpx.Request,
    content: bytes = b"data",
    *,
    headers: dict[str, str] | None = None,
    status: int = 206,
) -> httpx.Response:
    return httpx.Response(status, content=content, headers=headers, request=request)


@pytest.mark.asyncio
async def test_stream_download_uses_headers_callbacks_and_progress(tmp_path: Path) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return partial_response(
            request,
            b"abcdef",
            headers={
                "Content-Range": "bytes 0-5/6",
                "Content-Disposition": "attachment;filename*=utf-8''server%20name.bin",
            },
        )

    sync_callback = Mock()
    async_callback = AsyncMock()
    post = Post(id="post", user="creator", service="fanbox", title="Title")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        downloader = Downloader(
            "https://files.example.test/data/source.bin",
            tmp_path,
            client,
            buffer_size=16,
            chunk_size=2,
            server_path="/source.bin",
            post=post,
        )
        assert downloader.url.endswith("source.bin")
        assert downloader.path == tmp_path
        assert downloader.client is client
        assert downloader.buffer_size == 16
        assert downloader.chunk_size == 2
        assert downloader.post is post
        assert downloader.finished
        result = await run_once(
            downloader,
            sync_callable=sync_callback,
            async_callable=async_callback,
            progress=RecordingProgress(),
        )

    assert result.code == RetCodeEnum.Success
    assert result.data == "server name.bin"
    assert downloader.filename == "server name.bin"
    assert (tmp_path / "server name.bin").read_bytes() == b"abcdef"
    assert seen[0].headers["range"] == "bytes=0-"
    assert RecordingProgress.instances[-1].started == ("server name.bin", 6, 0)
    assert sum(RecordingProgress.instances[-1].updates) == 6
    sync_callback.assert_called_once_with(downloader)
    async_callback.assert_awaited_once_with(downloader)
    assert bool(downloader)
    assert downloader.__call__.__func__ is downloader.run.__func__


@pytest.mark.asyncio
async def test_resume_counts_existing_bytes_for_content_length_filter(tmp_path: Path) -> None:
    temp = tmp_path / "resume.bin.tmp"
    temp.write_bytes(b"abc")
    config.job.max_file_size = 5

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["range"] == "bytes=3-"
        return partial_response(request, b"def")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        downloader = Downloader(
            "https://files.example.test/data/resume.bin",
            tmp_path,
            client,
            designated_filename="resume.bin",
            server_path="/resume.bin",
        )
        result = await run_once(downloader)

    assert result.code == RetCodeEnum.FileExisted
    assert "size: 6 bytes" in result.message
    assert temp.read_bytes() == b"abc"


@pytest.mark.asyncio
async def test_resume_download_appends_and_renames(tmp_path: Path) -> None:
    (tmp_path / "resume.bin.tmp").write_bytes(b"abc")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["range"] == "bytes=3-"
        return partial_response(request, b"def", headers={"Content-Range": "bytes 3-5/6"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        downloader = Downloader(
            "https://files.example.test/data/resume.bin",
            tmp_path,
            client,
            designated_filename="resume.bin",
            server_path="/resume.bin",
        )
        result = await run_once(downloader, progress=RecordingProgress())
    assert result.data == "resume.bin"
    assert (tmp_path / "resume.bin").read_bytes() == b"abcdef"
    assert RecordingProgress.instances[-1].started == ("resume.bin", 6, 3)


@pytest.mark.asyncio
async def test_duplicate_checks_before_and_after_request(tmp_path: Path) -> None:
    existing = tmp_path / "source.bin"
    existing.write_bytes(b"existing")

    def unexpected(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"Unexpected request: {request.url}")

    async with httpx.AsyncClient(transport=httpx.MockTransport(unexpected)) as client:
        downloader = Downloader("https://files.example.test/source.bin", tmp_path, client, server_path="/source.bin")
        result = await run_once(downloader)
    assert result.code == RetCodeEnum.FileExisted

    existing.rename(tmp_path / "header.bin")

    def handler(request: httpx.Request) -> httpx.Response:
        return partial_response(
            request,
            headers={
                "Content-Range": "bytes 0-3/4",
                "Content-Disposition": "attachment;filename=header.bin",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        downloader = Downloader("https://files.example.test/source.bin", tmp_path, client, server_path="/source.bin")
        result = await run_once(downloader)
    assert result.code == RetCodeEnum.FileExisted
    assert (tmp_path / "header.bin").read_bytes() == b"existing"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("minimum", "maximum", "total", "message"),
    [(5, None, 4, "below minimum"), (None, 3, 4, "above maximum")],
)
async def test_content_range_size_filters(
    tmp_path: Path,
    minimum: int | None,
    maximum: int | None,
    total: int,
    message: str,
) -> None:
    config.job.min_file_size = minimum
    config.job.max_file_size = maximum

    def handler(request: httpx.Request) -> httpx.Response:
        return partial_response(request, headers={"Content-Range": f"bytes 0-3/{total}"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        downloader = Downloader("https://files.example.test/file.bin", tmp_path, client, server_path="/file.bin")
        result = await run_once(downloader)
    assert result.code == RetCodeEnum.FileExisted
    assert message in result.message
    assert not (tmp_path / "file.bin").exists()


@pytest.mark.asyncio
async def test_invalid_content_length_does_not_abort_download(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            206,
            headers={"Content-Length": "invalid"},
            stream=httpx.ByteStream(b"x"),
            request=request,
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        downloader = Downloader("https://files.example.test/file.bin", tmp_path, client, server_path="/file.bin")
        result = await run_once(downloader, progress=RecordingProgress())
    assert result.data == "file.bin"
    assert RecordingProgress.instances[-1].started == ("file.bin", None, 0)


@pytest.mark.asyncio
async def test_unexpected_status_is_failure_and_restores_original_url(tmp_path: Path) -> None:
    transport = httpx.MockTransport(lambda request: partial_response(request, status=200))
    async with httpx.AsyncClient(transport=transport) as client:
        downloader = Downloader("https://files.example.test/file.bin", tmp_path, client, server_path="/file.bin")
        downloader._url = "https://redirected.example.test/file.bin"
        result = await run_once(downloader)
    assert result.code == RetCodeEnum.GeneralFailure
    assert downloader.url == "https://files.example.test/file.bin"


@pytest.mark.asyncio
async def test_bucket_download_uses_queryless_path_and_hardlink(tmp_path: Path) -> None:
    config.downloader.use_bucket = True
    config.downloader.bucket_path = tmp_path / "bucket"
    output = tmp_path / "output"
    output.mkdir()

    def handler(request: httpx.Request) -> httpx.Response:
        return partial_response(request, b"bucket", headers={"Content-Range": "bytes 0-5/6"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        downloader = Downloader(
            "https://files.example.test/data/aa/file.bin?download=1",
            output,
            client,
            server_path="/aa/file.bin?download=1",
        )
        result = await run_once(downloader)

    local = output / "file.bin"
    bucket = config.downloader.bucket_path / "aa/file.bin"
    assert result.data == "file.bin"
    assert local.read_bytes() == bucket.read_bytes() == b"bucket"
    assert os.stat(local).st_ino == os.stat(bucket).st_ino
    assert not (config.downloader.bucket_path / "aa/file.bin?download=1").exists()


@pytest.mark.asyncio
async def test_metadata_failure_is_nonfatal_and_cancel_stops_stream(tmp_path: Path) -> None:
    config.downloader.keep_metadata = True

    def handler(request: httpx.Request) -> httpx.Response:
        return partial_response(request, b"x", headers={"Content-Range": "bytes 0-0/1"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        downloader = Downloader("https://files.example.test/file.bin", tmp_path, client, server_path="/file.bin")
        with patch("ktoolbox.downloader.downloader.utime_from_headers", side_effect=OSError("denied")):
            result = await run_once(downloader)
    assert result.data == "file.bin"

    (tmp_path / "file.bin").unlink()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        downloader = Downloader("https://files.example.test/file.bin", tmp_path, client, server_path="/file.bin")
        downloader.cancel()
        with pytest.raises(asyncio.CancelledError):
            await run_once(downloader)
    assert (tmp_path / "file.bin.tmp").exists()
