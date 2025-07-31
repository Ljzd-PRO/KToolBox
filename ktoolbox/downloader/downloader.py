import asyncio
import os
from asyncio import CancelledError, Lock
from functools import cached_property
from pathlib import Path
from typing import Callable, Any, Coroutine, Type, Optional, Set
from urllib.parse import urlparse, unquote

import aiofiles
import httpx
import tenacity
import tqdm.asyncio
from loguru import logger
from pathvalidate import sanitize_filename
from tenacity import wait_fixed, retry_if_result, retry_if_exception
from tenacity.stop import stop_after_attempt, stop_never
from tqdm import tqdm as std_tqdm

from ktoolbox._enum import RetCodeEnum
from ktoolbox.api.model import Post
from ktoolbox.configuration import config
from ktoolbox.downloader.base import DownloaderRet
from ktoolbox.downloader.utils import filename_from_headers, duplicate_file_check, utime_from_headers
from ktoolbox.utils import generate_msg

__all__ = ["Downloader"]


class Downloader:
    """
    :ivar _save_filename: The actual filename for saving.
    """
    succeeded_servers: Set[int] = set()
    failure_servers: Set[int] = set()
    wait_lock = Lock()

    def __init__(
            self,
            url: str,
            path: Path,
            client: httpx.AsyncClient,
            *,
            buffer_size: int = None,
            chunk_size: int = None,
            designated_filename: str = None,
            server_path: str = None,
            post: Post = None
    ):
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

        self._next_subdomain_index = 1
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
    def post(self) -> Post:
        """Post that the file belongs to"""
        return self._post

    @property
    def filename(self) -> Optional[str]:
        """Actual filename of the download file"""
        return self._save_filename

    @property
    def finished(self) -> bool:
        """
        Check if the download finished

        :return: ``False`` if the download **in process**, ``True`` otherwise
        """
        return not self._finished_lock.locked()

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
                file=x.args[0].filename,
                post_name=x.args[0].post.title if x.args[0].post else None,
                post_id=x.args[0].post.id if x.args[0].post else None,
                message=x.outcome.result().message if not x.outcome.failed else None,
                exception=x.outcome.exception(),
                url=x.args[0].url
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
        :raise CancelledError: Job cancelled
        """
        # Get filename to check if file exists (First-time duplicate file check)
        # Check it before request to make progress more efficiency
        server_relpath = self._server_path[1:]
        server_relpath_without_params = urlparse(server_relpath).path
        server_path_filename = unquote(Path(server_relpath_without_params).name)
        # Priority order can be referenced from the constructor's documentation
        save_filepath = self._path / (self._save_filename or server_path_filename)

        # Get bucket file path
        bucket_file_path: Optional[Path] = None
        if config.downloader.use_bucket:
            bucket_file_path = config.downloader.bucket_path / server_relpath

        # Check if the file exists
        file_existed, ret_msg = duplicate_file_check(save_filepath, bucket_file_path)
        if file_existed:
            return DownloaderRet(
                code=RetCodeEnum.FileExisted,
                message=generate_msg(
                    ret_msg,
                    path=save_filepath
                )
            )

        tqdm_class: Type[std_tqdm] = tqdm_class or tqdm.asyncio.tqdm
        async with self.wait_lock:
            await asyncio.sleep(1 / config.downloader.tps_limit)
        async with self._finished_lock:
            temp_filepath = Path(f"{save_filepath}.{config.downloader.temp_suffix}")
            temp_size = temp_filepath.stat().st_size if temp_filepath.exists() else 0

            async with self._client.stream(
                    method="GET",
                    url=config.downloader.reverse_proxy.format(self._url),
                    follow_redirects=True,
                    timeout=config.downloader.timeout,
                    headers={"Range": f"bytes={temp_size}-"}
            ) as res:  # type: httpx.Response
                try:
                    subdomain_index = int(res.url.netloc.split(b".")[0][1:])
                except ValueError:
                    subdomain_index = None
                if res.status_code == 403:
                    if subdomain_index is not None:
                        self.succeeded_servers.discard(subdomain_index)
                        self.failure_servers.add(subdomain_index)
                    # try succeeded servers first
                    subdomain_index = next(iter(self.succeeded_servers), None)
                    if subdomain_index is None:
                        subdomain_index = self._next_subdomain_index
                        # Update self._next_subdomain_index
                        ## index fallback to 1 when a server after failure_servers has been tried
                        if self.failure_servers and self._next_subdomain_index > max(self.failure_servers):
                            self._next_subdomain_index = 1
                            self.failure_servers.clear()
                        ## otherwise, increment the index and avoid failure_servers
                        else:
                            self._next_subdomain_index += 1
                            while self._next_subdomain_index in self.failure_servers:
                                self._next_subdomain_index += 1
                        msg = "Download failed, trying next subdomain"
                    else:
                        msg = "Download failed, trying succeeded subdomains"
                    new_netloc = f"n{subdomain_index}.{config.api.files_netloc}"
                    self._url = str(res.url.copy_with(netloc=new_netloc.encode()))
                    return DownloaderRet(
                        code=RetCodeEnum.GeneralFailure,
                        message=generate_msg(
                            msg,
                            nex_subdomain=new_netloc,
                            status_code=res.status_code,
                            filename=save_filepath
                        )
                    )
                elif res.status_code != httpx.codes.PARTIAL_CONTENT:
                    self._url = self._initial_url
                    return DownloaderRet(
                        code=RetCodeEnum.GeneralFailure,
                        message=generate_msg(
                            "Download failed",
                            status_code=res.status_code,
                            filename=save_filepath
                        )
                    )
                else:
                    if subdomain_index is not None:
                        self.failure_servers.discard(subdomain_index)
                        self.succeeded_servers.add(subdomain_index)

                # Get filename for saving and check if file exists (Second-time duplicate file check)
                # Priority order can be referenced from the constructor's documentation
                self._save_filename = self._designated_filename or sanitize_filename(
                    filename_from_headers(res.headers)
                ) or server_path_filename
                save_filepath = self._path / self._save_filename
                file_existed, ret_msg = duplicate_file_check(save_filepath, bucket_file_path)
                if file_existed:
                    return DownloaderRet(
                        code=RetCodeEnum.FileExisted,
                        message=generate_msg(
                            ret_msg,
                            path=save_filepath
                        )
                    )

                # Download
                total_size = int(range_str.split("/")[-1]) if (range_str := res.headers.get("Content-Range")) else None
                async with aiofiles.open(str(temp_filepath), "ab", self._buffer_size) as f:
                    chunk_iterator = res.aiter_bytes(self._chunk_size)
                    t = tqdm_class(
                        desc=self._save_filename,
                        total=total_size,
                        initial=temp_size,
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
            if config.downloader.use_bucket:
                bucket_file_path.parent.mkdir(parents=True, exist_ok=True)
                os.link(temp_filepath, bucket_file_path)
            final_filepath = self._path / self._save_filename
            temp_filepath.rename(final_filepath)

            try:
                utime_from_headers(res.headers, final_filepath)
            except (OSError, ValueError, TypeError) as e:
                logger.warning(
                    generate_msg(
                        "Failed to set file time from headers",
                        file=self._save_filename,
                        exception=e
                    )
                )

            # Callbacks
            if sync_callable:
                sync_callable(self)
            if async_callable:
                await async_callable(self)

            return DownloaderRet(
                data=self._save_filename
            ) if self._save_filename else DownloaderRet(
                code=RetCodeEnum.GeneralFailure,
                message=generate_msg(
                    "Download failed",
                    filename=self._designated_filename
                )
            )

    __call__ = run
