from k_tool_box.api.misc import get_app_version
from k_tool_box.api.model import Creator
from k_tool_box.api.posts import get_creators
from k_tool_box.enum import TextEnum

__all__ = ["KToolBoxCli"]


class KToolBoxCli:
    @staticmethod
    async def site_version():
        # noinspection SpellCheckingInspection
        """Show current Kemono site app commit hash"""
        ret = await get_app_version()
        return ret.data if ret else ret.message

    # noinspection PyShadowingBuiltins
    @staticmethod
    async def search_creator(id: str = None, name: str = None, service: str = None):
        """
        Search creator, you can use multiple parameters.

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
                return ret.message
            creators = ret.data
            return list(filter(filter_func, creators)) or TextEnum.SearchResultEmpty

        return await inner(id=id, name=name, service=service)

    @staticmethod
    async def test():
        """run test"""
        ret = await get_creators()
        return ret.data if ret else ret.message
