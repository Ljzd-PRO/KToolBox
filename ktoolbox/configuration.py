import datetime
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Literal, Union, Optional, Any, Set, List

from loguru import logger
from pydantic import BaseModel, BaseSettings, validator, Field

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
    :ivar session_key: Session key that can be found in cookies after a successful login
    """
    scheme: Literal["http", "https"] = "https"
    netloc: str = "kemono.cr"
    statics_netloc: str = "img.kemono.cr"
    files_netloc: str = "kemono.cr"
    path: str = "/api/v1"
    timeout: float = 5.0
    retry_times: int = 3
    retry_interval: float = 2.0
    session_key: str = ""


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
    :ivar tps_limit: Maximum connections established per second
    :ivar use_bucket: Enable local storage bucket mode
    :ivar bucket_path: Path of local storage bucket
    :ivar reverse_proxy: Reverse proxy format for download URL. \
    Customize the filename format by inserting an empty ``{}`` to represent the original URL. \
    For example: ``https://example.com/{}`` will be ``https://example.com/https://n1.kemono.su/data/66/83/xxxxx.jpg``;  \
    ``https://example.com/?url={}`` will be ``https://example.com/?url=https://n1.kemono.su/data/66/83/xxxxx.jpg``
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
    tps_limit: float = 1.0
    use_bucket: bool = False
    bucket_path: Path = Path("./.ktoolbox/bucket_storage")
    reverse_proxy: str = "{}"

    def __init__(self, /, **data: Any):
        super().__init__(**data)
        self.check_bucket_path()

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
    ├─ external_links.txt
    ├─ {id}_{}.png (file)
    ├─ post.json (metadata)
    ├─ attachments
    │    ├─ 1.png
    │    └─ 2.png
    └─ revisions
         ├─ <PostStructure>
         │    ├─ ...
         │    └─ ...
         └─ <PostStructure>
              ├─ ...
              └─ ...
    ```

    - Available properties for ``file``

        | Property      | Type   |
        |---------------|--------|
        | ``id``        | String |
        | ``user``      | String |
        | ``service``   | String |
        | ``title``     | String |
        | ``added``     | Date   |
        | ``published`` | Date   |
        | ``edited``    | Date   |

    :ivar attachments: Sub path of attachment directory
    :ivar content: Sub path of post content file
    :ivar external_links: Sub path of external links file (for cloud storage links found in content)
    :ivar file: The format of the post `file` filename (`file` is not `attachment`, each post has only one `file`, usually the cover image) \
    Customize the filename format by inserting an empty ``{}`` to represent the basic filename. \
    You can use some of the [properties][ktoolbox.configuration.JobConfiguration] \
    in Post. For example: ``{title}_{}`` could result in filenames like \
    ``TheTitle_Stelle_lv5_logo.gif``, ``TheTitle_ScxHjZIdxt5cnjaAwf3ql2p7.jpg``, etc.
    :ivar revisions: Sub path of revisions directory
    """
    attachments: Path = Path("attachments")
    content: Path = Path("content.txt")
    external_links: Path = Path("external_links.txt")
    file: str = "{id}_{}"
    revisions: Path = Path("revisions")


