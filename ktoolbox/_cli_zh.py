from pathlib import Path
from typing import Union, overload

import ktoolbox.cli


# noinspection PyMethodOverriding,PyArgumentList
class KToolBoxCli(ktoolbox.cli.KToolBoxCli):
    @staticmethod
    async def version():
        """
        显示 KToolBox 版本号
        """
        return await super().version()

    @staticmethod
    async def site_version():
        # noinspection SpellCheckingInspection
        """
        显示当前 Kemono 站点应用提交哈希
        """
        return await super().site_version()

    @staticmethod
    async def config_editor():
        """
        启动图形化 KToolBox 配置编辑器
        """
        return await super().config_editor()

    @staticmethod
    async def example_env():
        """
        生成示例配置 ``.env`` 文件
        """
        return await super().example_env()

    # noinspection PyShadowingBuiltins
    @staticmethod
    async def search_creator(
            name: str = None,
            id: str = None,
            service: str = None,
            *,
            dump: Path = None
    ):
        """
        搜索创作者，可使用多个参数作为关键词。

        :param id: 创作者 ID
        :param name: 创作者名称
        :param service: 创作者所属平台
        :param dump: 将结果导出为 JSON 文件
        """
        return await super().search_creator(name=name, id=id, service=service, dump=dump)

    # noinspection PyShadowingBuiltins
    @staticmethod
    async def search_creator_post(
            id: str = None,
            name: str = None,
            service: str = None,
            q: str = None,
            o: int = None,
            *,
            dump: Path = None
    ):
        """
        搜索创作者的帖子，可使用多个参数作为关键词。

        :param id: 创作者 ID
        :param name: 创作者名称
        :param service: 创作者所属平台
        :param q: 搜索关键词
        :param o: 结果偏移量，步长为 50
        :param dump: 将结果导出为 JSON 文件
        """
        return await super().search_creator_post(id=id, name=name, service=service, q=q, o=o, dump=dump)

    @staticmethod
    async def get_post(service: str, creator_id: str, post_id: str, revision_id: str = None, *, dump: Path = None):
        """
        获取指定帖子或修订版本

        :param service: 平台名称
        :param creator_id: 创作者 ID
        :param post_id: 帖子 ID
        :param revision_id: 修订版本 ID（可选）
        :param dump: 将结果导出为 JSON 文件
        """
        return await super().get_post(service=service, creator_id=creator_id, post_id=post_id, revision_id=revision_id,
                                      dump=dump)

    @staticmethod
    @overload
    async def download_post(
            url: str,
            path: Union[Path, str] = Path("."),
            *,
            dump_post_data=True
    ):
        """
        下载指定帖子或修订版本（通过 URL）

        :param url: 帖子链接
        :param path: 下载路径，默认为当前目录
        :param dump_post_data: 是否在帖子目录中保存 post.json 数据
        """
        ...

    @staticmethod
    @overload
    async def download_post(
            service: str,
            creator_id: str,
            post_id: str,
            revision_id: str = None,
            path: Union[Path, str] = Path("."),
            *,
            dump_post_data=True
    ):
        """
        下载指定帖子或修订版本（通过参数）

        :param service: 平台名称
        :param creator_id: 创作者 ID
        :param post_id: 帖子 ID
        :param revision_id: 修订版本 ID（可选）
        :param path: 下载路径，默认为当前目录
        :param dump_post_data: 是否在帖子目录中保存 post.json 数据
        """
        ...

    @staticmethod
    async def download_post(
            url: str = None,
            service: str = None,
            creator_id: str = None,
            post_id: str = None,
            revision_id: str = None,
            path: Union[Path, str] = Path("."),
            *,
            dump_post_data=True
    ):
        """
        下载指定帖子或修订版本

        :param url: 帖子链接
        :param service: 平台名称
        :param creator_id: 创作者 ID
        :param post_id: 帖子 ID
        :param revision_id: 修订版本 ID（可选）
        :param path: 下载路径，默认为当前目录
        :param dump_post_data: 是否在帖子目录中保存 post.json 数据
        """
        return await super().download_post(
            url=url,
            service=service,
            creator_id=creator_id,
            post_id=post_id,
            revision_id=revision_id,
            path=path,
            dump_post_data=dump_post_data
        )

    @staticmethod
    @overload
    async def sync_creator(
            url: str,
            path: Union[Path, str] = Path("."),
            *,
            save_creator_indices: bool = True,
            mix_posts: bool = None,
            start_time: str = None,
            end_time: str = None,
            keywords: str = None,
            keywords_exclude: str = None
    ):
        """
        同步创作者所有帖子（通过 URL）

        :param url: 帖子链接
        :param path: 下载路径，默认为当前目录
        :param save_creator_indices: 是否记录 CreatorIndices 数据
        :param mix_posts: 是否将不同帖子的所有文件保存到同一路径
        :param start_time: 帖子发布时间范围起始
        :param end_time: 帖子发布时间范围结束
        :param keywords: 按标题过滤帖子，逗号分隔关键词
        :param keywords_exclude: 按标题排除帖子，逗号分隔关键词
        """
        ...

    @staticmethod
    @overload
    async def sync_creator(
            service: str,
            creator_id: str,
            path: Union[Path, str] = Path("."),
            *,
            save_creator_indices: bool = True,
            mix_posts: bool = None,
            start_time: str = None,
            end_time: str = None,
            keywords: str = None,
            keywords_exclude: str = None
    ):
        """
        同步创作者所有帖子（通过参数）

        :param service: 平台名称
        :param creator_id: 创作者 ID
        :param path: 下载路径，默认为当前目录
        :param save_creator_indices: 是否记录 CreatorIndices 数据
        :param mix_posts: 是否将不同帖子的所有文件保存到同一路径
        :param start_time: 帖子发布时间范围起始
        :param end_time: 帖子发布时间范围结束
        :param keywords: 按标题过滤帖子，逗号分隔关键词
        :param keywords_exclude: 按标题排除帖子，逗号分隔关键词
        """
        ...

    @staticmethod
    async def sync_creator(
            url: str = None,
            service: str = None,
            creator_id: str = None,
            path: Union[Path, str] = Path("."),
            *,
            save_creator_indices: bool = False,
            mix_posts: bool = None,
            start_time: str = None,
            end_time: str = None,
            offset: int = 0,
            length: int = None,
            keywords: str = None,
            keywords_exclude: str = None
    ):
        """
        同步创作者所有帖子

        可在下载完成后随时更新目录，例如创作者发布新帖子后进行更新。

        * ``start_time`` 和 ``end_time`` 示例：``2023-12-7``，``2023-12-07``

        :param url: 帖子链接
        :param service: 平台名称
        :param creator_id: 创作者 ID
        :param path: 下载路径，默认为当前目录
        :param save_creator_indices: 是否记录 CreatorIndices 数据
        :param mix_posts: 是否将不同帖子的所有文件保存到同一路径
        :param start_time: 帖子发布时间范围起始，格式 ``%Y-%m-%d``
        :param end_time: 帖子发布时间范围结束，格式 ``%Y-%m-%d``
        :param offset: 结果偏移量
        :param length: 获取帖子数量，默认为全部
        :param keywords: 按标题过滤帖子，逗号分隔关键词
        :param keywords_exclude: 按标题排除帖子，逗号分隔关键词
        """
        return await super().sync_creator(
            url=url,
            service=service,
            creator_id=creator_id,
            path=path,
            save_creator_indices=save_creator_indices,
            mix_posts=mix_posts,
            start_time=start_time,
            end_time=end_time,
            offset=offset,
            length=length,
            keywords=keywords,
            keywords_exclude=keywords_exclude
        )
