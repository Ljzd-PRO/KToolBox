from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from urllib.parse import urlparse

import aiofiles  # type: ignore[import-untyped]
from loguru import logger
from pathvalidate import is_valid_filename, sanitize_filename

from ktoolbox._enum import DataStorageNameEnum, PostFileTypeEnum
from ktoolbox.action.base import ActionRet, action_error
from ktoolbox.action.fetch import FetchInterruptError, fetch_creator_posts
from ktoolbox.action.utils import (
    extract_content_images,
    filter_posts_by_date,
    filter_posts_by_keywords,
    generate_filename,
    generate_grouped_post_path,
    generate_post_path_name,
)
from ktoolbox.api.client import PawchiveClient
from ktoolbox.api.errors import PawchiveError, PawchiveNotFoundError
from ktoolbox.api.generated import Post, Revision
from ktoolbox.api.utils import pawchive_client_scope
from ktoolbox.blocker import BlockerContext, BlockerEngine
from ktoolbox.blocker.engine import blocker_registry, legacy_keyword_blocker
from ktoolbox.configuration import config
from ktoolbox.failures import FailureStage, StagedFailure
from ktoolbox.job import CreatorIndices, Job
from ktoolbox.utils import extract_external_links, generate_msg

__all__ = ["CreatorJobGeneration", "create_job_from_post", "create_job_from_creator", "produce_jobs_from_creator"]


async def create_job_from_post(
    post: Post | Revision,
    post_path: Path,
    *,
    post_dir: bool = True,
    dump_post_data: bool = True,
    client: PawchiveClient | None = None,
) -> list[Job]:
    """
    Create a list of download job from a post data

    :param post: post data
    :param post_path: Path of the post directory, which needs to be sanitized
    :param post_dir: Whether to create post directory
    :param dump_post_data: Whether to dump post data (post.json) in post directory
    :raise FetchInterruptError: If fetching post content fails
    """
    await aiofiles.os.makedirs(post_path, exist_ok=True)
    job_post = Post.model_validate(post.model_dump(mode="python"))

    # Load ``PostStructureConfiguration``
    if post_dir:
        attachments_path = post_path / config.job.post_structure.attachments  # attachments
        await aiofiles.os.makedirs(attachments_path, exist_ok=True)
        content_path = post_path / config.job.post_structure.content  # content
        await aiofiles.os.makedirs(content_path.parent, exist_ok=True)
        external_links_path = post_path / config.job.post_structure.external_links  # external_links
        await aiofiles.os.makedirs(external_links_path.parent, exist_ok=True)
    else:
        attachments_path = post_path
        content_path = None
        external_links_path = None

    if dump_post_data:
        async with aiofiles.open(str(post_path / DataStorageNameEnum.PostData.value), "w", encoding="utf-8") as f:
            await f.write(post.model_dump_json(indent=config.json_dump_indent))

    # Filter and create jobs for ``Post.attachment``
    jobs: list[Job] = []
    sequential_counter = 1  # Counter for sequential filenames
    if config.job.download_attachments:
        for attachment in post.attachments or []:
            if not attachment.path:
                continue
            file_path_obj = (
                Path(attachment.name)
                if attachment.name and is_valid_filename(attachment.name)
                else Path(urlparse(attachment.path).path)
            )
            if (
                not config.job.allow_list or any(map(lambda x: fnmatch(file_path_obj.name, x), config.job.allow_list))
            ) and not any(map(lambda x: fnmatch(file_path_obj.name, x), config.job.block_list)):
                # Check if file extension should be excluded from sequential naming
                should_use_sequential = (
                    config.job.sequential_filename
                    and file_path_obj.suffix.lower() not in config.job.sequential_filename_excludes
                )
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
                        post=job_post,
                    )
                )

    # Filter and create jobs for ``Post.file``
    if config.job.download_file and post.file and post.file.path:
        post_file_name = (
            Path(post.file.name)
            if post.file.name and is_valid_filename(post.file.name)
            else Path(urlparse(post.file.path).path)
        )
        post_file_name = Path(generate_filename(post, post_file_name.name, config.job.post_structure.file))
        if (
            not config.job.allow_list or any(map(lambda x: fnmatch(post_file_name.name, x), config.job.allow_list))
        ) and not any(map(lambda x: fnmatch(post_file_name.name, x), config.job.block_list)):
            jobs.append(
                Job(
                    path=post_path,
                    alt_filename=post_file_name.name,
                    server_path=post.file.path,
                    type=PostFileTypeEnum.File,
                    post=job_post,
                )
            )
    # ``post.substring`` is used to determine if the post has content, but it's only partial
    if (
        (post.content or post.substring)
        and post_dir
        and (config.job.extract_content or config.job.extract_external_links or config.job.extract_content_images)
    ):
        # If post has no content, fetch it from get_post API
        if not post.content:
            try:
                async with pawchive_client_scope(client) as api_client:
                    if isinstance(post, Revision):
                        revisions = await api_client.list_post_revisions(post.service, post.user, post.id)
                        selected_revision = next(
                            (revision for revision in revisions if revision.revision_id == post.revision_id),
                            None,
                        )
                        if selected_revision is None:
                            raise ValueError(f"Revision {post.revision_id} was not returned by Pawchive")
                        post = selected_revision
                    else:
                        post = await api_client.get_post(post.service, post.user, post.id)
            except (PawchiveError, ValueError) as error:
                logger.error(
                    generate_msg(
                        "Failed to fetch post content",
                        post_name=post.title or "Unknown",
                        post_id=post.id,
                        creator_id=post.user,
                        service=post.service,
                    )
                )
                raise FetchInterruptError(error) from error

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
                    if image_src.startswith("/") and not image_src.startswith("//"):
                        # Relative path - construct full URL
                        image_path = image_src
                    elif image_src.startswith("http://") or image_src.startswith("https://"):
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

                    if (
                        not config.job.allow_list or any(map(lambda x: fnmatch(alt_filename, x), config.job.allow_list))
                    ) and not any(map(lambda x: fnmatch(alt_filename, x), config.job.block_list)):
                        # Regenerate filename with correct counter
                        should_use_sequential = (
                            config.job.sequential_filename
                            and image_file_path.suffix.lower() not in config.job.sequential_filename_excludes
                        )
                        if should_use_sequential:
                            basic_filename = f"{sequential_counter}{image_file_path.suffix}"
                            alt_filename = generate_filename(post, basic_filename, config.job.filename_format)
                            sequential_counter += 1

                        jobs.append(
                            Job(
                                path=attachments_path,
                                alt_filename=alt_filename,
                                server_path=image_path,
                                type=PostFileTypeEnum.Attachment,
                            )
                        )

    return jobs


