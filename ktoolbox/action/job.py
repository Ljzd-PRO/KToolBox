from datetime import datetime
from fnmatch import fnmatch
from itertools import count
from pathlib import Path
from typing import List, Union, Optional, Set
from urllib.parse import urlparse

import aiofiles
from loguru import logger
from pathvalidate import sanitize_filename, is_valid_filename

from ktoolbox._enum import PostFileTypeEnum, DataStorageNameEnum
from ktoolbox.action import ActionRet, fetch_creator_posts, FetchInterruptError
from ktoolbox.action.utils import generate_post_path_name, filter_posts_by_date, generate_filename, \
    filter_posts_by_keywords, filter_posts_by_keywords_exclude, generate_grouped_post_path, extract_content_images
from ktoolbox.api.model import Post, Attachment, Revision
from ktoolbox.api.posts import get_post_revisions as get_post_revisions_api, get_post as get_post_api
from ktoolbox.configuration import config
from ktoolbox.job import Job, CreatorIndices
from ktoolbox.utils import extract_external_links, generate_msg

__all__ = ["create_job_from_post", "create_job_from_creator"]


async def create_job_from_post(
        post: Union[Post, Revision],
        post_path: Path,
        *,
        post_dir: bool = True,
        dump_post_data: bool = True
) -> List[Job]:
    """
    Create a list of download job from a post data

    :param post: post data
    :param post_path: Path of the post directory, which needs to be sanitized
    :param post_dir: Whether to create post directory
    :param dump_post_data: Whether to dump post data (post.json) in post directory
    :raise FetchInterruptError: If fetching post content fails
    """
    post_path.mkdir(parents=True, exist_ok=True)

    # Load ``PostStructureConfiguration``
    if post_dir:
        attachments_path = post_path / config.job.post_structure.attachments  # attachments
        attachments_path.mkdir(exist_ok=True)
        content_path = post_path / config.job.post_structure.content  # content
        content_path.parent.mkdir(exist_ok=True)
        external_links_path = post_path / config.job.post_structure.external_links  # external_links
        external_links_path.parent.mkdir(exist_ok=True)
    else:
        attachments_path = post_path
        content_path = None
        external_links_path = None

    if dump_post_data:
        async with aiofiles.open(str(post_path / DataStorageNameEnum.PostData.value), "w", encoding="utf-8") as f:
            await f.write(
                post.model_dump_json(indent=config.json_dump_indent)
            )

    # Filter and create jobs for ``Post.attachment``
    jobs: List[Job] = []
    sequential_counter = 1  # Counter for sequential filenames
    if config.job.download_attachments:
        for i, attachment in enumerate(post.attachments):  # type: int, Attachment
            if not attachment.path:
                continue
            file_path_obj = Path(attachment.name) if is_valid_filename(attachment.name) else Path(
                urlparse(attachment.path).path
            )
            if (not config.job.allow_list or any(
                    map(
                        lambda x: fnmatch(file_path_obj.name, x),
                        config.job.allow_list
                    )
            )) and not any(
                map(
                    lambda x: fnmatch(file_path_obj.name, x),
                    config.job.block_list
                )
            ):
                # Check if file extension should be excluded from sequential naming
                should_use_sequential = (config.job.sequential_filename and
                                         file_path_obj.suffix.lower() not in config.job.sequential_filename_excludes)
                if should_use_sequential:
                    basic_filename = f"{sequential_counter}{file_path_obj.suffix}"
                    sequential_counter += 1
                else:
                    basic_filename = file_path_obj.name
                alt_filename = generate_filename(post, basic_filename, config.job.filename_format)
                jobs.append(
                    Job(
                        path=attachments_path,
                        alt_filename=alt_filename,
                        server_path=attachment.path,
                        type=PostFileTypeEnum.Attachment,
                        post=post
                    )
                )

    # Filter and create jobs for ``Post.file``
    if config.job.download_file and post.file and post.file.path:
        post_file_name = Path(post.file.name) if is_valid_filename(post.file.name) else Path(
            urlparse(post.file.path).path
        )
        post_file_name = Path(generate_filename(post, post_file_name.name, config.job.post_structure.file))
        if (not config.job.allow_list or any(
                map(
                    lambda x: fnmatch(post_file_name.name, x),
                    config.job.allow_list
                )
        )) and not any(
            map(
                lambda x: fnmatch(post_file_name.name, x),
                config.job.block_list
            )
        ):
            jobs.append(
                Job(
                    path=post_path,
                    alt_filename=post_file_name.name,
                    server_path=post.file.path,
                    type=PostFileTypeEnum.File,
                    post=post
                )
            )
    # ``post.substring`` is used to determine if the post has content, but it's only partial
    if (post.content or post.substring) and post_dir and (
            config.job.extract_content or config.job.extract_external_links or config.job.extract_content_images
    ):
        # If post has no content, fetch it from get_post API
        if not post.content:
            get_post_ret = await get_post_api(
                service=post.service,
                creator_id=post.user,
                post_id=post.id,
                revision_id=post.revision_id if isinstance(post, Revision) else None
            )
            if get_post_ret:
                post = get_post_ret.data.post
            else:
                logger.error(
                    generate_msg(
                        "Failed to fetch post content",
                        post_name=post.title or "Unknown",
                        post_id=post.id,
                        creator_id=post.user,
                        service=post.service
                    )
                )
                raise FetchInterruptError(ret=get_post_ret)

        # If post content is still empty, skip content extraction
        if post.content:
            # Write content file
            if config.job.extract_content:
                async with aiofiles.open(content_path, "w", encoding=config.downloader.encoding) as f:
                    await f.write(post.content)

            # Extract and write external links file
            if config.job.extract_external_links:
                external_links = extract_external_links(post.content, config.job.external_link_patterns)
                if external_links:
                    async with aiofiles.open(external_links_path, "w", encoding=config.downloader.encoding) as f:
                        # Write each link on a separate line
                        for link in sorted(external_links):
                            await f.write(f"{link}\n")

            # Extract content images
            if config.job.extract_content_images:
                content_image_sources = extract_content_images(post.content)
                for image_src in content_image_sources:
                    if not image_src or not image_src.strip():
                        continue

                    # Handle relative paths by making them absolute
                    # noinspection HttpUrlsUsage
                    if image_src.startswith('/') and not image_src.startswith('//'):
                        # Relative path - construct full URL
                        image_path = image_src
                    elif image_src.startswith('http://') or image_src.startswith('https://'):
                        # Absolute URL - extract path
                        image_path = urlparse(image_src).path
                    else:
                        # Skip data URLs, protocol-relative URLs, or other non-path sources
                        continue

                    if not image_path or not image_path.strip():
                        continue

                    # Generate filename from the image path
                    image_file_path = Path(image_path)

                    # Apply "allow/block list" filtering first (before incrementing counter)
                    if config.job.sequential_filename:
                        basic_filename = f"{sequential_counter + 1}{image_file_path.suffix}"
                    else:
                        basic_filename = image_file_path.name

                    alt_filename = generate_filename(post, basic_filename, config.job.filename_format)

                    if (not config.job.allow_list or any(
                            map(
                                lambda x: fnmatch(alt_filename, x),
                                config.job.allow_list
                            )
                    )) and not any(
                        map(
                            lambda x: fnmatch(alt_filename, x),
                            config.job.block_list
                        )
                    ):
                        # Regenerate filename with correct counter
                        should_use_sequential = (config.job.sequential_filename and
                                                 image_file_path.suffix.lower() not in config.job.sequential_filename_excludes)
                        if should_use_sequential:
                            basic_filename = f"{sequential_counter}{image_file_path.suffix}"
                            alt_filename = generate_filename(post, basic_filename, config.job.filename_format)
                            sequential_counter += 1

                        jobs.append(
                            Job(
                                path=attachments_path,
                                alt_filename=alt_filename,
                                server_path=image_path,
                                type=PostFileTypeEnum.Attachment
                            )
                        )

    return jobs


