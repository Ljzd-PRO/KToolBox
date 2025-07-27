from pydantic import BaseModel
from typing import Optional

from ktoolbox.api import BaseAPI, APIRet
from ktoolbox.api.model import Post

__all__ = ["GetPost", "get_post"]


class GetPost(BaseAPI):
    path = "/{service}/user/{creator_id}/post/{post_id}"
    method = "get"

    class Response(BaseModel):
        post: Post

    @classmethod
    async def __call__(cls, service: str, creator_id: str, post_id: str, revision_id: Optional[str] = None) -> APIRet[Response]:
        """
        Get a specific post or revision

        :param service: The service name
        :param creator_id: The creator's ID
        :param post_id: The post ID
        :param revision_id: The revision ID (optional, for revision posts)
        """
        if revision_id:
            path = f"/{service}/user/{creator_id}/post/{post_id}/revision/{revision_id}"
        else:
            path = cls.path.format(
                service=service,
                creator_id=creator_id,
                post_id=post_id
            )
        
        return await cls.request(path=path)


get_post = GetPost.__call__
