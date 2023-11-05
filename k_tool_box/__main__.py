import asyncio

from k_tool_box.api.posts import get_creators

if __name__ == "__main__":
    async def main():
        ret = await get_creators()
        print(ret)

    asyncio.run(main())
