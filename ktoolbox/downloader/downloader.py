import urllib.parse
from pathlib import Path

import httpx
import tqdm.asyncio

from ktoolbox.configuration import config
from ktoolbox.downloader import DownloaderRet
from ktoolbox.enum import RetCodeEnum

__all__ = ["download"]

from ktoolbox.utils import file_name_from_headers


async def download(
        url: str,
        path: Path,
        *,
        buffer_size: int = None,
        chunk_size: int = None,
        alt_filename: str = None,
        progress: bool = False
) -> DownloaderRet[str]:
    """
    Download a file from url to a destination path.

    :param url: Download URL
    :param path: Directory path to save the file
    :param buffer_size: Number of bytes for file I/O buffer
    :param chunk_size: Number of bytes for chunk of download stream
    :param alt_filename: Use this name if no filename given by the server
    :param progress: Show progress bar
    :return: `DownloaderRet` which contain the actual output filename

    About filename:
        * If `Content-Disposition` is set in headers, use filename from it.
        * Else if `alt_filename` parameter is set, use it.
        * Else use filename from URL 'path' part.
    """
    buffer_size = buffer_size or config.downloader.buffer_size
    chunk_size = chunk_size or config.downloader.chunk_size
    async with httpx.AsyncClient() as client:
        async with client.stream(
                method="GET",
                url=url,
                follow_redirects=True,
                timeout=config.downloader.timeout
        ) as res:  # type: httpx.Response
            if res.status_code != httpx.codes.OK:
                return DownloaderRet(
                    code=RetCodeEnum.GeneralFailure.value,
                    message=f"Download failed - status_code: {res.status_code}"
                )
            if not (file_name := file_name_from_headers(res.headers)):
                if not (file_name := alt_filename):
                    file_name = urllib.parse.unquote(Path(url).name)
            total_size = int(length_str) if (length_str := res.headers.get("Content-Length")) else None
            with open(str(path / file_name), "wb", buffer_size) as f:
                chunk_iterator = res.aiter_bytes(chunk_size)
                t = tqdm.asyncio.tqdm(
                    desc=file_name,
                    total=total_size,
                    disable=not progress,
                    unit="B",
                    unit_scale=True
                )
                async for chunk in chunk_iterator:
                    f.write(chunk)
                    t.update(len(chunk))  # Update progress bar
    return DownloaderRet(
        data=file_name
    ) if file_name else DownloaderRet(
        code=RetCodeEnum.GeneralFailure.value,
        message="Download failed"
    )
