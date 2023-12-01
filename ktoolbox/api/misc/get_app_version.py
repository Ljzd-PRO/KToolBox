from ktoolbox.api import BaseAPI, APIRet
from ktoolbox.model import RootModel

__all__ = ["GetAppVersion", "get_app_version"]


class GetAppVersion(BaseAPI):
    path = "/app_version"
    method = "get"

    class Response(RootModel[str]):
        __root__: str

    extra_validator = RootModel.parse_obj

    @classmethod
    async def __call__(cls) -> APIRet[str]:
        return await cls.request()


get_app_version = GetAppVersion.__call__
"""Show current App commit hash"""
