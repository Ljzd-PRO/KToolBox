from datetime import datetime
from pathlib import Path
from typing import Union, overload, Tuple

import aiofiles
from loguru import logger
from pathvalidate import sanitize_filename

from ktoolbox import __version__
from ktoolbox.action import create_job_from_post, create_job_from_creator, generate_post_path_name
from ktoolbox.action import search_creator as search_creator_action, search_creator_post as search_creator_post_action
from ktoolbox.api.misc import get_app_version
from ktoolbox.api.posts import get_post as get_post_api
from ktoolbox.configuration import config
from ktoolbox.enum import TextEnum
from ktoolbox.job import JobRunner, CreatorIndices
from ktoolbox.utils import dump_search, parse_webpage_url, generate_msg

__all__ = ["KToolBoxCli"]


class KToolBoxCli:
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
    @staticmethod
    async def search_creator(
            name: str = None,
            id: str = None,
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
                await dump_search(result_list, dump)
            return result_list or TextEnum.SearchResultEmpty.value
        else:
            return ret.message

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
                await dump_search(ret.data, dump)
            return ret.data or TextEnum.SearchResultEmpty.value
        else:
            return ret.message

    @staticmethod
    async def get_post(service: str, creator_id: str, post_id: str, *, dump: Path = None):
        """
        Get a specific post

        :param service: The service name
        :param creator_id: The creator's ID
        :param post_id: The post ID
        :param dump: Dump the result to a JSON file
        """
        ret = await get_post_api(
            service=service,
            creator_id=creator_id,
            post_id=post_id
        )
        if ret:
            if dump:
                async with aiofiles.open(str(dump), "w", encoding="utf-8") as f:
                    await f.write(
                        ret.data.model_dump_json(indent=config.json_dump_indent)
                    )
            return ret.data
        else:
            return ret.message

    @staticmethod
    @overload
    async def download_post(
            url: str,
            path: Union[Path, str] = Path("."),
            *,
            dump_post_data=True
    ):
        ...

    @staticmethod
    @overload
    async def download_post(
            service: str,
            creator_id: str,
            post_id: str,
            path: Union[Path, str] = Path("."),
            *,
            dump_post_data=True
    ):
        ...

    @staticmethod
    async def download_post(
            url: str = None,
            service: str = None,
            creator_id: str = None,
            post_id: str = None,
            path: Union[Path, str] = Path("."),
            *,
            dump_post_data=True
    ):
        """
        Download a specific post

        :param url: The post URL
        :param service: The service name
        :param creator_id: The creator's ID
        :param post_id: The post ID
        :param path: Download path, default is current directory
        :param dump_post_data: Whether to dump post data (post.json) in post directory
        """
        # Get service, creator_id, post_id
        if url:
            service, creator_id, post_id = parse_webpage_url(url)
        if not all([service, creator_id, post_id]):
            return generate_msg(
                TextEnum.MissingParams.value,
                use_at_lease_one=[
                    ["url"],
                    ["service", "creator_id", "post_id"]
                ])

        path = path if isinstance(path, Path) else Path(path)
        ret = await get_post_api(
            service=service,
            creator_id=creator_id,
            post_id=post_id
        )
        if ret:
            post_path = path / generate_post_path_name(ret.data)
            job_list = await create_job_from_post(
                post=ret.data,
                post_path=post_path,
                dump_post_data=dump_post_data
            )
            job_runner = JobRunner(job_list=job_list)
            await job_runner.start()
        else:
            return ret.message

    @staticmethod
    @overload
    async def sync_creator(
            url: str,
            path: Union[Path, str] = Path("."),
            *,
            update_from: Path = None,
            save_creator_indices: bool = True,
            mix_posts: bool = None,
            time_range: Tuple[str, str] = None,
            start_time: str = None,
            end_time: str = None
    ):
        ...

    @staticmethod
    @overload
    async def sync_creator(
            service: str,
            creator_id: str,
            path: Union[Path, str] = Path("."),
            *,
            update_from: Path = None,
            save_creator_indices: bool = True,
            mix_posts: bool = None,
            time_range: Tuple[str, str] = None,
            start_time: str = None,
            end_time: str = None
    ):
        ...

    @staticmethod
    async def sync_creator(
            url: str = None,
            service: str = None,
            creator_id: str = None,
            path: Union[Path, str] = Path("."),
            *,
            update_from: Union[Path, str] = None,
            save_creator_indices: bool = True,
            mix_posts: bool = None,
            start_time: str = None,
            end_time: str = None
    ):
        """
        Sync all posts from a creator

        You can update the directory anytime after download finished, \
        such as to update after creator published new posts.

        * If ``update_from`` was provided, the file should be located **inside the creator directory**.
        * ``start_time`` & ``end_time`` example: ``2023-12-7``, ``2023-12-07``

        :param url: The post URL
        :param service: The service where the post is located
        :param creator_id: The ID of the creator
        :param path: Download path, default is current directory
        :param update_from: ``CreatorIndices`` data path for update posts from current creator directory, \
            ``save_creator_indices`` will be enabled if this provided
        :param save_creator_indices: Record ``CreatorIndices`` data for update posts from current creator directory
        :param mix_posts: Save all files from different posts at same path, \
            ``update_from``, ``save_creator_indices`` will be ignored if enabled
        :param start_time: Start time of the published time range for posts downloading. \
            Set to ``0`` if ``None`` was given. \
            Time format: ``%Y-%m-%d``
        :param end_time: End time of the published time range for posts downloading. \
            Set to latest time (infinity) if ``None`` was given. \
            Time format: ``%Y-%m-%d``
        """
        # Get service, creator_id
        if url:
            service, creator_id, _ = parse_webpage_url(url)
        if not all([service, creator_id]):
            return generate_msg(
                TextEnum.MissingParams.value,
                use_at_lease_one=[
                    ["url"],
                    ["service", "creator_id"]
                ])

        path = path if isinstance(path, Path) else Path(path)
        if update_from:
            update_from = update_from if isinstance(update_from, Path) else Path(update_from)

        # Get ``CreatorIndices`` data
        if update_from:
            async with aiofiles.open(update_from, encoding="utf-8") as f:
                indices_text = await f.read()
            indices = CreatorIndices.model_validate_json(indices_text)
            creator_path = update_from.parent
        else:
            indices = None

            # Get creator name
            creator_name = creator_id
            creator_ret = await search_creator_action(id=creator_id, service=service)
            if creator_ret:
                creator = next(creator_ret.data, None)
                if creator:
                    creator_name = creator.name
                    logger.info(
                        generate_msg(
                            "Got creator information",
                            name=creator.name,
                            id=creator.id
                        )
                    )
            else:
                logger.warning(
                    generate_msg(
                        f"Failed to fetch the name of creator <{creator_id}>, use creator ID as directory name",
                        detail=creator_ret.message
                    )
                )
            creator_path = path / sanitize_filename(creator_name)

        creator_path.mkdir(exist_ok=True)
        ret = await create_job_from_creator(
            service=service,
            creator_id=creator_id,
            path=creator_path,
            update_from=indices,
            all_pages=True,
            save_creator_indices=save_creator_indices,
            mix_posts=mix_posts,
            start_time=datetime.strptime(start_time, "%Y-%m-%d") if start_time else None,
            end_time=datetime.strptime(end_time, "%Y-%m-%d") if end_time else None
        )
        if ret:
            job_runner = JobRunner(job_list=ret.data)
            await job_runner.start()
        else:
            return ret.message
