import datetime
import logging
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Literal, cast

from loguru import logger
from pydantic import BaseModel, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    "config",
    "APIConfiguration",
    "DownloaderConfiguration",
    "PostStructureConfiguration",
    "JobConfiguration",
    "LoggerConfiguration",
    "WebUIConfiguration",
    "Configuration",
    "RuntimeContext",
    "active_configuration",
    "configuration_scope",
    "load_configuration",
]


# noinspection SpellCheckingInspection,GrazieInspection
class APIConfiguration(BaseModel):
    """
    Pawchive API Configuration

    :ivar scheme: Pawchive API URL scheme
    :ivar netloc: Pawchive API URL netloc
    :ivar statics_netloc: Pawchive host for static creator assets
    :ivar path: Pawchive API URL root path
    :ivar timeout: API request timeout
    :ivar retry_times: API request retry times (when request failed)
    :ivar retry_interval: Seconds of API request retry interval
    """

    scheme: Literal["http", "https"] = "https"
    netloc: str = "pawchive.pw"
    statics_netloc: str = "pawchive.pw"
    path: str = "/api/v1"
    timeout: float = 5.0
    retry_times: int = 3
    retry_interval: float = 2.0


class DownloaderConfiguration(BaseModel):
    """
    File Downloader Configuration

    :ivar scheme: Downloader URL scheme
    :ivar files_netloc: Pawchive host for post files
    :ivar file_path_prefix: Path prepended to file paths returned by the API
    :ivar session_key: Optional session cookie sent only to the file host
    :ivar timeout: Downloader request timeout
    :ivar encoding: Charset for filename parsing and post ``content``, ``external_links`` saving
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
    For example: ``https://example.com/{}`` will be \
    ``https://example.com/https://file.pawchive.pw/data/66/83/xxxxx.jpg``; \
    ``https://example.com/?url={}`` will be \
    ``https://example.com/?url=https://file.pawchive.pw/data/66/83/xxxxx.jpg``
    :ivar keep_metadata: Keep the file metadata when downloading files (e.g. last modified time, etc.)
    """

    scheme: Literal["http", "https"] = "https"
    files_netloc: str = "file.pawchive.pw"
    file_path_prefix: str = "/data"
    session_key: str = ""
    timeout: float = 30.0
    encoding: str = "utf-8"
    buffer_size: int = 20480
    chunk_size: int = 1024
    temp_suffix: str = "tmp"
    retry_times: int = 10
    retry_stop_never: bool = False
    retry_interval: float = 3.0
    tps_limit: float = 5.0
    use_bucket: bool = False
    bucket_path: Path = Path("./.ktoolbox/bucket_storage")
    reverse_proxy: str = "{}"
    keep_metadata: bool = True

    @model_validator(mode="after")
    def check_bucket_path(self) -> "DownloaderConfiguration":
        if self.use_bucket:
            temp_path: Path | None = None
            temp_link_path: Path | None = None
            try:
                bucket_path = Path(self.bucket_path)
                bucket_path.mkdir(parents=True, exist_ok=True)
                file_descriptor, temp_name = tempfile.mkstemp(dir=bucket_path)
                os.close(file_descriptor)
                temp_path = Path(temp_name)
                temp_link_path = Path(f"{temp_name}.hlink")
                os.link(temp_path, temp_link_path)
            except Exception:
                self.use_bucket = False
                logger.exception(
                    "`DownloaderConfiguration.bucket_path` is not available, "
                    "`DownloaderConfiguration.use_bucket` has been disabled."
                )
            finally:
                if temp_link_path is not None:
                    temp_link_path.unlink(missing_ok=True)
                if temp_path is not None:
                    temp_path.unlink(missing_ok=True)
        return self


