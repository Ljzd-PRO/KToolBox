from typing import List, TypeVar

import httpx

from ktoolbox.api import BaseAPI, APIRet
from ktoolbox.api.model import Revision
from ktoolbox.model import RootModel

__all__ = ["GetPostRevisions", "get_post_revisions"]

_T = TypeVar('_T')


class GetPostRevisions(BaseAPI):
    path = "/{service}/user/{creator_id}/post/{post_id}/revisions"
    method = "get"

    class Response(RootModel[List[Revision]]):
        __root__: List[Revision]

    @classmethod
    async def __call__(cls, service: str, creator_id: str, post_id: str) -> APIRet[Response]:
        """
        Get all revisions of a specific post

        :param service: The service name
        :param creator_id: The creator's ID
        :param post_id: The post ID
        """
        path = cls.path.format(
            service=service,
            creator_id=creator_id,
            post_id=post_id
        )

        return await cls.request(path=path)

    @classmethod
    def handle_res(cls, res: httpx.Response) -> APIRet[_T]:
        return APIRet(data=[]) if res.status_code == 404 else super().handle_res(res)


get_post_revisions = GetPostRevisions.__call__
