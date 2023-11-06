from typing import TypeVar

from ktoolbox.utils import BaseRet

__all__ = ["ActionRet"]

_T = TypeVar("_T")


class ActionRet(BaseRet[_T]):
    """Return data model of action call"""
    pass
