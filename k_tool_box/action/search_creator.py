from typing import Iterator

from k_tool_box.api.model import Creator
from k_tool_box.api.posts import get_creators
from .base import ActionRet

__all__ = ["search_creator"]

from k_tool_box.utils import BaseRet


# noinspection PyShadowingBuiltins
async def search_creator(id: str = None, name: str = None, service: str = None) -> BaseRet[Iterator[Creator]]:
    """
    Search creator with multiple keywords support.

    :param id: The ID of the creator
    :param name: The name of the creator
    :param service: The service for the creator
    """

    async def inner(**kwargs):
        def filter_func(creator: Creator):
            for key, value in kwargs.items():
                if value is None:
                    continue
                elif creator.__getattribute__(key) != value:
                    return False
            return True

        ret = await get_creators()
        if not ret:
            return ret
        creators = ret.data
        return ActionRet(data=iter(filter(filter_func, creators)))

    return await inner(id=id, name=name, service=service)
