from typing import TypeVar

from ktoolbox.utils import BaseRet

__all__ = ["DownloaderRet"]

_T = TypeVar("_T")


class DownloaderRet(BaseRet[_T]):
    """Return data model of action call"""

    status_code: int | None = None
    retry_after: float | None = None
    """Seconds the server asked us to wait (``Retry-After``), only set for HTTP 429"""
