from typing import Literal

from pydantic import BaseModel

__all__ = ["config", "Configuration"]


class Configuration(BaseModel):
    api_scheme: Literal["http", "https"] = "https"
    # noinspection SpellCheckingInspection
    api_netloc: str = "kemono.su"
    api_path: str = "/api/v1"
    api_timeout: float = 5.0
    api_retry_times: int = 3
    api_retry_interval: float = 2.0

    # noinspection SpellCheckingInspection
    statics_host: str = "img.kemono.su"


config = Configuration()
