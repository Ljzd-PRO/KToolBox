from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["config", "Configuration"]


class APIConfiguration(BaseModel):
    scheme: Literal["http", "https"] = "https"
    # noinspection SpellCheckingInspection
    netloc: str = "kemono.su"
    # noinspection SpellCheckingInspection
    statics_host: str = "img.kemono.su"
    path: str = "/api/v1"
    timeout: float = 5.0
    retry_times: int = 3
    retry_interval: float = 2.0


class Configuration(BaseSettings):
    api: APIConfiguration = APIConfiguration()

    # noinspection SpellCheckingInspection
    model_config = SettingsConfigDict(
        env_prefix='ktoolbox_',
        env_nested_delimiter='__',
        env_file='.env',
        env_file_encoding='utf-8'
    )


config = Configuration(_env_file='prod.env')
