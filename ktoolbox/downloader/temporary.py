from __future__ import annotations

import asyncio
import errno
import filecmp
import logging
import os
import tempfile
from collections.abc import Awaitable, Callable
from contextlib import suppress
from contextvars import ContextVar
from pathlib import Path
from typing import Any

import aiofiles  # type: ignore[import-untyped]
import aiofiles.os  # type: ignore[import-untyped]
import httpx
from loguru import logger

from ktoolbox import __version__
from ktoolbox._enum import RetCodeEnum
from ktoolbox.api.temporary_files import validated_temporary_url
from ktoolbox.configuration import config
from ktoolbox.reporting import DownloadProgressObserver

from .base import DownloaderRet
from .downloader import Downloader
from .utils import utime_from_headers

_signed_request = ContextVar("ktoolbox_signed_request", default=False)


class _HideSignedRequest(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not _signed_request.get()


# HTTPX includes the entire request URL in its INFO log.
_filter = _HideSignedRequest()
for _logger_name in ("httpx", "httpcore.http11", "httpcore.http2"):
    logging.getLogger(_logger_name).addFilter(_filter)


class TemporaryOutputConflict(Exception):
    def __init__(self) -> None:
        super().__init__("The output filename conflicts with an existing or scheduled file; nothing was overwritten")


class TemporaryDownloader(Downloader):
    """Download a signed file without Range, bucket paths, or the configured reverse proxy."""

    async def _run_once(
        self,
        *,
        sync_callable: Callable[[Downloader], Any] | None = None,
        async_callable: Callable[[Downloader], Awaitable[Any]] | None = None,
        progress: DownloadProgressObserver | None = None,
    ) -> DownloaderRet[str]:
        filename = self.filename
        if filename is None:
            raise ValueError("Temporary downloads require a destination filename")
        if validated_temporary_url(self.url) is None:
            raise ValueError("Invalid Pawchive temporary download destination")
        target = self.path / filename

        async with self._finished_lock:
            request = self.client.build_request(
                "GET",
                self.url,
                headers={"Accept-Encoding": "identity", "User-Agent": f"KToolBox/{__version__}"},
                timeout=config.downloader.timeout,
            )
            request.headers.pop("cookie", None)
            request.headers.pop("authorization", None)
            request.headers.pop("range", None)
            async with Downloader.wait_lock:
                await asyncio.sleep(1 / config.downloader.tps_limit)
                await Downloader._wait_for_rate_limit()
                request_generation = Downloader._rate_limit_generation
            token = _signed_request.set(True)
            try:
                response = await self.client.send(request, stream=True, follow_redirects=False, auth=None)
                try:
                    Downloader._track_rate_limit(response, request_generation=request_generation)
                    result = await self._save_response(response, target, progress)
                finally:
                    await response.aclose()
            finally:
                _signed_request.reset(token)
            if result:
                if sync_callable:
                    sync_callable(self)
                if async_callable:
                    await async_callable(self)
            return result

    async def _save_response(
        self,
        response: httpx.Response,
        target: Path,
        progress: DownloadProgressObserver | None,
    ) -> DownloaderRet[str]:
        if response.status_code != httpx.codes.OK:
            return DownloaderRet(
                code=RetCodeEnum.GeneralFailure,
                message=f"Temporary file host returned HTTP {response.status_code}",
                status_code=response.status_code,
            )
        content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        disposition = response.headers.get("content-disposition", "").split(";", 1)[0].strip().lower()
        if content_type == "text/html" and disposition != "attachment":
            return DownloaderRet(
                code=RetCodeEnum.GeneralFailure,
                message="Temporary file host returned a page instead of a download",
                status_code=response.status_code,
            )
        total_size = _content_length(response.headers)
        if total_size is not None:
            filtered = self._size_filter_result(total_size, target)
            if filtered is not None:
                return filtered
        fd, name = tempfile.mkstemp(
            prefix=".ktoolbox-download-", suffix=f".{config.downloader.temp_suffix}", dir=self.path
        )
        os.close(fd)
        temporary = Path(name)
        try:
            size = 0
            async with aiofiles.open(temporary, "wb", self.buffer_size) as output:
                if progress is not None:
                    progress.start(target.name, total_size, 0)
                async for chunk in response.aiter_bytes(self.chunk_size):
                    if self._stop:
                        raise asyncio.CancelledError
                    size += len(chunk)
                    maximum = config.job.max_file_size
                    if maximum is not None and size > maximum:
                        filtered = self._size_filter_result(size, target)
                        assert filtered is not None
                        return filtered
                    await output.write(chunk)
                    if progress is not None:
                        progress.advance(len(chunk))
            if total_size is not None and size != total_size:
                raise httpx.RemoteProtocolError("Temporary file length did not match the response headers")
            filtered = self._size_filter_result(size, target)
            if filtered is not None:
                return filtered
            if not await asyncio.to_thread(_publish, temporary, target):
                return DownloaderRet(code=RetCodeEnum.FileExisted, message="The existing file has identical contents")
            if config.downloader.keep_metadata:
                try:
                    utime_from_headers(response.headers, target)
                except (OSError, TypeError, ValueError):
                    logger.warning("Failed to preserve metadata for {}", target.name)
            return DownloaderRet(data=target.name)
        finally:
            with suppress(FileNotFoundError):
                await aiofiles.os.remove(temporary)


def _content_length(headers: httpx.Headers) -> int | None:
    if headers.get("content-encoding", "identity").lower() != "identity":
        return None
    try:
        length = int(headers.get("content-length", ""))
    except ValueError:
        return None
    return length if length >= 0 else None


def _publish(temporary: Path, target: Path) -> bool:
    """Publish without overwriting; an existing name alone doesn't prove file identity."""
    try:
        try:
            os.link(temporary, target)
        except OSError as error:
            no_hardlinks = error.errno in {errno.ENOTSUP, errno.EPERM, errno.EXDEV, errno.ENOSYS}
            if not no_hardlinks and getattr(error, "winerror", None) not in {1, 50}:
                raise
            # Filesystems without hardlinks still support exclusive file creation.
            with target.open("xb"):
                pass
            try:
                os.replace(temporary, target)
            except OSError:
                target.unlink(missing_ok=True)
                raise
    except FileExistsError:
        if not target.is_symlink() and target.is_file() and filecmp.cmp(temporary, target, shallow=False):
            return False
        raise TemporaryOutputConflict from None
    return True
