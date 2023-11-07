from pathlib import Path
from typing import List, Union

import aiofiles

from ktoolbox.api.model import Post
from ktoolbox.configuration import config, PostStructureConfiguration
from ktoolbox.enum import PostFileTypeEnum, DataStorageNameEnum
from ktoolbox.job import Job

__all__ = ["create_job_from_post"]


async def create_job_from_post(
        post: Post,
        post_path: Path,
        *,
        post_structure: Union[PostStructureConfiguration, bool] = None,
        dump_post_data: bool = False
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
        async with aiofiles.open(str(post_path / DataStorageNameEnum.PostData), "w", encoding="utf-8") as f:
            await f.write(
                post.model_dump_json(indent=config.json_dump_indent)
            )
    return jobs
