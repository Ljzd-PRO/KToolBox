import asyncio
import urllib.parse
from asyncio import CancelledError
from functools import cached_property
from pathlib import Path
from typing import Callable, Any, Coroutine, Type, Optional

import aiofiles
import httpx
import tqdm.asyncio
from tqdm import tqdm as std_tqdm

from ktoolbox.configuration import config
from ktoolbox.downloader import DownloaderRet
from ktoolbox.enum import RetCodeEnum
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
            alt_filename: str = None
    ):
        """
        Initialize a file downloader

        :param url: Download URL
        :param path: Directory path to save the file
        :param buffer_size: Number of bytes for file I/O buffer
        :param chunk_size: Number of bytes for chunk of download stream
        :param alt_filename: Use this name if no filename given by the server

        .. rubric:: About filename:
        * If ``Content-Disposition`` is set in headers, use filename from it.
        * Else if ``alt_filename`` parameter is set, use it.
        * Else use filename from URL 'path' part.
        """

        self._url = url
        self._path = path
        self._buffer_size = buffer_size or config.downloader.buffer_size
        self._chunk_size = chunk_size or config.downloader.chunk_size
        self._alt_filename = alt_filename
        self._filename = alt_filename

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
        tqdm_class: Type[std_tqdm] = tqdm_class or tqdm.asyncio.tqdm
        async with self._lock:
            async with httpx.AsyncClient() as client:
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
                                filename=self._alt_filename
                            )
                        )

                    # Get filename
                    if not (filename := filename_from_headers(res.headers)):
                        if not (filename := self._alt_filename):
                            filename = urllib.parse.unquote(Path(self._url).name)
                    self._filename = filename

                    if (self._path / filename).is_file():
                        return DownloaderRet(
                            code=RetCodeEnum.FileExisted,
                            message=generate_msg(
                                "Download file existed, skipped",
                                path=self._path / filename
                            )
                        )

                    # Download
                    temp_filepath = (self._path / filename).with_suffix(f".{config.downloader.temp_suffix}")
                    total_size = int(length_str) if (length_str := res.headers.get("Content-Length")) else None
                    async with aiofiles.open(str(temp_filepath), "wb", self._buffer_size) as f:
                        chunk_iterator = res.aiter_bytes(self._chunk_size)
                        t = tqdm_class(
                            desc=filename,
                            total=total_size,
                            disable=not progress,
                            unit="B",
                            unit_scale=True
                        )
                        async for chunk in chunk_iterator:
                            if self._stop:
                                raise CancelledError
                            await f.write(chunk)
                            t.update(len(chunk))  # Update progress bar

            # Download finished
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
