from enum import StrEnum, IntEnum

__all__ = ["TextEnum", "RetCodeEnum"]


class TextEnum(StrEnum):
    SearchResultEmpty = str(None)


class RetCodeEnum(IntEnum):
    Success = 0
    GeneralFailure = -1

    # APIRet
    NetWorkError = 100
    JsonDecodeError = 200
    ValidationError = 300
