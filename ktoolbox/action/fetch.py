from typing import AsyncGenerator, List, Any

from ktoolbox.api.model import Post
from ktoolbox.api.posts import get_creator_post
from ktoolbox.api.utils import SEARCH_STEP
from ktoolbox.utils import BaseRet

__all__ = ["FetchInterruptError", "fetch_all_creator_posts"]


class FetchInterruptError(Exception):
    """Exception for interrupt of data fetching"""

    def __init__(self, *args, ret: BaseRet = None):
        super().__init__(*args)
        self.ret = ret


async def fetch_all_creator_posts(service: str, creator_id: str) -> AsyncGenerator[List[Post], Any]:
    """
    Fetch all posts from a creator

    :param service: The service where the post is located
    :param creator_id: The ID of the creator
    :return: Async generator of several list of posts
    :raise FetchInterruptError
    """
    o = 0
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
