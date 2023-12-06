from pathvalidate import sanitize_filename

from ktoolbox.api.model import Post
from ktoolbox.configuration import config

__all__ = ["generate_post_path_name"]


def generate_post_path_name(post: Post) -> str:
    """Generate directory name for post to save."""
    if config.job.post_id_as_path or not post.title:
        return post.id
    else:
        return sanitize_filename(post.title)
