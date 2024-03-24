import asyncio
import os
from asyncio import CancelledError
from functools import cached_property
from pathlib import Path
from typing import Callable, Any, Coroutine, Type, Optional
from urllib.parse import urlparse, unquote

import aiofiles
import httpx
import tenacity
import tqdm.asyncio
from loguru import logger
from tenacity import wait_fixed, retry_if_result, retry_if_exception
from tenacity.stop import stop_after_attempt, stop_never
from tqdm import tqdm as std_tqdm

from ktoolbox._enum import RetCodeEnum
from ktoolbox.configuration import config
from ktoolbox.downloader import DownloaderRet
from ktoolbox.utils import filename_from_headers, generate_msg

__all__ = ["Downloader"]


class Downloader:
    def __init__(
            self,
            url: str,
            path: Path,
            *,
            buffer_size: int = None,
            chunk_size: int = None,
            alt_filename: str = None,
            server_path: str = None
    ):
        # noinspection GrazieInspection
        """
        Initialize a file downloader

        - About filename:
            * If ``alt_filename`` parameter is set, use it.
            * Else if ``Content-Disposition`` is set in headers, use filename from it.
            * Else use filename from URL 'path' part.

        :param url: Download URL
        :param path: Directory path to save the file
        :param buffer_size: Number of bytes for file I/O buffer
        :param chunk_size: Number of bytes for chunk of download stream
        :param alt_filename: Use this name if no filename given by the server
        :param server_path: Server path of the file. if config.use_bucket is True, \
        it will be used as save the path to the file
        """

        self._url = url
        self._path = path
        self._buffer_size = buffer_size or config.downloader.buffer_size
        self._chunk_size = chunk_size or config.downloader.chunk_size
        # _alt_filename 是用于下载的文件名
        self._alt_filename = alt_filename  # 用于下载的文件名
        self._server_path = server_path  # 服务器文件路径 /hash[:1]/hash2[1:3]/hash
        self._filename = alt_filename  # 保留用做实际文件名

        self._lock = asyncio.Lock()
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
    def buffer_size(self) -> int:
        """Number of bytes for file I/O buffer"""
        return self._buffer_size

    @cached_property
    def chunk_size(self) -> int:
        """Number of bytes for chunk of download stream"""
        return self._chunk_size

    @property
    def filename(self) -> Optional[str]:
        """Actual filename of the download file"""
        return self._filename

    @property
    def finished(self) -> bool:
        """
        Check if the download finished

        :return: ``False`` if the download **in process**, ``True`` otherwise
        """
        return not self._lock.locked()

    def cancel(self):
        """
        Cancel the download

        It will raise ``asyncio.CancelledError`` in ``chunk_iterator`` (writing chunk to file) iteration.
        """
        self._stop = True

    @tenacity.retry(
        stop=stop_never if config.downloader.retry_stop_never else stop_after_attempt(config.downloader.retry_times),
        wait=wait_fixed(config.downloader.retry_interval),
        retry=retry_if_result(
            lambda x: not x and x.code != RetCodeEnum.FileExisted
        ) | retry_if_exception(
            lambda x: isinstance(x, httpx.HTTPError)
        ),
        before_sleep=lambda x: logger.warning(
            generate_msg(
                f"Retrying ({x.attempt_number})",
                message=x.outcome.result().message if not x.outcome.failed else None,
                exception=x.outcome.exception()
            )
        ),
        reraise=True
    )
    async def run(
            self,
            *,
            sync_callable: Callable[["Downloader"], Any] = None,
            async_callable: Callable[["Downloader"], Coroutine] = None,
            tqdm_class: Type[std_tqdm] = None,
            progress: bool = False
    ) -> DownloaderRet[str]:
        """
        Start to download

        :param sync_callable: Sync callable for download finished
        :param async_callable: Async callable for download finished
        :param tqdm_class: ``tqdm`` class to replace default ``tqdm.asyncio.tqdm``
        :param progress: Show progress bar
        :return: ``DownloaderRet`` which contain the actual output filename
        :raise CancelledError
        """
        # Get filename to check if file exists
        # Check it before request to make progress more efficiency
        server_relpath = self._server_path[1:]
        server_relpath_without_params = urlparse(server_relpath).path
        server_path_filename = unquote(Path(server_relpath_without_params).name)
        art_file_path = self._path / (self._filename or server_path_filename)
        check_path = art_file_path

        # Get bucket file path
        art_bucket_file_path: Optional[Path] = None
        if config.downloader.use_bucket:
            art_bucket_file_path = config.downloader.bucket_path / server_relpath
            check_path = art_bucket_file_path

        # Check if the file exists
        if check_path.is_file():
            if config.downloader.use_bucket:
                ret_msg = "Download file already exists in both bucket and local, skipping"
                if not art_file_path.is_file():
                    ret_msg = "Download file already exists in bucket, linking to target path"
                    check_path.hardlink_to(art_file_path)
            else:
                ret_msg = "Download file already exists, skipping"
            return DownloaderRet(
                code=RetCodeEnum.FileExisted,
                message=generate_msg(
                    ret_msg,
                    path=art_file_path
                )
            )

        tqdm_class: Type[std_tqdm] = tqdm_class or tqdm.asyncio.tqdm
        async with self._lock:
            async with httpx.AsyncClient(verify=config.ssl_verify) as client:
                async with client.stream(
                        method="GET",
                        url=self._url,
                        follow_redirects=True,
                        timeout=config.downloader.timeout
                ) as res:  # type: httpx.Response
                    if res.status_code != httpx.codes.OK:
                        return DownloaderRet(
                            code=RetCodeEnum.GeneralFailure,
                            message=generate_msg(
                                "Download failed",
                                status_code=res.status_code,
                                filename=art_file_path
                            )
                        )

                    # Get filename
                    filename = self._alt_filename or filename_from_headers(res.headers) or server_path_filename
                    self._filename = filename

                    # Download
                    temp_filepath = Path(f"{(self._path / server_path_filename)}.{config.downloader.temp_suffix}")
                    total_size = int(length_str) if (length_str := res.headers.get("Content-Length")) else None
                    async with aiofiles.open(str(temp_filepath), "wb", self._buffer_size) as f:
                        chunk_iterator = res.aiter_bytes(self._chunk_size)
                        t = tqdm_class(
                            desc=filename,
                            total=total_size,
                            disable=not progress,
                            unit="iB",
                            unit_scale=True,
                            unit_divisor=1024
                        )
                        async for chunk in chunk_iterator:
                            if self._stop:
                                raise CancelledError
                            await f.write(chunk)
                            t.update(len(chunk))  # Update progress bar

            # Download finished
            if config.downloader.use_bucket:
                art_bucket_file_path.parent.mkdir(parents=True, exist_ok=True)
                os.link(temp_filepath, art_bucket_file_path)

            temp_filepath.rename(self._path / filename)
            if sync_callable:
                sync_callable(self)
            if async_callable:
                await async_callable(self)
            return DownloaderRet(
                data=filename
            ) if filename else DownloaderRet(
                code=RetCodeEnum.GeneralFailure,
                message=generate_msg(
                    "Download failed",
                    filename=self._alt_filename
                )
            )

    __call__ = run
