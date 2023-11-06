from typing import Generic, TypeVar, Optional

from pydantic import BaseModel, ConfigDict

__all__ = ["BaseRet"]

from ktoolbox.enum import RetCodeEnum

_T = TypeVar('_T')


class BaseRet(BaseModel, Generic[_T]):
    """Base data model of function return value"""
    code: int = RetCodeEnum.Success.value
    message: str = ''
    exception: Optional[Exception] = None
    data: Optional[_T] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __bool__(self):
        return self.code == RetCodeEnum.Success
