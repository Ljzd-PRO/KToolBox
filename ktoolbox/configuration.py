import datetime
import logging
from pathlib import Path
from typing import Literal, Union, Optional

from pydantic import BaseModel, BaseSettings

__all__ = [
    "config",
    "APIConfiguration",
    "DownloaderConfiguration",
    "PostStructureConfiguration",
    "JobConfiguration",
    "Configuration"
]


# noinspection SpellCheckingInspection,GrazieInspection
class APIConfiguration(BaseModel):
    """
    Kemono API Configuration

    :ivar scheme: Kemono API URL scheme
    :ivar netloc: Kemono API URL netloc
    :ivar statics_netloc: URL netloc of Kemono server for static files (e.g. images)
    :ivar files_netloc: URL netloc of Kemono server for post files
    :ivar path: Kemono API URL root path
    :ivar timeout: API request timeout
    :ivar retry_times: API request retry times (when request failed)
    :ivar retry_interval: Seconds of API request retry interval
    """
    scheme: Literal["http", "https"] = "https"
    netloc: str = "kemono.su"
    statics_netloc: str = "img.kemono.su"
    files_netloc: str = "kemono.su"
    path: str = "/api/v1"
    timeout: float = 5.0
    retry_times: int = 3
    retry_interval: float = 2.0


class DownloaderConfiguration(BaseModel):
    """
    File Downloader Configuration

    :ivar scheme: Downloader URL scheme
    :ivar timeout: Downloader request timeout
    :ivar encoding: Charset for filename parsing and post content text saving
    :ivar buffer_size: Number of bytes of file I/O buffer for each downloading file
    :ivar chunk_size: Number of bytes of chunk of downloader stream
    :ivar temp_suffix: Temp filename suffix of downloading files
    """
    scheme: Literal["http", "https"] = "https"
    timeout: float = 30.0
    encoding: str = "utf-8"
    buffer_size: int = 20480
    chunk_size: int = 1024
    temp_suffix: str = "tmp"


class PostStructureConfiguration(BaseModel):
    # noinspection SpellCheckingInspection
    """
    Post path structure model

    - Default:
    ```
    |-- ..
    |-- attachments
    |   |-- 1.png
    |   |-- 2.png
    |-- content.txt
    |-- <Post file>
    |-- <Post data (post.ktoolbox.json)>
    ```

    :ivar attachments: Sub path of attachment directory
    :ivar content_filepath: Sub path of post content HTML file
    """
    attachments: Path = Path("attachments")
    content_filepath: Path = Path("index.html")


class JobConfiguration(BaseModel):
    """
    Download jobs Configuration

    :ivar count: Number of coroutines for concurrent download
    :ivar post_id_as_path: Use post ID as post directory name
    :ivar post_structure: Post path structure
    :ivar mix_posts: Save all files from different posts at same path in creator directory. \
    It would not create any post directory, and ``CreatorIndices`` would not been recorded, \
    without ``CreatorIndices`` you **cannot update** the creator directory.
    :ivar job_list_filepath: Filepath for job list data saving, ``None`` for disable job list saving
    """
    count: int = 4
    post_id_as_path: bool = False
    post_structure: PostStructureConfiguration = PostStructureConfiguration()
    mix_posts: bool = False
    job_list_filepath: Optional[Path] = None


class LoggerConfiguration(BaseModel):
    """
    Logger configuration

    :ivar path: Path to save logs, ``None`` for disable log file output
    :ivar level: Log filter level
    :ivar rotation: Log rotation
    """
    path: Optional[Path] = Path("logs")
    level: Union[str, int] = logging.DEBUG
    rotation: Union[str, int, datetime.time, datetime.timedelta] = "1 week"


class Configuration(BaseSettings):
    # noinspection SpellCheckingInspection,GrazieInspection
    """
    KToolBox Configuration

    :ivar api:
    :ivar downloader:
    :ivar job:
    :ivar logger:
    :ivar ssl_verify: Enable SSL certificate verification for Kemono API server and download server
    :ivar json_dump_indent: Indent of JSON file dump
    :ivar use_uvloop: Use uvloop for asyncio (Disabled on Windows by default) \
    uvloop will improve concurrent performance, but it is not compatible with Windows. \
    Install uvloop by `pip install ktoolbox[uvloop]` or it will not work.
    """
    api: APIConfiguration = APIConfiguration()
    downloader: DownloaderConfiguration = DownloaderConfiguration()
    job: JobConfiguration = JobConfiguration()
    logger: LoggerConfiguration = LoggerConfiguration()

    ssl_verify: bool = True
    json_dump_indent: int = 4
    use_uvloop: bool = True

    class Config(BaseSettings.Config):
        env_prefix = 'ktoolbox_'
        env_nested_delimiter = '__'
        env_file = '.env'
        env_file_encoding = 'utf-8'


config = Configuration(_env_file='prod.env')
