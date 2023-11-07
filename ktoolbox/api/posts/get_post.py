from ktoolbox.api import BaseAPI, APIRet
from ktoolbox.api.model import Post

__all__ = ["GetPost", "get_post"]


class GetPost(BaseAPI):
    path = "/{service}/user/{creator_id}/post/{post_id}"
    method = "get"

    class Response(Post):
        ...

    @classmethod
    async def __call__(cls, service: str, creator_id: str, post_id: str) -> APIRet[Post]:
        """
        Get a specific post

        :param service: The service name
        :param creator_id: The creator's ID
        :param post_id: The post ID
        """
        return await cls.request(
            path=cls.path.format(
                service=service,
                creator_id=creator_id,
                post_id=post_id
            )
        )


get_post = GetPost.__call__