class JobConfiguration(BaseModel):
    """
    Download jobs Configuration

    - Available properties for ``post_dirname_format`` and ``filename_format``

        | Property      | Type   |
        |---------------|--------|
        | ``id``        | String |
        | ``user``      | String |
        | ``service``   | String |
        | ``title``     | String |
        | ``added``     | Date   |
        | ``published`` | Date   |
        | ``edited``    | Date   |

    - Available properties for ``year_dirname_format`` and ``month_dirname_format``

        | Property      | Type   |
        |---------------|--------|
        | ``year``      | String |
        | ``month``     | String |

    :ivar count: Number of coroutines for concurrent download
    :ivar include_revisions: Include and download revision posts when available
    :ivar post_dirname_format: Customize the post directory name format, you can use some of the \
    [properties][ktoolbox.configuration.JobConfiguration] in ``Post``. \
    e.g. ``[{published}]{id}`` > ``[2024-1-1]123123``, ``{user}_{published}_{title}`` > ``234234_2024-1-1_TheTitle``
    :ivar post_structure: Post path structure
    :ivar mix_posts: Save all files from different posts at same path in creator directory. \
    It would not create any post directory, and ``CreatorIndices`` would not been recorded.
    :ivar sequential_filename: Rename attachments in numerical order, e.g. ``1.png``, ``2.png``, ...
    :ivar sequential_filename_excludes: File extensions to exclude from sequential naming when ``sequential_filename`` is enabled. \
    Files with these extensions will keep their original names. e.g. ``[".psd", ".zip", ".mp4"]``
    :ivar filename_format: Customize the filename format by inserting an empty ``{}`` to represent the basic filename.
    Similar to post_dirname_format, you can use some of the [properties][ktoolbox.configuration.JobConfiguration] \
    in Post. For example: ``{title}_{}`` could result in filenames like \
    ``TheTitle_b4b41de2-8736-480d-b5c3-ebf0d917561b``, ``TheTitle_af349b25-ac08-46d7-98fb-6ce99a237b90``, etc. \
    You can also use it with ``sequential_filename``. For instance, \
    ``[{published}]_{}`` could result in filenames like ``[2024-1-1]_1.png``, ``[2024-1-1]_2.png``, etc.
    :ivar allow_list: Download files which match these patterns (Unix shell-style), e.g. ``["*.png"]``
    :ivar block_list: Not to download files which match these patterns (Unix shell-style), e.g. ``["*.psd","*.zip"]``
    :ivar extract_external_links: Extract external file sharing links from post content and save to separate file
    :ivar external_link_patterns: Regex patterns for extracting external links.
    :ivar group_by_year: Group posts by year in separate directories based on published date
    :ivar group_by_month: Group posts by month in separate directories based on published date (requires group_by_year)
    :ivar year_dirname_format: Customize the year directory name format. Available properties: ``year``. \
    e.g. ``{year}`` > ``2024``, ``Year_{year}`` > ``Year_2024``
    :ivar month_dirname_format: Customize the month directory name format. Available properties: ``year``, ``month``. \
    e.g. ``{year}-{month}`` > ``2024-01``, ``{year}_{month}`` > ``2024_01``
    :ivar keywords: keywords to filter posts by title (case-insensitive)
    :ivar keywords_exclude: keywords to exclude posts by title (case-insensitive)
    """
    count: int = 4
    include_revisions: bool = False
    post_dirname_format: str = "{title}"
    post_structure: PostStructureConfiguration = PostStructureConfiguration()
    mix_posts: bool = False
    sequential_filename: bool = False
    sequential_filename_excludes: Set[str] = Field(default_factory=set)
    filename_format: str = "{}"
    allow_list: Set[str] = Field(default_factory=set)
    block_list: Set[str] = Field(default_factory=set)
    extract_external_links: bool = True
    external_link_patterns: List[str] = [
        # Google Drive
        r'https?://drive\.google\.com/[^\s]+',
        r'https?://docs\.google\.com/[^\s]+',

        # MEGA
        r'https?://mega\.nz/[^\s]+',
        r'https?://mega\.co\.nz/[^\s]+',

        # Dropbox
        r'https?://(?:www\.)?dropbox\.com/[^\s]+',
        r'https?://db\.tt/[^\s]+',

        # OneDrive
        r'https?://onedrive\.live\.com/[^\s]+',
        r'https?://1drv\.ms/[^\s]+',

        # MediaFire
        r'https?://(?:www\.)?mediafire\.com/[^\s]+',

        # WeTransfer
        r'https?://(?:www\.)?wetransfer\.com/[^\s]+',
        r'https?://we\.tl/[^\s]+',

        # SendSpace
        r'https?://(?:www\.)?sendspace\.com/[^\s]+',

        # 4shared
        r'https?://(?:www\.)?4shared\.com/[^\s]+',

        # Zippyshare
        r'https?://(?:www\.)?zippyshare\.com/[^\s]+',

        # Uploadfiles.io
        r'https?://(?:www\.)?uploadfiles\.io/[^\s]+',

        # Box
        r'https?://(?:www\.)?box\.com/[^\s]+',

        # pCloud
        r'https?://(?:www\.)?pcloud\.com/[^\s]+',

        # Yandex Disk
        r'https?://disk\.yandex\.[a-z]+/[^\s]+',

        # Generic patterns for other file hosting services
        r'https?://[^\s]*(?:file|upload|share|download|drive|storage)[^\s]*\.[a-z]{2,4}/[^\s]+',
    ]
    group_by_year: bool = False
    group_by_month: bool = False
    year_dirname_format: str = "{year}"
    month_dirname_format: str = "{year}-{month:02d}"
    keywords: Set[str] = Field(default_factory=set)
    keywords_exclude: Set[str] = Field(default_factory=set)

    @validator("allow_list", "block_list", pre=True)
    def allow_block_list_validator(cls, v):
        return set(json.loads(v))

    @validator("external_link_patterns", pre=True)
    def external_link_patterns_validator(cls, v):
        return set(json.loads(v))


class LoggerConfiguration(BaseModel):
    """
    Logger configuration

    :ivar path: Path to save logs, ``None`` for disable log file output
    :ivar level: Log filter level
    :ivar rotation: Log rotation
    """
    path: Optional[Path] = None
    level: Union[str, int] = logging.getLevelName(logging.DEBUG)
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
    :ivar use_uvloop: Use uvloop/winloop for asyncio performance optimization \
    Uses winloop on Windows and uvloop on Unix-like systems for better concurrent performance. \
    Install winloop on Windows with `pip install ktoolbox[winloop]` \
    or uvloop on Unix with `pip install ktoolbox[uvloop]`.
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
        env_file = ['.env', 'prod.env']
        env_file_encoding = 'utf-8'


config = Configuration()
