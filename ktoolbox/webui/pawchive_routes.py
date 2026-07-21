from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import ValidationError

from ktoolbox.action.search import search_creator, search_creator_post
from ktoolbox.api.errors import PawchiveError, PawchiveNotFoundError
from ktoolbox.api.generated import CreatorSummary, Post, Revision
from ktoolbox.api.utils import create_pawchive_client
from ktoolbox.configuration import RuntimeContext
from ktoolbox.webui.auth import require_session
from ktoolbox.webui.database import WebUISession
from ktoolbox.webui.models import SiteVersionResponse

SessionDependency = Annotated[WebUISession, Depends(require_session)]


def create_pawchive_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/pawchive")

    def runtime(request: Request) -> RuntimeContext:
        return cast(RuntimeContext, request.app.state.runtime_context).snapshot()

    @router.get("/creators", response_model=list[CreatorSummary])
    async def creators(
        request: Request,
        _: SessionDependency,
        creator_id: str | None = None,
        name: str | None = None,
        service: str | None = None,
    ) -> list[CreatorSummary]:
        context = runtime(request)
        with context.activate():
            async with create_pawchive_client() as client:
                result = await search_creator(id=creator_id, name=name, service=service, client=client)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=result.message or "creator search failed"
            )
        return list(result.data or ())

    @router.get("/posts", response_model=list[Post])
    async def posts(
        request: Request,
        _: SessionDependency,
        creator_id: str | None = None,
        name: str | None = None,
        service: str | None = None,
        query: str | None = None,
        offset: int | None = None,
    ) -> list[Post]:
        context = runtime(request)
        with context.activate():
            async with create_pawchive_client() as client:
                result = await search_creator_post(
                    id=creator_id,
                    name=name,
                    service=service,
                    q=query,
                    o=offset,
                    client=client,
                )
        if not result:
            code = (
                status.HTTP_422_UNPROCESSABLE_CONTENT
                if not any((creator_id, name, service))
                else status.HTTP_502_BAD_GATEWAY
            )
            raise HTTPException(status_code=code, detail=result.message or "post search failed")
        return result.data or []

    @router.get("/posts/{service}/{creator_id}/{post_id}", response_model=Post | Revision)
    async def post_details(
        service: str,
        creator_id: str,
        post_id: str,
        request: Request,
        _: SessionDependency,
        revision_id: str | None = None,
    ) -> Post | Revision:
        context = runtime(request)
        try:
            with context.activate():
                async with create_pawchive_client() as client:
                    if revision_id is None:
                        return await client.get_post(service, creator_id, post_id)
                    revisions = await client.list_post_revisions(service, creator_id, post_id)
            revision = next((item for item in revisions if str(item.revision_id) == revision_id), None)
            if revision is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="revision not found")
            return revision
        except PawchiveNotFoundError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        except (PawchiveError, ValidationError) as error:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

    @router.get("/site-version", response_model=SiteVersionResponse)
    async def site_version(request: Request, _: SessionDependency) -> SiteVersionResponse:
        context = runtime(request)
        try:
            with context.activate():
                async with create_pawchive_client() as client:
                    version = await client.get_app_version()
        except PawchiveError as error:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
        return SiteVersionResponse(version=version)

    return router
