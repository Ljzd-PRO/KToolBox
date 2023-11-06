from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["config", "Configuration"]


# noinspection SpellCheckingInspection
class APIConfiguration(BaseModel):
    """Kemono API Configuration"""
    scheme: Literal["http", "https"] = "https"
    """Kemono API URL scheme"""
    netloc: str = "kemono.su"
    """Kemono API URL netloc"""
    statics_netloc: str = "img.kemono.su"
    """URL netloc of Kemono server for static files (e.g. images)"""
    attachment_netloc: str = "kemono.su"
    """URL netloc of Kemono server for post attachment files"""
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
    """Charset for filename parsing"""
    buffer_size: int = 1024
    """Number of bytes for file I/O buffer"""
    chunk_size: int = 1024
    """Number of bytes for chunk of downloader stream"""


class Configuration(BaseSettings):
    api: APIConfiguration = APIConfiguration()
    downloader: DownloaderConfiguration = DownloaderConfiguration()

    # noinspection SpellCheckingInspection
    model_config = SettingsConfigDict(
        env_prefix='ktoolbox_',
        env_nested_delimiter='__',
        env_file='.env',
        env_file_encoding='utf-8'
    )


config = Configuration(_env_file='prod.env')
