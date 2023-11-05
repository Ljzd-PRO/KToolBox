from enum import IntEnum

__all__ = ["APIRetCodeEnum"]


class APIRetCodeEnum(IntEnum):
    Success = 0
    NetWorkError = 100
    JsonDecodeError = 200
    ValidationError = 300
