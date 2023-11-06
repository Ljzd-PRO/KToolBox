from typing import TypeVar

from ktoolbox.utils import BaseRet

__all__ = ["DownloaderRet"]

_T = TypeVar("_T")


class DownloaderRet(BaseRet[_T]):
    """Return data model of action call"""
    pass
