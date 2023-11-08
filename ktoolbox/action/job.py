from pathlib import Path
from typing import List, Union

import aiofiles

from ktoolbox.action import ActionRet
from ktoolbox.api.model import Post
from ktoolbox.api.posts import get_creator_post
from ktoolbox.api.utils import SEARCH_STEP
from ktoolbox.configuration import config, PostStructureConfiguration
from ktoolbox.enum import PostFileTypeEnum, DataStorageNameEnum
from ktoolbox.job import Job, CreatorIndices

__all__ = ["create_job_from_post"]


async def create_job_from_post(
        post: Post,
        post_path: Path,
        *,
        post_structure: Union[PostStructureConfiguration, bool] = None,
        dump_post_data: bool = True
) -> List[Job]:
    """
    Create a list of download job from a post data

    :param post: post data
    :param post_path: Path of the post directory
    :param post_structure: post path structure, `False` -> disable, `True` & `None` -> `config.job.post_structure`
    :param dump_post_data: Whether to dump post data (post.json) in post directory
    """
    jobs: List[Job] = []
    if post_structure in [True, None]:
        post_structure = config.job.post_structure
    if post_structure:
        attachments_path = post_path / post_structure.attachments
        content_path = post_path / post_structure.content_filepath
    else:
        attachments_path = post_path
        content_path = None
    for attachment in post.attachments:
        jobs.append(
            Job(
                path=attachments_path,
                alt_filename=attachment.name,
                server_path=attachment.path,
                type=PostFileTypeEnum.Attachment
            )
        )
    jobs.append(
        Job(
            path=post_path,
            alt_filename=post.file.name,
            server_path=post.file.path,
            type=PostFileTypeEnum.File
        )
    )
    if content_path:
        async with aiofiles.open(content_path, "w", encoding=config.downloader.encoding) as f:
            await f.write(post.content)
    if dump_post_data:
        async with aiofiles.open(str(post_path / DataStorageNameEnum.PostData.value), "w", encoding="utf-8") as f:
            await f.write(
                post.model_dump_json(indent=config.json_dump_indent)
            )
    return jobs


# TODO
async def create_job_from_creator(
        service: str,
        creator_id: str,
        path: Path,
        *,
        update_from: CreatorIndices = None,
        all_pages: bool = False,
        o: int = None,
        save_creator_indices: bool = False,
        mix_posts: bool = None
) -> ActionRet[List[Job]]:
    """
    Create a list of download job from a creator

    :param service: The service where the post is located
    :param creator_id: The ID of the creator
    :param path: The path for posts to download
    :param update_from: `CreatorIndices` data for update posts from current creator directory
    :param all_pages: Fetch all pages of posts, `o` will be ignored if enabled
    :param o: Result offset, stepping of 50 is enforced
    :param save_creator_indices: Record `CreatorIndices` data for update posts from current creator directory
    :param mix_posts: Save all files from different posts at same path, \
     `update_from`, `save_creator_indices` will be ignored if enabled
    """
    mix_posts = config.job.mix_posts if mix_posts is None else mix_posts
    if all_pages:
        post_list: List[Post] = []
        o = 0
        while True:
            ret = await get_creator_post(service=service, creator_id=creator_id, o=o)
            if ret:
                post_list += ret.data
                if len(ret.data) < SEARCH_STEP:
                    break
                else:
                    o += SEARCH_STEP
            else:
                return ActionRet(**ret.model_dump(mode="python"))
    else:
        ret = await get_creator_post(service=service, creator_id=creator_id, o=o)
        if ret:
            post_list = ret.data
        else:
            return ActionRet(**ret.model_dump(mode="python"))

    job_list: List[Job] = []
    for post in post_list:
        job_list += await create_job_from_post(
            post=post,
            post_path=path if mix_posts else path / post.title,
            post_structure=False if mix_posts else None,
            dump_post_data=not mix_posts
        )
    return ActionRet(data=job_list)
