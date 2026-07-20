from typing import Any, TypeVar

from ktoolbox._enum import RetCodeEnum
from ktoolbox.api.errors import PawchiveResponseValidationError, PawchiveTransportError
from ktoolbox.utils import BaseRet

__all__ = ["ActionRet", "action_error"]

_T = TypeVar("_T")


class ActionRet(BaseRet[_T]):
    """Return data model of action call"""

    pass


def action_error(error: Exception) -> ActionRet[Any]:
    """Convert a typed API failure into the existing action result boundary."""
    if isinstance(error, PawchiveTransportError):
        code = RetCodeEnum.NetWorkError
    elif isinstance(error, PawchiveResponseValidationError):
        code = RetCodeEnum.ValidationError
    else:
        code = RetCodeEnum.GeneralFailure
    return ActionRet(code=code, message=str(error), exception=error)
