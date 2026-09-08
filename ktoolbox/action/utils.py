from collections.abc import Iterator
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

from loguru import logger
from pathvalidate import sanitize_filename

from ktoolbox.api.generated import Post
from ktoolbox.job import CreatorIndices
from ktoolbox.project_config import ProjectNamingConfiguration
from ktoolbox.publication_time import (
    PublishedTimePolicy,
    effective_post_timestamp,
    effective_published,
    target_boundary,
)

__all__ = [
    "generate_post_path_name",
    "generate_creator_path_name",
    "generate_revision_path_name",
    "generate_filename",
    "generate_year_dirname",
    "generate_month_dirname",
    "generate_grouped_post_path",
    "filter_posts_by_date",
    "filter_posts_by_indices",
    "match_post_keywords",
    "filter_posts_by_keywords",
    "filter_posts_by_keywords_exclude",
    "extract_content_images",
]

TIME_FORMAT = "%Y-%m-%d"


class _ContentImageParser(HTMLParser):
    """HTML parser to extract image sources from content"""

    def __init__(self) -> None:
        super().__init__()
        self.image_sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "img":
            for attr_name, attr_value in attrs:
                if attr_name.lower() == "src" and attr_value:
                    self.image_sources.append(attr_value)


def _post_template_values(post: Post, published_time: PublishedTimePolicy) -> dict[str, object]:
    published = effective_published(post, published_time)
    return {
        "id": post.id,
        "post_id": post.id,
        "user": post.user,
        "creator_id": post.user,
        "service": post.service,
        "platform": post.service,
        "title": post.title or post.id,
        "added": post.added.strftime(TIME_FORMAT) if post.added else "",
        "published": published.strftime(TIME_FORMAT) if published else "",
        "edited": post.edited.strftime(TIME_FORMAT) if post.edited else "",
    }


def _format_component(template: str, fallback: str, *args: object, **values: object) -> str:
    try:
        rendered = sanitize_filename(template.format(*args, **values)).strip()
    except (KeyError, IndexError, ValueError) as error:
        raise ValueError(f"invalid naming template {template!r}: {error}") from error
    return rendered or sanitize_filename(fallback)


def generate_creator_path_name(
    service: str,
    creator_id: str,
    creator_name: str | None,
    naming: ProjectNamingConfiguration,
    *,
    alias: str | None = None,
) -> str:
    """Generate one creator directory component from project naming."""
    return _format_component(
        naming.creator_dirname_format,
        creator_id,
        creator_name=creator_name or creator_id,
        creator_id=creator_id,
        service=service,
        platform=service,
        alias=alias or "",
    )


def generate_post_path_name(
    post: Post,
    naming: ProjectNamingConfiguration,
    published_time: PublishedTimePolicy,
) -> str:
    """Generate directory name for post to save."""
    return _format_component(
        naming.post_dirname_format,
        post.id,
        **_post_template_values(post, published_time),
    )


def generate_revision_path_name(
    post: Post,
    naming: ProjectNamingConfiguration,
    published_time: PublishedTimePolicy,
) -> str:
    """Generate one revision directory component from project naming."""
    revision_id = str(getattr(post, "revision_id", "") or "")
    return _format_component(
        naming.revision_dirname_format,
        revision_id or post.id,
        revision_id=revision_id,
        **_post_template_values(post, published_time),
    )


def generate_year_dirname(
    post: Post,
    naming: ProjectNamingConfiguration,
    published_time: PublishedTimePolicy,
) -> str:
    """Generate year directory name for post grouping."""
    # Use published date, fall back to added date
    post_date = effective_post_timestamp(post, published_time)
    if not post_date:
        return "unknown"

    return _format_component(naming.year_dirname_format, str(post_date.year), year=post_date.year)


def generate_month_dirname(
    post: Post,
    naming: ProjectNamingConfiguration,
    published_time: PublishedTimePolicy,
) -> str:
    """Generate month directory name for post grouping."""
    # Use published date, fall back to added date
    post_date = effective_post_timestamp(post, published_time)
    if not post_date:
        return "unknown"

    return _format_component(
        naming.month_dirname_format,
        f"{post_date.year}-{post_date.month:02d}",
        year=post_date.year,
        month=post_date.month,
    )


