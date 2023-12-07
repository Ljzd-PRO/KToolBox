from datetime import datetime
from typing import Optional, List, Generator, Any, Tuple

from pathvalidate import sanitize_filename

from ktoolbox.api.model import Post
from ktoolbox.configuration import config
from ktoolbox.job import CreatorIndices

__all__ = ["generate_post_path_name", "filter_posts_by_time", "filter_posts_by_indices"]


def generate_post_path_name(post: Post) -> str:
    """Generate directory name for post to save."""
    if config.job.post_id_as_path or not post.title:
        return post.id
    else:
        return sanitize_filename(post.title)


def _match_post_time(
        post: Post,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
) -> bool:
    """
    Check if the post publish date match the time range.

    :param post: Target post object
    :param start_time: Start time of the time range
    :param end_time: End time of the time range
    :return: Whether if the post publish date match the time range
    """
    if start_time and post.published < start_time:
        return False
    if end_time and post.published > end_time:
        return False
    return True


def filter_posts_by_time(
        post_list: List[Post],
        start_time: Optional[datetime],
        end_time: Optional[datetime]
) -> Generator[Post, Any, Any]:
    """
    Filter posts by publish time range

    :param post_list: List of posts
    :param start_time: Start time of the time range
    :param end_time: End time of the time range
    """
    post_filter = filter(lambda x: _match_post_time(x, start_time, end_time), post_list)
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
    new_indices = indices.copy(deep=True)
    for post in new_list:
        new_indices.posts[post.id] = post
    return new_list, new_indices
