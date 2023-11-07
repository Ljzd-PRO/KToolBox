import asyncio
import urllib.parse
from pathlib import Path
from typing import Callable, Any, Coroutine, Type

import aiofiles
import httpx
import tqdm.asyncio
from tqdm import tqdm as std_tqdm

from ktoolbox.configuration import config
from ktoolbox.downloader import DownloaderRet
from ktoolbox.enum import RetCodeEnum
from ktoolbox.utils import file_name_from_headers, generate_message

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
        Initial a file downloader

        :param url: Download URL
        :param path: Directory path to save the file
        :param buffer_size: Number of bytes for file I/O buffer
        :param chunk_size: Number of bytes for chunk of download stream
        :param alt_filename: Use this name if no filename given by the server

        About filename:
            * If `Content-Disposition` is set in headers, use filename from it.
            * Else if `alt_filename` parameter is set, use it.
            * Else use filename from URL 'path' part.
        """

        self.url = url
        self.path = path
        self.buffer_size = buffer_size or config.downloader.buffer_size
        self.chunk_size = chunk_size or config.downloader.chunk_size
        self.alt_filename = alt_filename

        self.lock = asyncio.Lock()

    @property
    def finished(self) -> bool:
        """
        Check if the download finished

        :return: `False` if the download **in process**, `False` otherwise
        """
        return not self.lock.locked()

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
        :param tqdm_class: `tqdm` class to replace default `tqdm.asyncio.tqdm`
        :param progress: Show progress bar
        :return: `DownloaderRet` which contain the actual output filename
        """
        tqdm_class: Type[std_tqdm] = tqdm_class or tqdm.asyncio.tqdm
        async with self.lock:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                        method="GET",
                        url=self.url,
                        follow_redirects=True,
                        timeout=config.downloader.timeout
                ) as res:  # type: httpx.Response
                    if res.status_code != httpx.codes.OK:
                        return DownloaderRet(
                            code=RetCodeEnum.GeneralFailure,
                            message=generate_message(
                                title="Download failed",
                                status_code=res.status_code,
                                filename=self.alt_filename
                            )
                        )
                    if not (file_name := file_name_from_headers(res.headers)):
                        if not (file_name := self.alt_filename):
                            file_name = urllib.parse.unquote(Path(self.url).name)
                    total_size = int(length_str) if (length_str := res.headers.get("Content-Length")) else None
                    async with aiofiles.open(str(self.path / file_name), "wb", self.buffer_size) as f:
                        chunk_iterator = res.aiter_bytes(self.chunk_size)
                        t = tqdm_class(
                            desc=file_name,
                            total=total_size,
                            disable=not progress,
                            unit="B",
                            unit_scale=True
                        )
                        async for chunk in chunk_iterator:
                            await f.write(chunk)
                            t.update(len(chunk))  # Update progress bar
            if sync_callable:
                sync_callable(self)
            if async_callable:
                await async_callable(self)
            return DownloaderRet(
                data=file_name
            ) if file_name else DownloaderRet(
                code=RetCodeEnum.GeneralFailure,
                message=generate_message(
                    "Download failed",
                    filename=self.alt_filename
                )
            )

    __call__ = run