class PostStructureConfiguration(BaseModel):
    # noinspection SpellCheckingInspection,GrazieInspection
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
    ``TheTitle_Stelle_lv5_logo.gif``, ``TheTitle_ScxHjZIdxt5cnjaAwf3ql2p7.jpg``, etc. \
    Meanwhile, you can also use the formatting feature of the Python Format Specification Mini-Language, for example: \
    ``{title:.6}_{}`` could shorten the title length to 6 characters like \
    ``HiEveryoneThisIsALongTitle_ScxHjZIdxt5cnjaAwf3ql2p7.jpg`` to ``HiEver_ScxHjZIdxt5cnjaAwf3ql2p7.jpg``
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

    - Python Format Specification Mini-Language reference:

        https://docs.python.org/3.13/library/string.html#format-specification-mini-language

    :ivar count: Number of coroutines for concurrent download
    :ivar include_revisions: Include and download revision posts when available
    :ivar post_dirname_format: Customize the post directory name format, you can use some of the \
    [properties][ktoolbox.configuration.JobConfiguration] in ``Post``. \
    e.g. ``[{published}]{id}`` could result dirname ``[2024-1-1]123123``, \
    ``{user}_{published}_{title}`` could result dirname like ``234234_2024-1-1_TheTitle``. \
    Meanwhile, you can also use the formatting feature of the Python Format Specification Mini-Language, for example: \
    ``{title:.6}`` could shorten the title length to 6 characters like ``HiEveryoneThisIsALongTitle`` to ``HiEver``
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
    ``[{published}]_{}`` could result in filenames like ``[2024-1-1]_1.png``, ``[2024-1-1]_2.png``, etc. \
    Meanwhile, you can also use the formatting feature of the Python Format Specification Mini-Language, for example: \
    ``{title:.6}`` could shorten the title length to 6 characters like ``HiEveryoneThisIsALongTitle`` to ``HiEver``
    :ivar allow_list: Download files which match these patterns (Unix shell-style), e.g. ``["*.png"]``
    :ivar block_list: Not to download files which match these patterns (Unix shell-style), e.g. ``["*.psd","*.zip"]``
    :ivar extract_content: Extract post content and save to separate file (filename was defined in ``config.job.post_structure.content``)
    :ivar extract_content_images: Extract images from post content and download them.
    :ivar extract_external_links: Extract external file sharing links from post content and save to separate file \
    (filename was defined in ``config.job.post_structure.external_links``)
    :ivar external_link_patterns: Regex patterns for extracting external links.
    :ivar group_by_year: Group posts by year in separate directories based on published date
    :ivar group_by_month: Group posts by month in separate directories based on published date (requires group_by_year)
    :ivar year_dirname_format: Customize the year directory name format. Available properties: ``year``. \
    e.g. ``{year}`` > ``2024``, ``Year_{year}`` > ``Year_2024``
    :ivar month_dirname_format: Customize the month directory name format. Available properties: ``year``, ``month``. \
    e.g. ``{year}-{month}`` > ``2024-01``, ``{year}_{month}`` > ``2024_01``
    :ivar keywords: keywords to filter posts by title (case-insensitive)
    :ivar keywords_exclude: Deprecated title exclusions converted to an implicit global field-match blocker. \
    Define structured blockers in ``ktoolbox.toml`` instead.
    :ivar creator_concurrency: Maximum number of creators fetched and prepared concurrently
    :ivar download_file: Download post file (usually cover image). Set to False to skip file downloads.
    :ivar download_attachments: Download post attachments. Set to False to skip attachment downloads.
    :ivar min_file_size: Minimum file size in bytes to download. Files smaller than this will be skipped. \
    Set to None to disable minimum size filtering.
    :ivar max_file_size: Maximum file size in bytes to download. Files larger than this will be skipped. \
    Set to None to disable maximum size filtering.
    """

    count: int = Field(default=4, ge=1, le=64)
    creator_concurrency: int = Field(default=4, ge=1, le=64)
    include_revisions: bool = False
    post_dirname_format: str = "{title}"
    post_structure: PostStructureConfiguration = PostStructureConfiguration()
    mix_posts: bool = False
    sequential_filename: bool = False
    sequential_filename_excludes: set[str] = Field(default_factory=set)
    filename_format: str = "{}"
    # noinspection PyDataclass
    allow_list: set[str] = Field(default_factory=set)
    # noinspection PyDataclass
    block_list: set[str] = Field(default_factory=set)
    extract_content: bool = False
    extract_content_images: bool = False
    extract_external_links: bool = False
    # noinspection SpellCheckingInspection
    external_link_patterns: list[str] = [
        # Google Drive
        r"https?://drive\.google\.com/[^\s]+",
        r"https?://docs\.google\.com/[^\s]+",
        # MEGA
        r"https?://mega\.nz/[^\s]+",
        r"https?://mega\.co\.nz/[^\s]+",
        # Dropbox
        r"https?://(?:www\.)?dropbox\.com/[^\s]+",
        r"https?://db\.tt/[^\s]+",
        # OneDrive
        r"https?://onedrive\.live\.com/[^\s]+",
        r"https?://1drv\.ms/[^\s]+",
        # MediaFire
        r"https?://(?:www\.)?mediafire\.com/[^\s]+",
        # WeTransfer
        r"https?://(?:www\.)?wetransfer\.com/[^\s]+",
        r"https?://we\.tl/[^\s]+",
        # SendSpace
        r"https?://(?:www\.)?sendspace\.com/[^\s]+",
        # 4shared
        r"https?://(?:www\.)?4shared\.com/[^\s]+",
        # Zippyshare
        r"https?://(?:www\.)?zippyshare\.com/[^\s]+",
        # Uploadfiles.io
        r"https?://(?:www\.)?uploadfiles\.io/[^\s]+",
        # Box
        r"https?://(?:www\.)?box\.com/[^\s]+",
        # pCloud
        r"https?://(?:www\.)?pcloud\.com/[^\s]+",
        # Yandex Disk
        r"https?://disk\.yandex\.[a-z]+/[^\s]+",
        # Generic patterns for other file hosting services
        r"https?://[^\s]*(?:file|upload|share|download|drive|storage)[^\s]*\.[a-z]{2,4}/[^\s]+",
    ]
    group_by_year: bool = False
    group_by_month: bool = False
    year_dirname_format: str = "{year}"
    month_dirname_format: str = "{year}-{month:02d}"
    keywords: set[str] = Field(default_factory=set)
    keywords_exclude: set[str] = Field(default_factory=set)
    download_file: bool = True
    download_attachments: bool = True
    min_file_size: int | None = None
    max_file_size: int | None = None


class LoggerConfiguration(BaseModel):
    """
    Logger configuration

    :ivar path: Directory where ``ktoolbox.log`` is saved, ``None`` to disable log file output
    :ivar level: Log filter level
    :ivar rotation: Log rotation
    """

    path: Path | None = None
    level: str | int = logging.getLevelName(logging.DEBUG)
    rotation: str | int | datetime.time | datetime.timedelta = "1 week"


class WebUIConfiguration(BaseModel):
    """
    WebUI configuration

    :ivar host: Interface used by the WebUI HTTP server
    :ivar port: TCP port used by the WebUI HTTP server
    :ivar open_browser: Open the WebUI in the default browser after startup
    :ivar username: Username of the single WebUI account; startup uses ``admin`` when empty
    :ivar password_hash: Preferred Argon2id password hash for the WebUI account
    :ivar password: Plaintext compatibility password; startup generates one when both password forms are empty
    :ivar max_active_tasks: Maximum number of top-level sync or download tasks running concurrently
    :ivar session_idle_hours: Session lifetime in hours since its most recent use
    :ivar session_absolute_hours: Maximum session lifetime in hours since login
    """

    host: str = "0.0.0.0"
    port: int = Field(default=8789, ge=1, le=65535)
    open_browser: bool = True
    username: str = ""
    password_hash: SecretStr = SecretStr("")
    password: SecretStr = SecretStr("")
    max_active_tasks: int = Field(default=2, ge=1, le=16)
    session_idle_hours: int = Field(default=24, ge=1, le=24 * 30)
    session_absolute_hours: int = Field(default=24 * 7, ge=1, le=24 * 90)


class Configuration(BaseSettings):
    # noinspection SpellCheckingInspection,GrazieInspection
    """
    KToolBox Configuration

    :ivar api: Pawchive API Configuration
    :ivar downloader: File Downloader Configuration
    :ivar job: Download jobs Configuration
    :ivar logger: Logger configuration
    :ivar webui: Local WebUI server and account configuration
    :ivar ssl_verify: Enable SSL certificate verification for the Pawchive API and file servers
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
    webui: WebUIConfiguration = WebUIConfiguration()

    ssl_verify: bool = True
    json_dump_indent: int = 4
    use_uvloop: bool = True

    # noinspection SpellCheckingInspection
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="ktoolbox_",
        env_nested_delimiter="__",
        env_file=[".env", "prod.env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )


def load_configuration(project_root: Path | str) -> Configuration:
    """Load an isolated configuration using dotenv files from one project root."""
    root = Path(project_root).expanduser().resolve()
    env_files = [root / ".env", root / "prod.env"]
    return Configuration(_env_file=env_files)


_default_configuration = Configuration()
_active_configuration: ContextVar[Configuration] = ContextVar(
    "ktoolbox_active_configuration",
    default=_default_configuration,
)


def active_configuration() -> Configuration:
    """Return the configuration active in the current async context."""
    return _active_configuration.get()


@contextmanager
def configuration_scope(configuration: Configuration) -> Iterator[Configuration]:
    """Activate an isolated configuration for this context and its child tasks."""
    token: Token[Configuration] = _active_configuration.set(configuration)
    try:
        yield configuration
    finally:
        _active_configuration.reset(token)


class _ActiveConfigurationProxy:
    """Compatibility proxy that resolves legacy ``config`` access per context."""

    model_fields = Configuration.model_fields

    def __getattr__(self, name: str) -> Any:
        return getattr(active_configuration(), name)

    def __setattr__(self, name: str, value: object) -> None:
        setattr(active_configuration(), name, value)

    def __repr__(self) -> str:
        return repr(active_configuration())


config = cast(Configuration, _ActiveConfigurationProxy())


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    """Project root and immutable-at-dispatch configuration for one operation."""

    project_root: Path
    configuration: Configuration

    @classmethod
    def from_project(cls, project_root: Path | str) -> "RuntimeContext":
        root = Path(project_root).expanduser().resolve()
        return cls(project_root=root, configuration=load_configuration(root))

    @contextmanager
    def activate(self) -> Iterator[Configuration]:
        with configuration_scope(self.configuration):
            yield self.configuration

    def snapshot(self) -> "RuntimeContext":
        return RuntimeContext(self.project_root, self.configuration.model_copy(deep=True))

    def redacted_configuration(self) -> dict[str, object]:
        return self.configuration.model_dump(
            mode="json",
            exclude={
                "downloader": {"session_key"},
                "webui": {"password", "password_hash"},
            },
        )
