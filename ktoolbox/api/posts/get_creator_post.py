from typing import List

from ktoolbox.api import BaseAPI, APIRet
from ktoolbox.api.model import Post
from ktoolbox.model import RootModel

__all__ = ["GetCreatorPost", "get_creator_post"]


class GetCreatorPost(BaseAPI):
    path = "/{service}/user/{creator_id}"
    method = "get"

    class Response(RootModel[List[Post]]):
        __root__: List[Post]

    @classmethod
    async def __call__(cls, service: str, creator_id: str, *, q: str = None, o: int = None) -> APIRet[List[Post]]:
        """
        Get a list of creator posts

        :param service: The service where the post is located
        :param creator_id: The ID of the creator
        :param q: Search query
        :param o: Result offset, stepping of 50 is enforced
        """
        return await cls.request(
            path=cls.path.format(service=service, creator_id=creator_id),
            params={
                "q": q,
                "o": o
            }
        )


get_creator_post = GetCreatorPost.__call__