async def create_job_from_creator(
        service: str,
        creator_id: str,
        path: Path,
        *,
        all_pages: bool = False,
        offset: int = 0,
        length: Optional[int] = 50,
        save_creator_indices: bool = False,
        mix_posts: bool = None,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        keywords: Optional[Set[str]] = None,
        keywords_exclude: Optional[Set[str]] = None
) -> ActionRet[List[Job]]:
    """
    Create a list of download job from a creator

    :param service: The service where the post is located
    :param creator_id: The ID of the creator
    :param path: The path for downloading posts, which needs to be sanitized
    :param all_pages: Fetch all posts, ``offset`` and ``length`` will be ignored if enabled
    :param offset: Result offset (or start offset)
    :param length: The number of posts to fetch
    :param save_creator_indices: Record ``CreatorIndices`` data.
    :param mix_posts: Save all files from different posts at same path, \
     ``save_creator_indices`` will be ignored if enabled
    :param start_time: Start time of the time range
    :param end_time: End time of the time range
    :param keywords: Set of keywords to filter posts by title (case-insensitive)
    :param keywords_exclude: Set of keywords to exclude posts by title (case-insensitive)
    """
    mix_posts = config.job.mix_posts if mix_posts is None else mix_posts

    # Get posts
    logger.info(f"Start fetching posts from creator {creator_id}")
    post_list: List[Post] = []
    start_offset = offset - offset % 50
    if all_pages:
        page_counter = count()
    else:
        page_num = length // 50 + 1
        page_counter = iter(range(page_num))

    try:
        async for part in fetch_creator_posts(service=service, creator_id=creator_id, o=start_offset):
            if next(page_counter, None) is not None:
                post_list += part
            else:
                break
    except FetchInterruptError as e:
        return ActionRet(**e.ret.model_dump(mode="python"))

    if not all_pages:
        post_list = post_list[offset % 50:][:length]
    else:
        post_list = post_list[offset % 50:]

    # Filter posts by publish time
    if start_time or end_time:
        post_list = list(filter_posts_by_date(post_list, start_time, end_time))

    # Filter posts by keywords
    if keywords:
        post_list = list(filter_posts_by_keywords(post_list, keywords))

    # Filter out posts by exclude keywords
    if keywords_exclude:
        post_list = list(filter_posts_by_keywords_exclude(post_list, keywords_exclude))

    logger.info(f"Get {len(post_list)} posts after filtering, start creating jobs")

    # Filter posts and generate ``CreatorIndices``
    if not mix_posts:
        if save_creator_indices:
            # Generate posts_path with year/month grouping if enabled
            posts_path = {}
            for post in post_list:
                grouped_base_path = generate_grouped_post_path(post, path)
                posts_path[post.id] = grouped_base_path / sanitize_filename(post.title)

            indices = CreatorIndices(
                creator_id=creator_id,
                service=service,
                posts={post.id: post for post in post_list},
                posts_path=posts_path
            )
            async with aiofiles.open(
                    path / DataStorageNameEnum.CreatorIndicesData.value,
                    "w",
                    encoding="utf-8"
            ) as f:
                await f.write(indices.model_dump_json(indent=config.json_dump_indent))

    if config.job.include_revisions:
        logger.warning("`job.include_revisions` is enabled and will fetch post revisions, "
                       "which may take time. Disable if not needed.")
    if config.job.extract_content or config.job.extract_external_links or config.job.extract_content_images:
        logger.warning(
            "`job.extract_content` or `job.extract_external_links` or `job.extract_content_images` is enabled "
            "and will fetch post content one by one, which may take time. Disable if not needed.")

    job_list: List[Job] = []
    for post in post_list:
        # Get post path
        if mix_posts:
            post_path = path
        else:
            # Apply year/month grouping if enabled
            grouped_base_path = generate_grouped_post_path(post, path)
            post_path = grouped_base_path / generate_post_path_name(post)

        # Generate jobs for the main post
        try:
            job_list += await create_job_from_post(
                post=post,
                post_path=post_path,
                post_dir=not mix_posts,
                dump_post_data=not mix_posts
            )
        except FetchInterruptError as e:
            return ActionRet(**e.ret.model_dump(mode="python"))

        # If include_revisions is enabled, fetch and download revisions for this post
        if config.job.include_revisions and not mix_posts:
            try:
                revisions_ret = await get_post_revisions_api(
                    service=service,
                    creator_id=creator_id,
                    post_id=post.id
                )
                if revisions_ret and revisions_ret.data:
                    for revision in revisions_ret.data:
                        if revision.revision_id:  # Only process actual revisions
                            revision_path = post_path / config.job.post_structure.revisions / generate_post_path_name(
                                revision)
                            try:
                                revision_jobs = await create_job_from_post(
                                    post=revision,
                                    post_path=revision_path,
                                    dump_post_data=True
                                )
                            except FetchInterruptError as e:
                                return ActionRet(**e.ret.model_dump(mode="python"))
                            job_list += revision_jobs
            except Exception as e:
                logger.warning(f"Failed to fetch revisions for post {post.id}: {e}")

    return ActionRet(data=job_list)
