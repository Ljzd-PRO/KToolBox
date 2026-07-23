import asyncio
from asyncio import CancelledError, Lock
from collections.abc import Awaitable, Callable
from functools import cached_property
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import aiofiles  # type: ignore[import-untyped]
import aiofiles.os  # type: ignore[import-untyped]
import httpx
from loguru import logger
from pathvalidate import sanitize_filename
from tenacity import AsyncRetrying, RetryCallState, retry_if_exception, retry_if_result, wait_fixed
from tenacity.stop import stop_after_attempt, stop_never

from ktoolbox._enum import RetCodeEnum
from ktoolbox.api.generated import Post
from ktoolbox.configuration import config
from ktoolbox.downloader.base import DownloaderRet
from ktoolbox.downloader.utils import duplicate_file_check, filename_from_headers, utime_from_headers
from ktoolbox.reporting import DownloadProgressObserver
from ktoolbox.utils import generate_msg

__all__ = ["Downloader"]


class Downloader:
    """
    :ivar _save_filename: The actual filename for saving.
    """

    wait_lock = Lock()

    def __init__(
        self,
        url: str,
        path: Path,
        client: httpx.AsyncClient,
        *,
        buffer_size: int | None = None,
        chunk_size: int | None = None,
        designated_filename: str | None = None,
        server_path: str,
        post: Post | None = None,
    ) -> None:
        # noinspection GrazieInspection
        """
        Initialize a file downloader

        - About filename:
            1. If ``designated_filename`` parameter is set, use it.
            2. Else if ``Content-Disposition`` is set in headers, use filename from it.
            3. Else use filename from 'file' part of ``server_path``.

        :param url: Download URL
        :param path: Directory path to save the file, which needs to be sanitized
        :param client: HTTPX AsyncClient
        :param buffer_size: Number of bytes for file I/O buffer
        :param chunk_size: Number of bytes for chunk of download stream
        :param designated_filename: Manually specify the filename for saving, which needs to be sanitized
        :param server_path: Server path of the file. if ``DownloaderConfiguration.use_bucket`` enabled, \
        it will be used as the save path.
        :param post: Post object, use for logging.
        """

        self._url = self._initial_url = url
        self._path = path
        self._client = client
        self._buffer_size = buffer_size or config.downloader.buffer_size
        self._chunk_size = chunk_size or config.downloader.chunk_size
        self._designated_filename = designated_filename
        self._server_path = server_path  # /hash[:1]/hash2[1:3]/hash
        self._save_filename = designated_filename  # Prioritize the manually specified filename
        self._post = post

        self._finished_lock = asyncio.Lock()
        self._stop: bool = False

    @cached_property
    def url(self) -> str:
        """Download URL"""
        return self._url

    @cached_property
    def path(self) -> Path:
        """Directory path to save the file"""
        return self._path

    @cached_property
    def client(self) -> httpx.AsyncClient:
        """HTTPX AsyncClient"""
        return self._client

    @cached_property
    def buffer_size(self) -> int:
        """Number of bytes for file I/O buffer"""
        return self._buffer_size

    @cached_property
    def chunk_size(self) -> int:
        """Number of bytes for chunk of download stream"""
        return self._chunk_size

    @cached_property
    def post(self) -> Post | None:
        """Post that the file belongs to"""
        return self._post

    @property
    def filename(self) -> str | None:
        """Actual filename of the download file"""
        return self._save_filename

    @property
    def finished(self) -> bool:
        """
        Check if the download finished

        :return: ``False`` if the download **in process**, ``True`` otherwise
        """
        return not self._finished_lock.locked()

    def cancel(self) -> None:
        """
        Cancel the download

        It will raise ``asyncio.CancelledError`` in ``chunk_iterator`` (writing chunk to file) iteration.
        """
        self._stop = True

    @staticmethod
    def _size_filter_result(total_size: int, save_filepath: Path) -> DownloaderRet[str] | None:
        minimum = config.job.min_file_size
        maximum = config.job.max_file_size
        if minimum is not None and total_size < minimum:
            reason = f"size: {total_size} bytes, below minimum: {minimum}"
        elif maximum is not None and total_size > maximum:
            reason = f"size: {total_size} bytes, above maximum: {maximum}"
        else:
            return None

        logger.debug(f"Skipping file {save_filepath.name} ({reason})")
        return DownloaderRet(
            code=RetCodeEnum.FileExisted,
            message=generate_msg(f"File skipped due to size filtering ({reason})", path=save_filepath),
        )

    async def run(
        self,
        *,
        sync_callable: Callable[["Downloader"], Any] | None = None,
        async_callable: Callable[["Downloader"], Awaitable[Any]] | None = None,
        progress: DownloadProgressObserver | None = None,
    ) -> DownloaderRet[str]:
        """
        Start to download

        :param sync_callable: Sync callable for download finished
        :param async_callable: Async callable for download finished
        :param progress: Optional byte-level progress observer
        :return: ``DownloaderRet`` which contain the actual output filename
        :raise CancelledError: Job cancelled
        """
        retrying = AsyncRetrying(
            stop=(
                stop_never if config.downloader.retry_stop_never else stop_after_attempt(config.downloader.retry_times)
            ),
            wait=wait_fixed(config.downloader.retry_interval),
            retry=retry_if_result(lambda result: not result and result.code != RetCodeEnum.FileExisted)
            | retry_if_exception(lambda error: isinstance(error, httpx.HTTPError)),
            before_sleep=self._before_retry,
            reraise=True,
        )
        return await retrying(
            self._run_once,
            sync_callable=sync_callable,
            async_callable=async_callable,
            progress=progress,
        )

    def _before_retry(self, state: RetryCallState) -> None:
        outcome = state.outcome
        logger.warning(
            generate_msg(
                f"Retrying ({state.attempt_number})",
                file=self.filename,
                post_name=self.post.title if self.post else None,
                post_id=self.post.id if self.post else None,
                message=(outcome.result().message if outcome is not None and not outcome.failed else None),
                exception=(outcome.exception() if outcome is not None else None),
                url=self.url,
            )
        )

    async def _run_once(
        self,
        *,
        sync_callable: Callable[["Downloader"], Any] | None = None,
        async_callable: Callable[["Downloader"], Awaitable[Any]] | None = None,
        progress: DownloadProgressObserver | None = None,
    ) -> DownloaderRet[str]:
        # Get filename to check if file exists (First-time duplicate file check)
        # Check it before request to make progress more efficiency
        server_relpath = self._server_path[1:]
        server_relpath_without_params = urlparse(server_relpath).path
        server_path_filename = unquote(Path(server_relpath_without_params).name)
        # Priority order can be referenced from the constructor's documentation
        save_filepath = self._path / (self._save_filename or server_path_filename)

        # Get bucket file path
        bucket_file_path: Path | None = None
        if config.downloader.use_bucket:
            bucket_file_path = config.downloader.bucket_path / server_relpath_without_params

        # Check if the file exists
        file_existed, ret_msg = duplicate_file_check(save_filepath, bucket_file_path)
        if file_existed:
            return DownloaderRet(
                code=RetCodeEnum.FileExisted,
                message=generate_msg(ret_msg or "Download file already exists", path=save_filepath),
            )

        async with self.wait_lock:
            await asyncio.sleep(1 / config.downloader.tps_limit)
        async with self._finished_lock:
            temp_filepath = Path(f"{save_filepath}.{config.downloader.temp_suffix}")
            try:
                temp_size = (await aiofiles.os.stat(temp_filepath)).st_size
            except FileNotFoundError:
                temp_size = 0

            async with self._client.stream(
                method="GET",
                url=config.downloader.reverse_proxy.format(self._url),
                follow_redirects=True,
                timeout=config.downloader.timeout,
                headers={"Range": f"bytes={temp_size}-"},
            ) as res:  # type: httpx.Response
                if res.status_code != httpx.codes.PARTIAL_CONTENT:
                    self._url = self._initial_url
                    return DownloaderRet(
                        code=RetCodeEnum.GeneralFailure,
                        message=generate_msg("Download failed", status_code=res.status_code, filename=save_filepath),
                        status_code=res.status_code,
                    )
                # Get filename for saving and check if file exists (Second-time duplicate file check)
                # Priority order can be referenced from the constructor's documentation
                header_filename = filename_from_headers(res.headers)
                self._save_filename = self._designated_filename or (
                    sanitize_filename(header_filename) if header_filename else server_path_filename
                )
                save_filepath = self._path / self._save_filename
                file_existed, ret_msg = duplicate_file_check(save_filepath, bucket_file_path)
                if file_existed:
                    return DownloaderRet(
                        code=RetCodeEnum.FileExisted,
                        message=generate_msg(ret_msg or "Download file already exists", path=save_filepath),
                    )

                # Download
                range_header = res.headers.get("Content-Range")
                total_size = int(range_header.split("/")[-1]) if range_header else None

                # A partial response's Content-Length is only the remaining size.
                if total_size is None:
                    content_length = res.headers.get("Content-Length")
                    if content_length:
                        try:
                            total_size = temp_size + int(content_length)
                        except ValueError:
                            pass
                if total_size is not None:
                    filtered = self._size_filter_result(total_size, save_filepath)
                    if filtered is not None:
                        return filtered
                async with aiofiles.open(str(temp_filepath), "ab", self._buffer_size) as f:
                    chunk_iterator = res.aiter_bytes(self._chunk_size)
                    if progress is not None:
                        progress.start(self._save_filename, total_size, temp_size)
                    async for chunk in chunk_iterator:
                        if self._stop:
                            raise CancelledError
                        await f.write(chunk)
                        if progress is not None:
                            progress.advance(len(chunk))

            # Download finished
            if config.downloader.use_bucket and bucket_file_path is not None:
                bucket_file_path.parent.mkdir(parents=True, exist_ok=True)
                await aiofiles.os.link(temp_filepath, bucket_file_path)
            final_filepath = self._path / self._save_filename
            await aiofiles.os.rename(temp_filepath, final_filepath)

            # Set file time from headers
            if config.downloader.keep_metadata:
                try:
                    utime_from_headers(res.headers, final_filepath)
                except (OSError, ValueError, TypeError) as e:
                    logger.warning(
                        generate_msg("Failed to set file time from headers", file=self._save_filename, exception=e)
                    )

            # Callbacks
            if sync_callable:
                sync_callable(self)
            if async_callable:
                await async_callable(self)

            return (
                DownloaderRet(data=self._save_filename)
                if self._save_filename
                else DownloaderRet(
                    code=RetCodeEnum.GeneralFailure,
                    message=generate_msg("Download failed", filename=self._designated_filename),
                )
            )

    __call__ = run
