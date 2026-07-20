from __future__ import annotations

from collections.abc import Iterator

from pydantic import ValidationError

from ktoolbox._enum import RetCodeEnum
from ktoolbox.action.base import ActionRet, action_error
from ktoolbox.api.client import PawchiveClient
from ktoolbox.api.errors import PawchiveError
from ktoolbox.api.generated import CreatorSummary, Post
from ktoolbox.api.utils import pawchive_client_scope
from ktoolbox.utils import BaseRet, generate_msg

__all__ = ["search_creator", "search_creator_post"]


async def search_creator(
    id: str | None = None,
    name: str | None = None,
    service: str | None = None,
    *,
    client: PawchiveClient | None = None,
) -> BaseRet[Iterator[CreatorSummary]]:
    """Search Pawchive creators using locally applied filters."""

    def matches(creator: CreatorSummary) -> bool:
        if id is not None and creator.id != id:
            return False
        if name is not None and name not in creator.name:
            return False
        return service is None or creator.service == service

    try:
        async with pawchive_client_scope(client) as api_client:
            creators = await api_client.list_creators()
    except (PawchiveError, ValidationError) as error:
        failure = action_error(error)
        return BaseRet(code=failure.code, message=failure.message, exception=failure.exception, data=iter(()))
    return ActionRet(data=iter(filter(matches, creators)))


async def search_creator_post(
    id: str | None = None,
    name: str | None = None,
    service: str | None = None,
    q: str | None = None,
    o: int | None = None,
    *,
    client: PawchiveClient | None = None,
) -> BaseRet[list[Post]]:
    """Search posts for one creator or creators selected by local filters."""
    if not any((id, name, service)):
        return ActionRet(
            code=RetCodeEnum.MissingParameter,
            message=generate_msg("At least one of creator_id, name, or service is required."),
        )

    try:
        async with pawchive_client_scope(client) as api_client:
            if id is not None and service:
                creator_posts = await api_client.list_creator_posts(
                    service,
                    id,
                    query=q,
                    offset=o,
                )
                return ActionRet(data=creator_posts)

            creators_result = await search_creator(
                id=id,
                name=name,
                service=service,
                client=api_client,
            )
            if not creators_result:
                return ActionRet(
                    code=creators_result.code,
                    message=creators_result.message,
                    exception=creators_result.exception,
                )

            posts: list[Post] = []
            for creator in creators_result.data or ():
                posts.extend(
                    await api_client.list_creator_posts(
                        creator.service,
                        creator.id,
                        query=q,
                        offset=o,
                    )
                )
            return ActionRet(data=posts)
    except (PawchiveError, ValidationError) as error:
        return action_error(error)
