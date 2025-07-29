from datetime import datetime
from pathlib import Path
from typing import Union, overload

import aiofiles
from loguru import logger
from pathvalidate import sanitize_filename
from settings_doc import render, OutputFormat

from ktoolbox import __version__
from ktoolbox._enum import TextEnum
from ktoolbox.action import create_job_from_post, create_job_from_creator, generate_post_path_name
from ktoolbox.action import search_creator as search_creator_action, search_creator_post as search_creator_post_action
from ktoolbox.api.misc import get_app_version
from ktoolbox.api.posts import get_post as get_post_api
from ktoolbox.configuration import config
from ktoolbox.job import JobRunner
from ktoolbox.queue import QueueItem, load_queue, save_queue
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
        logger.info(repr(config))
        ret = await get_app_version()
        return ret.data if ret else ret.message

    @staticmethod
    async def config_editor():
        """Launch graphical KToolBox configuration editor"""
        try:
            from ktoolbox.editor import run_config_editor
            run_config_editor()
        except ModuleNotFoundError:
            logger.error(
                "You need to install extra dependencies to use the editor, "
                "run `pip install ktoolbox[urwid]` "
                "or `pipx install ktoolbox[urwid] --force` if you are using pipx"
            )

    @staticmethod
    async def example_env():
        """Generate an example configuration ``.env`` file."""
        print(
            render(
                OutputFormat.DOTENV,
                class_path=("ktoolbox.configuration.Configuration",)
            )
        )

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
        logger.info(repr(config))
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
        logger.info(repr(config))
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
        logger.info(repr(config))
        ret = await get_post_api(
            service=service,
            creator_id=creator_id,
            post_id=post_id
        )
        if ret:
            if dump:
                async with aiofiles.open(str(dump), "w", encoding="utf-8") as f:
                    await f.write(
                        ret.data.post.model_dump_json(indent=config.json_dump_indent)
                    )
            return ret.data.post
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
        logger.info(repr(config))
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
            post_path = path / generate_post_path_name(ret.data.post)
            job_list = await create_job_from_post(
                post=ret.data.post,
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
            save_creator_indices: bool = True,
            mix_posts: bool = None,
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
            save_creator_indices: bool = True,
            mix_posts: bool = None,
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
            save_creator_indices: bool = False,
            mix_posts: bool = None,
            start_time: str = None,
            end_time: str = None,
            offset: int = 0,
            length: int = None
    ):
        """
        Sync posts from a creator

        You can update the directory anytime after download finished, \
        such as to update after creator published new posts.

        * ``start_time`` & ``end_time`` example: ``2023-12-7``, ``2023-12-07``

        :param url: The post URL
        :param service: The service where the post is located
        :param creator_id: The ID of the creator
        :param path: Download path, default is current directory
        :param save_creator_indices: Record ``CreatorIndices`` data
        :param mix_posts: Save all_pages files from different posts at same path, \
            ``save_creator_indices`` will be ignored if enabled
        :param start_time: Start time of the published time range for posts downloading. \
            Set to ``0`` if ``None`` was given. \
            Time format: ``%Y-%m-%d``
        :param end_time: End time of the published time range for posts downloading. \
            Set to latest time (infinity) if ``None`` was given. \
            Time format: ``%Y-%m-%d``
        :param offset: Result offset (or start offset)
        :param length: The number of posts to fetch, defaults to fetching all posts after ``offset``.
        """
        logger.info(repr(config))
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
            logger.error(
                generate_msg(
                    f"Failed to fetch the name of creator <{creator_id}>",
                    detail=creator_ret.message
                )
            )
            return creator_ret.message

        creator_path = path / sanitize_filename(creator_name)

        creator_path.mkdir(exist_ok=True)
        ret = await create_job_from_creator(
            service=service,
            creator_id=creator_id,
            path=creator_path,
            all_pages=not length,
            offset=offset,
            length=length,
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

    @staticmethod
    @overload
    async def queue_add(
            url: str,
            path: Union[Path, str] = Path("."),
            *,
            save_creator_indices: bool = False,
            mix_posts: bool = None,
            start_time: str = None,
            end_time: str = None,
            offset: int = 0,
            length: int = None
    ):
        ...

    @staticmethod
    @overload
    async def queue_add(
            service: str,
            creator_id: str,
            path: Union[Path, str] = Path("."),
            *,
            save_creator_indices: bool = False,
            mix_posts: bool = None,
            start_time: str = None,
            end_time: str = None,
            offset: int = 0,
            length: int = None
    ):
        ...

    @staticmethod
    async def queue_add(
            url: str = None,
            service: str = None,
            creator_id: Union[str, int] = None,
            path: Union[Path, str] = Path("."),
            *,
            save_creator_indices: bool = False,
            mix_posts: bool = None,
            start_time: str = None,
            end_time: str = None,
            offset: int = 0,
            length: int = None
    ):
        """
        Add a creator to the sync queue

        :param url: The creator URL
        :param service: The service where the creator is located
        :param creator_id: The ID of the creator
        :param path: Download path, default is current directory
        :param save_creator_indices: Record ``CreatorIndices`` data
        :param mix_posts: Save all files from different posts at same path
        :param start_time: Start time filter for posts (format: %Y-%m-%d)
        :param end_time: End time filter for posts (format: %Y-%m-%d)
        :param offset: Result offset (or start offset)
        :param length: The number of posts to fetch
        """
        logger.info(repr(config))
        
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

        # Convert creator_id to string if it's an integer
        creator_id = str(creator_id) if creator_id is not None else None
        path = path if isinstance(path, Path) else Path(path)

        # Create queue item
        if url:
            queue_item = QueueItem.from_url(
                url=url,
                path=path,
                save_creator_indices=save_creator_indices,
                mix_posts=mix_posts,
                start_time=start_time,
                end_time=end_time,
                offset=offset,
                length=length
            )
        else:
            queue_item = QueueItem.from_params(
                service=service,
                creator_id=creator_id,
                path=path,
                save_creator_indices=save_creator_indices,
                mix_posts=mix_posts,
                start_time=start_time,
                end_time=end_time,
                offset=offset,
                length=length
            )

        # Load queue, add item, save queue
        queue = load_queue()
        queue.add_item(queue_item)
        
        if save_queue(queue):
            logger.info(f"Added creator {service}/{creator_id} to sync queue")
            return f"Added creator {service}/{creator_id} to sync queue (position {queue.size()})"
        else:
            return "Failed to save queue"

    @staticmethod
    async def queue_remove(index: int):
        """
        Remove a creator from the sync queue by index

        :param index: Index of the item to remove (0-based)
        """
        logger.info(repr(config))
        
        queue = load_queue()
        
        if queue.is_empty():
            return "Queue is empty"
        
        if index < 0 or index >= queue.size():
            return f"Invalid index {index}. Queue has {queue.size()} items (indices 0-{queue.size()-1})"
        
        removed_item = queue.remove_item(index)
        
        if removed_item and save_queue(queue):
            logger.info(f"Removed creator {removed_item.service}/{removed_item.creator_id} from queue")
            return f"Removed creator {removed_item.service}/{removed_item.creator_id} from queue"
        else:
            return "Failed to remove item from queue"

    @staticmethod
    async def queue_list():
        """
        List all creators in the sync queue
        """
        logger.info(repr(config))
        
        queue = load_queue()
        
        if queue.is_empty():
            return "Queue is empty"
        
        result = []
        result.append(f"Sync Creator Queue ({queue.size()} items):")
        result.append("-" * 50)
        
        for i, item in enumerate(queue.items):
            url_part = f" ({item.url})" if item.url else ""
            path_part = f" -> {item.path}" if item.path else ""
            params = []
            if item.length:
                params.append(f"length={item.length}")
            if item.offset:
                params.append(f"offset={item.offset}")
            if item.start_time:
                params.append(f"start={item.start_time}")
            if item.end_time:
                params.append(f"end={item.end_time}")
            if item.mix_posts:
                params.append("mix_posts=True")
            if item.save_creator_indices:
                params.append("save_indices=True")
            
            params_part = f" [{', '.join(params)}]" if params else ""
            
            result.append(f"{i:2d}. {item.service}/{item.creator_id}{url_part}{path_part}{params_part}")
            result.append(f"    Added: {item.added_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(result)

    @staticmethod
    async def queue_clear():
        """
        Clear all creators from the sync queue
        """
        logger.info(repr(config))
        
        queue = load_queue()
        
        if queue.is_empty():
            return "Queue is already empty"
        
        item_count = queue.size()
        queue.clear()
        
        if save_queue(queue):
            logger.info(f"Cleared {item_count} items from sync queue")
            return f"Cleared {item_count} items from sync queue"
        else:
            return "Failed to clear queue"

    @staticmethod
    async def queue_run():
        """
        Process/execute all creators in the sync queue
        
        Downloads all creators in the queue sequentially and clears the queue upon completion.
        """
        logger.info(repr(config))
        
        queue = load_queue()
        
        if queue.is_empty():
            return "Queue is empty, nothing to process"
        
        logger.info(f"Starting to process {queue.size()} items in sync queue")
        
        successful = 0
        failed = 0
        
        for i, item in enumerate(queue.items):
            logger.info(f"Processing queue item {i+1}/{queue.size()}: {item.service}/{item.creator_id}")
            
            try:
                # Use the existing sync_creator logic
                result = await KToolBoxCli.sync_creator(
                    url=item.url,
                    service=item.service,
                    creator_id=item.creator_id,
                    path=item.path or Path("."),
                    save_creator_indices=item.save_creator_indices,
                    mix_posts=item.mix_posts,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    offset=item.offset,
                    length=item.length
                )
                
                if result is None:  # Success
                    successful += 1
                    logger.info(f"Successfully processed {item.service}/{item.creator_id}")
                else:
                    failed += 1
                    logger.error(f"Failed to process {item.service}/{item.creator_id}: {result}")
                    
            except Exception as e:
                failed += 1
                logger.error(f"Error processing {item.service}/{item.creator_id}: {e}")
        
        # Clear the queue after processing
        queue.clear()
        if save_queue(queue):
            logger.info("Queue cleared after processing")
        
        result_msg = f"Queue processing completed: {successful} successful, {failed} failed"
        logger.info(result_msg)
        return result_msg
