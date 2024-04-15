from typing import List

from ktoolbox.api import BaseAPI, APIRet
from ktoolbox.api.model import Creator
from ktoolbox.model import RootModel

__all__ = ["GetCreators", "get_creators"]


class GetCreators(BaseAPI):
    """List All Creators"""
    path = "/creators.txt"
    method = "get"

    class Response(RootModel[List[Creator]]):
        __root__: List[Creator]

    @classmethod
    async def __call__(cls) -> APIRet[List[Creator]]:
        """
        List of all creators

        List all creators with details. I blame DDG for .txt.
        """
        return await cls.request()


get_creators = GetCreators.__call__
