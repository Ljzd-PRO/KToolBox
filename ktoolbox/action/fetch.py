from typing import AsyncGenerator, List, Any

from ktoolbox.api.model import Post
from ktoolbox.api.posts import get_creator_post
from ktoolbox.api.utils import SEARCH_STEP
from ktoolbox.utils import BaseRet

__all__ = ["FetchInterruptError", "fetch_creator_posts"]


class FetchInterruptError(Exception):
    """Exception for interrupt of data fetching"""

    def __init__(self, *args, ret: BaseRet = None):
        super().__init__(*args)
        self.ret = ret


async def fetch_creator_posts(service: str, creator_id: str, o: int = 0) -> AsyncGenerator[List[Post], Any]:
    """
    Fetch posts from a creator

    :param service: The service where the post is located
    :param creator_id: The ID of the creator
    :param o: Result offset, stepping of 50 is enforced
    :return: Async generator of several list of posts
    :raise FetchInterruptError: Exception for interrupt of data fetching
    """
    while True:
        ret = await get_creator_post(service=service, creator_id=creator_id, o=o)
        if ret:
            yield ret.data
            if len(ret.data) < SEARCH_STEP:
                break
            else:
                o += SEARCH_STEP
        else:
            raise FetchInterruptError(ret=ret)
