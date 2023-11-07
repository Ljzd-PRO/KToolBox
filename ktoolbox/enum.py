from enum import StrEnum, IntEnum

__all__ = ["TextEnum", "RetCodeEnum", "PostFileTypeEnum", "DataStorageNameEnum"]


class TextEnum(StrEnum):
    SearchResultEmpty = str(None)


class RetCodeEnum(IntEnum):
    """Enum for `BaseRet.code`"""
    Success = 0
    GeneralFailure = -1

    # APIRet
    NetWorkError = 100
    JsonDecodeError = 200
    ValidationError = 300


class PostFileTypeEnum(StrEnum):
    # noinspection SpellCheckingInspection
    """File types of Kemono post files"""
    Attachment = "attachment"
    File = "file"


# noinspection SpellCheckingInspection
class DataStorageNameEnum(StrEnum):
    """File names for saving KToolBox data files"""
    PostData = "post.json"
    CreatorIndicesData = "creator-indices.ktoolbox"
    JobListData = "job-list.ktoolbox"
    LogData = "ktoolbox.log"
