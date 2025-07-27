from typing import List

from pydantic import RootModel

from ktoolbox.api import BaseAPI, APIRet
from ktoolbox.api.model import Post

__all__ = ["SearchPosts", "search_posts"]


class SearchPosts(BaseAPI):
    path = "/posts"
    method = "get"

    class Response(RootModel[List[Post]]):
        root: List[Post]

    @classmethod
    async def __call__(cls, q: str, o: int = None) -> APIRet[List[Post]]:
        """
        Search for posts by query

        :param q: Search query
        :param o: Result offset, stepping of 50 is enforced
        """
        return await cls.request(
            path=cls.path,
            params={
                "q": q,
                "o": o
            }
        )


search_posts = SearchPosts.__call__