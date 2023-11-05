from typing import TypeVar

from k_tool_box.utils import BaseRet

__all__ = ["ActionRet"]

_T = TypeVar("_T")


class ActionRet(BaseRet[_T]):
    """Return data model of action call"""
    pass
