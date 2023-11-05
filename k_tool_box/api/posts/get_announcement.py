from typing import List

from pydantic import RootModel

from k_tool_box.api import BaseAPI, APIRet
from k_tool_box.api.model import Announcement

__all__ = ["GetAnnouncement", "get_announcement"]


class GetAnnouncement(BaseAPI):
    """Get creator announcements"""
    path = "/{service}/user/{creator_id}/announcements"
    method = "get"

    class Response(RootModel[List[Announcement]]):
        root: List[Announcement]

    @classmethod
    async def __call__(cls, service: str, creator_id: str) -> APIRet[List[Announcement]]:
        return await cls.request(path=cls.path.format(service=service, creator_id=creator_id))


get_announcement = GetAnnouncement.__call__
"""Get creator announcements"""
