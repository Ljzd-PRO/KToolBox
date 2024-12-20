from typing import Iterator, List

from ktoolbox._enum import RetCodeEnum
from ktoolbox.action import ActionRet
from ktoolbox.api.model import Creator, Post
from ktoolbox.api.posts import get_creators, get_creator_post
from ktoolbox.utils import BaseRet, generate_msg

__all__ = ["search_creator", "search_creator_post"]


# noinspection PyShadowingBuiltins
async def search_creator(id: str = None, name: str = None, service: str = None) -> BaseRet[Iterator[Creator]]:
    """
    Search creator with multiple keywords support.

    :param id: The ID of the creator
    :param name: The name of the creator
    :param service: The service for the creator
    """

    def filter_func(creator: Creator):
        """Filter creators with attributes"""
        if id is not None and creator.id != id:
            return False
        if name is not None and name not in creator.name:
            return False
        if service is not None and creator.service != service:
            return False
        return True

    ret = await get_creators()
    if not ret:
        base_ret = BaseRet.model_validate(ret.model_dump())
        base_ret.data = iter([])
        return base_ret
    creators = ret.data
    return ActionRet(data=iter(filter(filter_func, creators)))


# noinspection PyShadowingBuiltins
async def search_creator_post(
        id: str = None,
        name: str = None,
        service: str = None,
        q: str = None,
        o: str = None
) -> BaseRet[List[Post]]:
    """
    Search posts from creator with multiple keywords support.

    :param id: The ID of the creator
    :param name: The name of the creator
    :param service: The service for the creator
    :param q: Search query
    :param o: Result offset, stepping of 50 is enforced
    """

    async def inner(**kwargs):
        posts: List[Post] = []
        if any([id, name, service]):
            if id is not None and service:  # ``get_creator_post`` required
                ret = await get_creator_post(
                    service=service,
                    creator_id=id,
                    q=q,
                    o=o
                )
                return ActionRet(data=ret.data) if ret else ret
            else:  # else need to get ``id`` and ``service``
                creators_ret = await search_creator(id=id, name=name, service=service)
                if not creators_ret:
                    return ActionRet(**creators_ret.model_dump(mode="python"))
                else:
                    for creator in creators_ret.data:
                        ret = await get_creator_post(
                            service=creator.service,
                            creator_id=creator.id,
                            q=q,
                            o=o
                        )
                        if ret:
                            posts += ret.data
                    return ActionRet(data=posts)
        else:
            return ActionRet(
                code=RetCodeEnum.MissingParameter,
                message=generate_msg(
                    "Missing `id`, `name`, `service` parameter, at least given one of them.",
                    **kwargs
                )
            )

    return await inner(id=id, name=name, service=service, q=q, o=o)
