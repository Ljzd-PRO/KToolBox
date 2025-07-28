from pydantic import BaseModel
from typing import List

from ktoolbox.api import BaseAPI, APIRet
from ktoolbox.api.model import Revision

__all__ = ["GetPostRevisions", "get_post_revisions"]


class GetPostRevisions(BaseAPI):
    path = "/{service}/user/{creator_id}/post/{post_id}/revisions"
    method = "get"

    class Response(BaseModel):
        revisions: List[Revision]

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


get_post_revisions = GetPostRevisions.__call__