@dataclass(slots=True)
class CreatorJobGeneration:
    fetched_posts: int = 0
    accepted_posts: int = 0
    generated_jobs: int = 0
    blocked_by: dict[str, int] = field(default_factory=dict)


JobSink = Callable[[Job], Awaitable[None]]


async def create_job_from_creator(
    service: str,
    creator_id: str,
    path: Path,
    *,
    all_pages: bool = False,
    offset: int = 0,
    length: int | None = 50,
    save_creator_indices: bool = False,
    mix_posts: bool | None = None,
    start_time: datetime | None,
    end_time: datetime | None,
    keywords: set[str] | None = None,
    keywords_exclude: set[str] | None = None,
    blocker_engine: BlockerEngine | None = None,
    client: PawchiveClient | None = None,
) -> ActionRet[list[Job]]:
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
    :param blocker_engine: Structured blockers applied before post jobs are created
    :param client: Pawchive client to reuse across all creator requests
    """
    job_list: list[Job] = []

    async def collect(job: Job) -> None:
        job_list.append(job)

    result = await produce_jobs_from_creator(
        service,
        creator_id,
        path,
        collect,
        all_pages=all_pages,
        offset=offset,
        length=length,
        save_creator_indices=save_creator_indices,
        mix_posts=mix_posts,
        start_time=start_time,
        end_time=end_time,
        keywords=keywords,
        keywords_exclude=keywords_exclude,
        blocker_engine=blocker_engine,
        client=client,
    )
    if not result:
        return ActionRet(code=result.code, message=result.message, exception=result.exception)
    return ActionRet(data=job_list)


async def produce_jobs_from_creator(
    service: str,
    creator_id: str,
    path: Path,
    sink: JobSink,
    *,
    all_pages: bool = False,
    offset: int = 0,
    length: int | None = 50,
    save_creator_indices: bool = False,
    mix_posts: bool | None = None,
    start_time: datetime | None,
    end_time: datetime | None,
    keywords: set[str] | None = None,
    keywords_exclude: set[str] | None = None,
    blocker_engine: BlockerEngine | None = None,
    client: PawchiveClient | None = None,
) -> ActionRet[CreatorJobGeneration]:
    """Generate and emit creator jobs as soon as each post has been processed."""
    if client is None:
        async with pawchive_client_scope(None) as api_client:
            return await produce_jobs_from_creator(
                service,
                creator_id,
                path,
                sink,
                all_pages=all_pages,
                offset=offset,
                length=length,
                save_creator_indices=save_creator_indices,
                mix_posts=mix_posts,
                start_time=start_time,
                end_time=end_time,
                keywords=keywords,
                keywords_exclude=keywords_exclude,
                blocker_engine=blocker_engine,
                client=api_client,
            )

    selected_mix_posts = config.job.mix_posts if mix_posts is None else mix_posts
    active_engine = _creator_blocker_engine(blocker_engine, keywords_exclude)
    context = BlockerContext(service=service, creator_id=creator_id)
    summary = CreatorJobGeneration()
    indexed_posts: dict[str, Post] = {}
    indexed_paths: dict[str, Path] = {}

    if config.job.include_revisions:
        logger.warning(
            "`job.include_revisions` is enabled and will fetch post revisions, "
            "which may take time. Disable if not needed."
        )
    if config.job.extract_content or config.job.extract_external_links or config.job.extract_content_images:
        logger.warning("Content extraction is enabled and will inspect posts individually; disable it when not needed.")

    logger.info(f"Start fetching posts from creator {creator_id}")
    start_offset = offset - offset % 50
    skip = offset % 50
    requested_length = 50 if length is None else length
    consumed = 0

    try:
        async for page in fetch_creator_posts(
            service=service,
            creator_id=creator_id,
            offset=start_offset,
            client=client,
        ):
            for post in page:
                if skip:
                    skip -= 1
                    continue
                if not all_pages and consumed >= requested_length:
                    break
                consumed += 1
                summary.fetched_posts += 1
                if not _post_matches_filters(post, start_time, end_time, keywords):
                    continue
                if decision := await active_engine.evaluate(post, context):
                    summary.blocked_by[decision.blocker_id] = summary.blocked_by.get(decision.blocker_id, 0) + 1
                    continue

                summary.accepted_posts += 1
                post_path = _creator_post_path(post, path, selected_mix_posts)
                if not selected_mix_posts and save_creator_indices:
                    indexed_posts[post.id] = post
                    indexed_paths[post.id] = generate_grouped_post_path(post, path) / sanitize_filename(
                        post.title or post.id
                    )

                try:
                    jobs = await create_job_from_post(
                        post=post,
                        post_path=post_path,
                        post_dir=not selected_mix_posts,
                        dump_post_data=not selected_mix_posts,
                        client=client,
                    )
                except FetchInterruptError as error:
                    return action_error(error.error)
                await _emit_jobs(jobs, sink, summary)

                if config.job.include_revisions and not selected_mix_posts:
                    try:
                        await _emit_revision_jobs(
                            post,
                            post_path,
                            service,
                            creator_id,
                            client,
                            sink,
                            summary,
                        )
                    except FetchInterruptError as error:
                        return action_error(error.error)
            if not all_pages and consumed >= requested_length:
                break
    except FetchInterruptError as error:
        return action_error(error.error)

    if not selected_mix_posts and save_creator_indices:
        try:
            await _write_creator_indices(service, creator_id, path, indexed_posts, indexed_paths)
        except OSError as error:
            raise StagedFailure(FailureStage.index_write, error) from error
    logger.info(
        f"Creator {creator_id}: accepted {summary.accepted_posts} of {summary.fetched_posts} posts, "
        f"generated {summary.generated_jobs} jobs"
    )
    return ActionRet(data=summary)


def _creator_blocker_engine(
    blocker_engine: BlockerEngine | None,
    keywords_exclude: set[str] | None,
) -> BlockerEngine:
    active_blockers = list(blocker_engine.blockers if blocker_engine is not None else ())
    if legacy_spec := legacy_keyword_blocker(keywords_exclude or ()):
        logger.warning(
            "`job.keywords_exclude` is deprecated; migrate it to a global field-match blocker in ktoolbox.toml."
        )
        active_blockers.insert(0, blocker_registry.build(legacy_spec))
    return BlockerEngine(active_blockers)


def _post_matches_filters(
    post: Post,
    start_time: datetime | None,
    end_time: datetime | None,
    keywords: set[str] | None,
) -> bool:
    if (start_time or end_time) and not list(filter_posts_by_date([post], start_time, end_time)):
        return False
    return not keywords or bool(list(filter_posts_by_keywords([post], keywords)))


def _creator_post_path(post: Post, path: Path, mix_posts: bool) -> Path:
    if mix_posts:
        return path
    return generate_grouped_post_path(post, path) / generate_post_path_name(post)


async def _emit_jobs(jobs: list[Job], sink: JobSink, summary: CreatorJobGeneration) -> None:
    for job in jobs:
        await sink(job)
        summary.generated_jobs += 1


async def _emit_revision_jobs(
    post: Post,
    post_path: Path,
    service: str,
    creator_id: str,
    client: PawchiveClient,
    sink: JobSink,
    summary: CreatorJobGeneration,
) -> None:
    try:
        revisions = await client.list_post_revisions(service, creator_id, post.id)
        for revision in revisions:
            revision_path = post_path / config.job.post_structure.revisions / generate_post_path_name(revision)
            revision_jobs = await create_job_from_post(
                post=revision,
                post_path=revision_path,
                dump_post_data=True,
                client=client,
            )
            await _emit_jobs(revision_jobs, sink, summary)
    except PawchiveNotFoundError:
        return
    except PawchiveError as error:
        logger.warning(f"Failed to fetch revisions for post {post.id}: {error}")
    except FetchInterruptError as error:
        raise error


async def _write_creator_indices(
    service: str,
    creator_id: str,
    path: Path,
    posts: dict[str, Post],
    posts_path: dict[str, Path],
) -> None:
    indices = CreatorIndices(creator_id=creator_id, service=service, posts=posts, posts_path=posts_path)
    index_path = path / DataStorageNameEnum.CreatorIndicesData.value
    temporary_path = index_path.with_suffix(f"{index_path.suffix}.tmp")
    try:
        async with aiofiles.open(temporary_path, "w", encoding="utf-8") as file:
            await file.write(indices.model_dump_json(indent=config.json_dump_indent))
        await aiofiles.os.replace(temporary_path, index_path)
    finally:
        try:
            await aiofiles.os.remove(temporary_path)
        except FileNotFoundError:
            pass
