from enum import StrEnum, IntEnum

__all__ = ["TextEnum", "RetCodeEnum", "PostFileTypeEnum", "DataStorageNameEnum"]


class TextEnum(StrEnum):
    SearchResultEmpty = str(None)


class RetCodeEnum(IntEnum):
    Success = 0
    GeneralFailure = -1

    # APIRet
    NetWorkError = 100
    JsonDecodeError = 200
    ValidationError = 300


class PostFileTypeEnum(StrEnum):
    Attachment = "attachment"
    File = "file"


# noinspection SpellCheckingInspection
class DataStorageNameEnum(StrEnum):
    PostData = "post.json"
    CreatorIndicesData = "creator-indices.ktoolbox"
