from enum import IntEnum, Enum

__all__ = ["TextEnum", "RetCodeEnum", "PostFileTypeEnum", "DataStorageNameEnum"]


class TextEnum(Enum):
    SearchResultEmpty = str(None)
    MissingParams = "Required parameters are missing"


class RetCodeEnum(IntEnum):
    """Enum for ``BaseRet.code``"""
    Success = 0
    GeneralFailure = -1

    # APIRet
    NetWorkError = 1001
    JsonDecodeError = 1002
    ValidationError = 1003

    # ActionRet
    MissingParameter = 2001

    # DownloaderRet
    FileExisted = 3001


class PostFileTypeEnum(Enum):
    # noinspection SpellCheckingInspection
    """File types of Kemono post files"""
    Attachment = "attachment"
    File = "file"


# noinspection SpellCheckingInspection
class DataStorageNameEnum(Enum):
    """File names for saving KToolBox data files"""
    PostData = "post.json"
    CreatorIndicesData = "creator-indices.ktoolbox"
    JobListData = "job-list.ktoolbox"
    LogData = "ktoolbox.log"
