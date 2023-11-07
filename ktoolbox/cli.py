from pathlib import Path
from typing import List

import aiofiles
from pydantic import BaseModel

from ktoolbox import __version__
from ktoolbox.action import search_creator as search_creator_action, search_creator_post as search_creator_post_action
from ktoolbox.api.misc import get_app_version
from ktoolbox.api.posts import get_post as get_post_api
from ktoolbox.downloader import Downloader
from ktoolbox.enum import TextEnum

from ktoolbox.model import SearchResult

__all__ = ["KToolBoxCli"]


class KToolBoxCli:
    @staticmethod
    async def _dump_search(result: List[BaseModel], path: Path):
        async with aiofiles.open(str(path), "w", encoding="utf-8") as f:
            await f.write(
                SearchResult(result=result)
                .model_dump_json(indent=4)
            )

    @staticmethod
    async def version():
        """Show KToolBox version"""
        return __version__

    @staticmethod
    async def site_version():
        # noinspection SpellCheckingInspection
        """Show current Kemono site app commit hash"""
        ret = await get_app_version()
        return ret.data if ret else ret.message

    # noinspection PyShadowingBuiltins
    @classmethod
    async def search_creator(
            cls,
            id: str = None,
            name: str = None,
            service: str = None,
            *,
            dump: Path = None
    ):
        """
        Search creator, you can use multiple parameters as keywords.

        :param id: The ID of the creator
        :param name: The name of the creator
        :param service: The service for the creator
        :param dump: Dump the result to a JSON file
        """
        ret = await search_creator_action(id=id, name=name, service=service)
        if ret:
            result_list = list(ret.data)
            if dump:
                await cls._dump_search(result_list, dump)
            return result_list or TextEnum.SearchResultEmpty
        else:
            return ret.message

    # noinspection PyShadowingBuiltins
    @classmethod
    async def search_creator_post(
            cls,
            id: str = None,
            name: str = None,
            service: str = None,
            q: str = None,
            o: int = None,
            *,
            dump: Path = None
    ):
        """
        Search posts from creator, you can use multiple parameters as keywords.

        :param id: The ID of the creator
        :param name: The name of the creator
        :param service: The service for the creator
        :param q: Search query
        :param o: Result offset, stepping of 50 is enforced
        :param dump: Dump the result to a JSON file
        """
        ret = await search_creator_post_action(id=id, name=name, service=service, q=q, o=o)
        if ret:
            if dump:
                await cls._dump_search(ret.data, dump)
            return ret.data or TextEnum.SearchResultEmpty
        else:
            return ret.message

    @staticmethod
    async def get_post(service: str, creator_id: str, post_id: str):
        """
        Get a specific post

        :param service: The service name
        :param creator_id: The creator's ID
        :param post_id: The post ID
        """
        ret = await get_post_api(
            service=service,
            creator_id=creator_id,
            post_id=post_id
        )
        return ret.data if ret else ret.message

    @staticmethod
    async def dev_test():
        """Dev test"""
        downloader = Downloader(
            "https://github.com/Ljzd-PRO/Mys_Goods_Tool/releases/download/v2.1.0/v2.1.0-Linux-x86_64.zip",
            Path("./")
        )
        ret = await downloader.run(progress=True)
        return ret.data if ret else ret.message
