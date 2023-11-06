from k_tool_box.action import search_creator as search_creator_action
from k_tool_box.api.misc import get_app_version
from k_tool_box.api.posts import get_creator_post

__all__ = ["KToolBoxCli"]

from k_tool_box.enum import TextEnum


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
        Search creator, you can use multiple parameters as keywords.

        :param id: The ID of the creator
        :param name: The name of the creator
        :param service: The service for the creator
        """
        ret = await search_creator_action(id=id, name=name, service=service)
        if ret:
            result_list = list(ret.data)
            return result_list or TextEnum.SearchResultEmpty
        else:
            return ret.message

    @staticmethod
    async def test():
        """run test"""
        ret = await get_creator_post(service="fanbox", creator_id="3316400", q="1月")
        return ret.data if ret else ret.message