def generate_grouped_post_path(
    post: Post,
    base_path: Path,
    naming: ProjectNamingConfiguration,
    published_time: PublishedTimePolicy,
) -> Path:
    """
    Generate the full path for a post considering year/month grouping.
    
    :param post: Post object
    :param base_path: Base path (usually creator directory)
    :return: Full path where the post should be saved
    """
    result_path = base_path

    if naming.group_by_year:
        year_dirname = generate_year_dirname(post, naming, published_time)
        result_path = result_path / year_dirname

        if naming.group_by_month:
            month_dirname = generate_month_dirname(post, naming, published_time)
            result_path = result_path / month_dirname

    return result_path


def generate_filename(
    post: Post,
    basic_name: str,
    filename_format: str,
    published_time: PublishedTimePolicy,
) -> str:
    """Generate download filename"""
    basic_name_path = Path(basic_name)
    basic_name_filename = basic_name.replace(basic_name_path.suffix, "")
    return _format_component(
        filename_format,
        basic_name_filename,
        basic_name_filename,
        **_post_template_values(post, published_time),
    ) + basic_name_path.suffix


def _match_post_date(
    post: Post,
    start_date: datetime | None,
    end_date: datetime | None,
    published_time: PublishedTimePolicy,
) -> bool:
    """
    Check if the post date match the time range.

    :param post: Target post object
    :param start_date: Start time of the time range
    :param end_date: End time of the time range
    :return: Whether if the post publish date match the time range
    """
    post_date = effective_post_timestamp(post, published_time)
    normalized_start = target_boundary(start_date, published_time) if start_date else None
    normalized_end = target_boundary(end_date, published_time) if end_date else None
    if normalized_start and post_date and post_date < normalized_start:
        return False
    if normalized_end and post_date and post_date > normalized_end:
        return False
    return True


def filter_posts_by_date(
    post_list: list[Post],
    start_date: datetime | None,
    end_date: datetime | None,
    published_time: PublishedTimePolicy,
) -> Iterator[Post]:
    """
    Filter posts by publish date range

    :param post_list: List of posts
    :param start_date: Start time of the time range
    :param end_date: End time of the time range
    """
    post_filter = filter(
        lambda x: _match_post_date(x, start_date, end_date, published_time),
        post_list,
    )
    yield from post_filter


def filter_posts_by_indices(
    posts: list[Post],
    indices: CreatorIndices,
) -> tuple[list[Post], CreatorIndices]:
    """
    Compare and filter posts by ``CreatorIndices`` data

    Only keep posts that was edited after last download.

    :param posts: Posts to filter
    :param indices: ``CreatorIndices`` data to use
    :return: A updated ``List[Post]`` and updated **new** ``CreatorIndices`` instance
    """
    new_list: list[Post] = []
    for post in posts:
        previous = indices.posts.get(post.id)
        if previous is None or (
            post.edited is not None
            and (previous.edited is None or post.edited > previous.edited)
        ):
            new_list.append(post)
    new_indices = indices.model_copy(deep=True)
    for post in new_list:
        new_indices.posts[post.id] = post
    return new_list, new_indices


def match_post_keywords(post: Post, keywords: set[str]) -> bool:
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
    post_list: list[Post],
    keywords: set[str] | None,
) -> Iterator[Post]:
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


def filter_posts_by_keywords_exclude(
    post_list: list[Post],
    keywords_exclude: set[str] | None,
) -> Iterator[Post]:
    """
    Filter out posts that contain any of the specified keywords in title

    :param post_list: List of posts
    :param keywords_exclude: Set of keywords to exclude (case-insensitive), None means no filtering
    """
    if not keywords_exclude:
        yield from post_list
        return

    # Exclude posts that match any of the exclude keywords
    post_filter = filter(lambda x: not match_post_keywords(x, keywords_exclude), post_list)
    yield from post_filter


def extract_content_images(content: str) -> list[str]:
    """
    Extract image sources from HTML content

    :param content: HTML content string
    :return: List of image source URLs/paths
    """
    if not content:
        return []

    parser = _ContentImageParser()
    try:
        parser.feed(content)
    except Exception as error:
        logger.warning(f"Failed to parse HTML content for images: {error}")
        return []

    return parser.image_sources
