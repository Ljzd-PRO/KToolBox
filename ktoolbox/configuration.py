import datetime
import logging
from pathlib import Path
from typing import Literal, Union, Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    "config",
    "APIConfiguration",
    "DownloaderConfiguration",
    "PostStructureConfiguration",
    "JobConfiguration",
    "Configuration"
]


# noinspection SpellCheckingInspection
class APIConfiguration(BaseModel):
    """Kemono API Configuration"""
    scheme: Literal["http", "https"] = "https"
    """Kemono API URL scheme"""
    netloc: str = "kemono.su"
    """Kemono API URL netloc"""
    statics_netloc: str = "img.kemono.su"
    """URL netloc of Kemono server for static files (e.g. images)"""
    files_netloc: str = "kemono.su"
    """URL netloc of Kemono server for post files"""
    path: str = "/api/v1"
    """Kemono API URL root path"""
    timeout: float = 5.0
    """API request timeout"""
    retry_times: int = 3
    """API request retry times (when request failed)"""
    retry_interval: float = 2.0
    """Seconds of API request retry interval"""


class DownloaderConfiguration(BaseModel):
    """File Downloader Configuration"""
    scheme: Literal["http", "https"] = "https"
    """Downloader URL scheme"""
    timeout: float = 30.0
    """Downloader request timeout"""
    encoding: str = "utf-8"
    """Charset for filename parsing and post content text saving"""
    buffer_size: int = 20480
    """Number of bytes of file I/O buffer for each downloading file"""
    chunk_size: int = 1024
    """Number of bytes of chunk of downloader stream"""
    temp_suffix: str = "tmp"
    """Temp filename suffix of downloading files"""


class PostStructureConfiguration(BaseModel):
    # noinspection SpellCheckingInspection
    """
    Post path structure model

    .. rubric:: Default:
    |__+ ..

    |__+ attachments

    |____+ (e.g. 1.png)

    |____+ (e.g. 2.png)

    |__+ content.txt

    |__+ <Post file>

    |__+ <Post data (post.ktoolbox.json)>
    """
    attachments: Path = Path("attachments")
    """Sub path of attachment directory"""
    content_filepath: Path = Path("index.html")
    """Sub path of post content HTML file"""


class JobConfiguration(BaseModel):
    """Download jobs Configuration"""
    count: int = 4
    """Number of coroutines for concurrent download"""
    post_id_as_name: bool = False
    """Use post ID as post directory name"""
    post_structure: PostStructureConfiguration = PostStructureConfiguration()
    """Post path structure"""
    mix_posts: bool = False
    """
    Save all files from different posts at same path in creator directory

    .. rubric:: NOTICE:
    It would not create any post directory, and ``CreatorIndices`` would not been recorded, \
    without ``CreatorIndices`` you **cannot update** the creator directory.
    """
    job_list_filepath: Optional[Path] = None
    """Filepath for job list data saving, ``None`` for disable job list saving"""


class LoggerConfiguration(BaseModel):
    """Logger configuration"""
    path: Optional[Path] = Path("logs")
    """Path to save logs, ``None`` for disable log file output"""
    level: Union[str, int] = logging.DEBUG
    """Log filter level"""
    rotation: Union[str, int, datetime.time, datetime.timedelta] = "1 week"
    """Log rotation"""


class Configuration(BaseSettings):
    """KToolBox Configuration"""
    api: APIConfiguration = APIConfiguration()
    downloader: DownloaderConfiguration = DownloaderConfiguration()
    job: JobConfiguration = JobConfiguration()
    logger: LoggerConfiguration = LoggerConfiguration()

    json_dump_indent: int = 4
    """Indent of JSON file dump"""

    # noinspection SpellCheckingInspection
    model_config = SettingsConfigDict(
        env_prefix='ktoolbox_',
        env_nested_delimiter='__',
        env_file='.env',
        env_file_encoding='utf-8'
    )


config = Configuration(_env_file='prod.env')
