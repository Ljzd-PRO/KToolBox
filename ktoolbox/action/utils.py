from datetime import datetime
from pathlib import Path
from typing import Optional, List, Generator, Any, Tuple, Set

from loguru import logger
from pathvalidate import sanitize_filename

from ktoolbox.api.model import Post
from ktoolbox.configuration import config
from ktoolbox.job import CreatorIndices

__all__ = [
    "generate_post_path_name",
    "generate_filename",
    "filter_posts_by_date",
    "filter_posts_by_indices",
    "match_post_keywords",
    "filter_posts_by_keywords"
]

TIME_FORMAT = "%Y-%m-%d"


def generate_post_path_name(post: Post) -> str:
    """Generate directory name for post to save."""
    if not post.title:
        return post.id
    else:
        try:
            return sanitize_filename(
                config.job.post_dirname_format.format(
                    id=post.id,
                    user=post.user,
                    service=post.service,
                    title=post.title,
                    added=post.added.strftime(TIME_FORMAT) if post.added else "",
                    published=post.published.strftime(TIME_FORMAT) if post.published else "",
                    edited=post.edited.strftime(TIME_FORMAT) if post.edited else ""
                )
            )
        except KeyError as e:
            logger.error(f"`JobConfiguration.post_dirname_format` contains invalid key: {e}")
            exit(1)


def generate_filename(post: Post, basic_name: str, filename_format: str) -> str:
    """Generate download filename"""
    basic_name_path = Path(basic_name)
    basic_name_filename = basic_name.replace(basic_name_path.suffix, "")
    try:
        return sanitize_filename(
            filename_format.format(
                basic_name_filename,
                id=post.id,
                user=post.user,
                service=post.service,
                title=post.title,
                added=post.added.strftime(TIME_FORMAT) if post.added else "",
                published=post.published.strftime(TIME_FORMAT) if post.published else "",
                edited=post.edited.strftime(TIME_FORMAT) if post.edited else ""
            ) + basic_name_path.suffix
        )
    except KeyError as e:
        logger.error(
            f"`JobConfiguration.filename_format` or `PostStructureConfiguration.file` contains invalid key: {e}")
        exit(1)


def _match_post_date(
        post: Post,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
) -> bool:
    """
    Check if the post date match the time range.

    :param post: Target post object
    :param start_date: Start time of the time range
    :param end_date: End time of the time range
    :return: Whether if the post publish date match the time range
    """
    post_date = post.published or post.added
    if start_date and post_date and post_date < start_date:
        return False
    if end_date and post_date and post_date > end_date:
        return False
    return True


def filter_posts_by_date(
        post_list: List[Post],
        start_date: Optional[datetime],
        end_date: Optional[datetime]
) -> Generator[Post, Any, Any]:
    """
    Filter posts by publish date range

    :param post_list: List of posts
    :param start_date: Start time of the time range
    :param end_date: End time of the time range
    """
    post_filter = filter(lambda x: _match_post_date(x, start_date, end_date), post_list)
    yield from post_filter


def filter_posts_by_indices(posts: List[Post], indices: CreatorIndices) -> Tuple[List[Post], CreatorIndices]:
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
    new_indices = indices.model_copy(deep=True)
    for post in new_list:
        new_indices.posts[post.id] = post
    return new_list, new_indices


def match_post_keywords(post: Post, keywords: Set[str]) -> bool:
    """
    Check if the post contains any of the specified keywords.

    :param post: Target post object
    :param keywords: Set of keywords to search for (case-insensitive)
    :return: Whether the post contains any of the keywords in title
    """
    if not keywords:
        return True
    
    # Only search in post title
    searchable_text = ""
    if post.title:
        searchable_text = post.title.lower()
    
    # Check if any keyword is found in the title
    return any(keyword.lower() in searchable_text for keyword in keywords)


def filter_posts_by_keywords(
        post_list: List[Post],
        keywords: Optional[Set[str]]
) -> Generator[Post, Any, Any]:
    """
    Filter posts by keywords in title

    :param post_list: List of posts
    :param keywords: Set of keywords to search for (case-insensitive), None means no filtering
    """
    if not keywords:
        yield from post_list
        return
    
    post_filter = filter(lambda x: match_post_keywords(x, keywords), post_list)
    yield from post_filter
