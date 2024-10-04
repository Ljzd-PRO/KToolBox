import datetime
import logging
import os
import tempfile
import warnings
from pathlib import Path
from typing import Literal, Union, Optional, Set

from loguru import logger
from pydantic import BaseModel, model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    "config",
    "APIConfiguration",
    "DownloaderConfiguration",
    "PostStructureConfiguration",
    "JobConfiguration",
    "LoggerConfiguration",
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
    :ivar retry_times: Downloader retry times (when download failed)
    :ivar retry_stop_never: Never stop downloader from retrying (when download failed) \
    (``retry_times`` will be ignored when enabled)
    :ivar retry_interval: Seconds of downloader retry interval
    :ivar use_bucket: Enable local storage bucket mode
    :ivar bucket_path: Path of local storage bucket
    """
    scheme: Literal["http", "https"] = "https"
    timeout: float = 30.0
    encoding: str = "utf-8"
    buffer_size: int = 20480
    chunk_size: int = 1024
    temp_suffix: str = "tmp"
    retry_times: int = 10
    retry_stop_never: bool = False
    retry_interval: float = 3.0
    use_bucket: bool = False
    bucket_path: Path = Path("./.ktoolbox/bucket_storage")

    @model_validator(mode="after")
    def check_bucket_path(self) -> "DownloaderConfiguration":
        if self.use_bucket:
            # noinspection PyBroadException
            try:
                bucket_path = Path(self.bucket_path)
                bucket_path.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryFile(dir=bucket_path) as temp_file:
                    temp_link_file_path = f"{bucket_path / temp_file.name}.hlink"
                    os.link(temp_file.name, temp_link_file_path)
                    os.remove(temp_link_file_path)
            except Exception:
                self.use_bucket = False
                logger.exception(f"`DownloaderConfiguration.bucket_path` is not available, "
                                 f"`DownloaderConfiguration.use_bucket` has been disabled.")
        return self


class PostStructureConfiguration(BaseModel):
    # noinspection SpellCheckingInspection
    """
    Post path structure model

    - Default:
    ```
    ..
    ├─ content.txt
    ├─ <Post file>
    ├─ <Post data (post.json)>
    └─ attachments
       ├─ 1.png
       └─ 2.png
    ```

    :ivar attachments: Sub path of attachment directory
    :ivar content_filepath: Sub path of post content file
    """
    attachments: Path = Path("attachments")
    content_filepath: Path = Path("content.txt")


class JobConfiguration(BaseModel):
    """
    Download jobs Configuration

    - Available properties for ``post_dirname_format``

        | Property      | Type   |
        |---------------|--------|
        | ``id``        | String |
        | ``user``      | String |
        | ``service``   | String |
        | ``title``     | String |
        | ``added``     | Date   |
        | ``published`` | Date   |
        | ``edited``    | Date   |

    :ivar count: Number of coroutines for concurrent download
    :ivar post_id_as_path: (**Deprecated**) Use post ID as post directory name
    :ivar post_dirname_format: Customize the post directory name format, you can use some of the \
    [properties][ktoolbox.configuration.JobConfiguration] in ``Post``. \
    e.g. ``[{published}]{id}`` > ``[2024-1-1]123123``, ``{user}_{published}_{title}`` > ``234234_2024-1-1_HelloWorld``
    :ivar post_structure: Post path structure
    :ivar mix_posts: Save all files from different posts at same path in creator directory. \
    It would not create any post directory, and ``CreatorIndices`` would not been recorded.
    :ivar sequential_filename: Rename attachments in numerical order, e.g. ``1.png``, ``2.png``, ...
    :ivar filename_format: Customize the filename format by inserting an empty ``{}`` to represent the basic filename.
    Similar to post_dirname_format, you can use some of the [properties][ktoolbox.configuration.JobConfiguration] \
    in Post. For example: ``{title}_{}`` could result in filenames like \
    ``HelloWorld_b4b41de2-8736-480d-b5c3-ebf0d917561b``, ``HelloWorld_af349b25-ac08-46d7-98fb-6ce99a237b90``, etc. \
    You can also use it with ``sequential_filename``. For instance, \
    ``[{published}]_{}`` could result in filenames like ``[2024-1-1]_1.png``, ``[2024-1-1]_2.png``, etc.
    :ivar allow_list: Download files which match these patterns (Unix shell-style), e.g. ``["*.png"]``
    :ivar block_list: Not to download files which match these patterns (Unix shell-style), e.g. ``["*.psd","*.zip"]``
    """
    count: int = 4
    post_id_as_path: bool = False
    post_dirname_format: str = "{title}"
    post_structure: PostStructureConfiguration = PostStructureConfiguration()
    mix_posts: bool = False
    sequential_filename: bool = False
    filename_format: str = "{}"
    allow_list: Set[str] = set()
    block_list: Set[str] = set()

    # job_list_filepath: Optional[Path] = None
    # """Filepath for job list data saving, ``None`` for disable job list saving"""

    @field_validator("post_id_as_path")
    def post_id_as_path_validator(cls, v):
        if v != cls.model_fields["post_id_as_path"].default:
            warnings.warn(
                "`JobConfiguration.post_id_as_path` is deprecated and is scheduled for removal in further version. "
                "Use `JobConfiguration.post_dirname_format` instead",
                FutureWarning
            )


class LoggerConfiguration(BaseModel):
    """
    Logger configuration

    :ivar path: Path to save logs, ``None`` for disable log file output
    :ivar level: Log filter level
    :ivar rotation: Log rotation
    """
    path: Optional[Path] = None
    level: Union[str, int] = logging.DEBUG
    rotation: Union[str, int, datetime.time, datetime.timedelta] = "1 week"


class Configuration(BaseSettings):
    # noinspection SpellCheckingInspection,GrazieInspection
    """
    KToolBox Configuration

    :ivar api: Kemono API Configuration
    :ivar downloader: File Downloader Configuration
    :ivar job: Download jobs Configuration
    :ivar logger: Logger configuration
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

    # noinspection SpellCheckingInspection
    model_config = SettingsConfigDict(
        env_prefix='ktoolbox_',
        env_nested_delimiter='__',
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )


config = Configuration(_env_file=['.env', 'prod.env'])
