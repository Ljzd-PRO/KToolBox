from k_tool_box.api.posts import get_creators

__all__ = ["KToolBoxCli"]


class KToolBoxCli:
    @staticmethod
    async def test():
        """run test"""
        return await get_creators()
