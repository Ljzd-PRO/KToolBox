from pathlib import Path
from typing import List, Union, Tuple

import aiofiles
from loguru import logger
from pathvalidate import sanitize_filename

from ktoolbox.action import ActionRet, fetch_all_creator_posts, FetchInterruptError
from ktoolbox.api.model import Post
from ktoolbox.api.posts import get_creator_post
from ktoolbox.configuration import config, PostStructureConfiguration
from ktoolbox.enum import PostFileTypeEnum, DataStorageNameEnum
from ktoolbox.job import Job, CreatorIndices

__all__ = ["create_job_from_post", "filter_posts_with_indices", "create_job_from_creator"]


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
    :param post_structure: post path structure, ``False`` -> disable, \
     ``True`` & ``None`` -> ``config.job.post_structure``
    :param dump_post_data: Whether to dump post data (post.json) in post directory
    """
    post_path.mkdir(exist_ok=True)

    # Load ``PostStructureConfiguration``
    if post_structure in [True, None]:
        post_structure = config.job.post_structure
    if post_structure:
        attachments_path = post_path / post_structure.attachments  # attachments
        attachments_path.mkdir(exist_ok=True)
        content_path = post_path / post_structure.content_filepath  # content
        content_path.parent.mkdir(exist_ok=True)
    else:
        attachments_path = post_path
        content_path = None

    # Create jobs
    jobs: List[Job] = []
    for attachment in post.attachments:  # attachments
        if not attachment.path:
            continue
        jobs.append(
            Job(
                path=attachments_path,
                alt_filename=attachment.name,
                server_path=attachment.path,
                type=PostFileTypeEnum.Attachment
            )
        )
    if post.file.path:  # file
        jobs.append(
            Job(
                path=post_path,
                alt_filename=f"{post.id}_{post.file.name}",
                server_path=post.file.path,
                type=PostFileTypeEnum.File
            )
        )

    # Write content file
    if content_path and post.content:
        async with aiofiles.open(content_path, "w", encoding=config.downloader.encoding) as f:
            await f.write(post.content)
    if dump_post_data:
        async with aiofiles.open(str(post_path / DataStorageNameEnum.PostData.value), "w", encoding="utf-8") as f:
            await f.write(
                post.json(indent=config.json_dump_indent)
            )

    return jobs


def filter_posts_with_indices(posts: List[Post], indices: CreatorIndices) -> Tuple[List[Post], CreatorIndices]:
    """
    Compare and filter posts by ``CreatorIndices`` data

    Only keep posts that was edited after last download.

    :param posts: Posts to filter
    :param indices: ``CreatorIndices`` data to use
    :return: A updated ``List[Post]`` and updated **new** ``CreatorIndices`` instance
    """
    new_list = list(
        filter(
            lambda x: x.id not in indices.posts or x.edited > indices.posts[x.id].edited, posts
        )
    )
    new_indices = indices.copy(deep=True)
    for post in new_list:
        new_indices.posts[post.id] = post
    return new_list, new_indices


async def create_job_from_creator(
        service: str,
        creator_id: str,
        path: Path,
        *,
        update_from: CreatorIndices = None,
        all_pages: bool = False,
        o: int = None,
        save_creator_indices: bool = True,
        mix_posts: bool = None
) -> ActionRet[List[Job]]:
    """
    Create a list of download job from a creator

    :param service: The service where the post is located
    :param creator_id: The ID of the creator
    :param path: The path for posts to download
    :param update_from: ``CreatorIndices`` data for update posts from current creator directory, \
     ``save_creator_indices`` will be enabled if this provided
    :param all_pages: Fetch all pages of posts, ``o`` will be ignored if enabled
    :param o: Result offset, stepping of 50 is enforced
    :param save_creator_indices: Record ``CreatorIndices`` data for update posts from current creator directory
    :param mix_posts: Save all files from different posts at same path, \
     ``update_from``, ``save_creator_indices`` will be ignored if enabled
    """
    mix_posts = config.job.mix_posts if mix_posts is None else mix_posts

    # Get posts
    logger.info(f"Start fetching posts from creator {creator_id}")
    if all_pages:
        post_list: List[Post] = []
        try:
            async for part in fetch_all_creator_posts(service=service, creator_id=creator_id):
                post_list += part
        except FetchInterruptError as e:
            return ActionRet(**e.ret.dict())
    else:
        ret = await get_creator_post(service=service, creator_id=creator_id, o=o)
        if ret:
            post_list = ret.data
        else:
            return ActionRet(**ret.dict())
    logger.info(f"Get {len(post_list)} posts, start creating jobs")

    # Filter posts and generate ``CreatorIndices``
    if not mix_posts:
        indices = None
        if update_from:
            post_list, indices = filter_posts_with_indices(post_list, update_from)
            logger.info(f"{len(post_list)} posts will be downloaded")
        elif save_creator_indices:  # It's unnecessary to create indices again when ``update_from`` was provided
            indices = CreatorIndices(
                creator_id=creator_id,
                service=service,
                posts={post.id: post for post in post_list},
                posts_path={post.id: path / sanitize_filename(post.title) for post in post_list}
            )
        if indices:
            async with aiofiles.open(
                    path / DataStorageNameEnum.CreatorIndicesData.value,
                    "w",
                    encoding="utf-8"
            ) as f:
                await f.write(indices.json(indent=config.json_dump_indent))

    job_list: List[Job] = []
    for post in post_list:
        # Get post path
        if mix_posts:
            default_post_path = path
        elif config.job.post_id_as_path:
            default_post_path = path / post.id
        else:
            default_post_path = path / sanitize_filename(post.title)
        if update_from:
            if not (post_path := update_from.posts_path.get(post.id)):
                post_path = default_post_path
        else:
            post_path = default_post_path

        # Generate jobs
        job_list += await create_job_from_post(
            post=post,
            post_path=post_path,
            post_structure=False if mix_posts else None,
            dump_post_data=not mix_posts
        )
    return ActionRet(data=job_list)
