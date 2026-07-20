from __future__ import annotations

from collections.abc import AsyncGenerator

from ktoolbox.api.client import PawchiveClient
from ktoolbox.api.errors import PawchiveError, PawchiveNotFoundError
from ktoolbox.api.generated import Post
from ktoolbox.api.utils import SEARCH_STEP, pawchive_client_scope

__all__ = ["FetchInterruptError", "fetch_creator_posts"]


class FetchInterruptError(Exception):
    """Raised when paginated Pawchive fetching cannot continue."""

    def __init__(self, error: Exception) -> None:
        self.error = error
        super().__init__(str(error))


async def fetch_creator_posts(
    service: str,
    creator_id: str,
    offset: int = 0,
    *,
    client: PawchiveClient | None = None,
) -> AsyncGenerator[list[Post], None]:
    """Yield every page of posts for one creator."""
    async with pawchive_client_scope(client) as api_client:
        while True:
            try:
                posts = await api_client.list_creator_posts(service, creator_id, offset=offset)
            except PawchiveNotFoundError:
                return
            except PawchiveError as error:
                raise FetchInterruptError(error) from error

            yield posts
            if len(posts) < SEARCH_STEP:
                return
            offset += SEARCH_STEP
