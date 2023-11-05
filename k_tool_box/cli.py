from k_tool_box.api.misc import get_app_version
from k_tool_box.api.posts import get_creators

__all__ = ["KToolBoxCli"]


class KToolBoxCli:
    @staticmethod
    async def site_version():
        """Show current Kemono site app commit hash"""
        return await get_app_version()

    @staticmethod
    async def test():
        """run test"""
        ret = await get_creators()
        return ret.data if ret else ret.message
