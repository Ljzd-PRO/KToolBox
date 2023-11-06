from pydantic import RootModel

from ktoolbox.api import BaseAPI, APIRet

__all__ = ["GetAppVersion", "get_app_version"]


class GetAppVersion(BaseAPI):
    path = "/app_version"
    method = "get"

    class Response(RootModel[str]):
        root: str

    extra_validator = Response.model_validate_strings

    @classmethod
    async def __call__(cls) -> APIRet[str]:
        return await cls.request()


get_app_version = GetAppVersion.__call__
"""Show current App commit hash"""
