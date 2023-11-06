from typing import List

from pydantic import RootModel

from ktoolbox.api import BaseAPI, APIRet
from ktoolbox.api.model import Announcement

__all__ = ["GetAnnouncement", "get_announcement"]


class GetAnnouncement(BaseAPI):
    path = "/{service}/user/{creator_id}/announcements"
    method = "get"

    class Response(RootModel[List[Announcement]]):
        root: List[Announcement]

    @classmethod
    async def __call__(cls, service: str, creator_id: str) -> APIRet[List[Announcement]]:
        """
        Get creator announcements

        :param service: The service name
        :param creator_id: The creator's ID
        """
        return await cls.request(path=cls.path.format(service=service, creator_id=creator_id))


get_announcement = GetAnnouncement.__call__
