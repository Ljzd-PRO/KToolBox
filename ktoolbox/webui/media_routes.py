from __future__ import annotations

from typing import Annotated, Any, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from ktoolbox.configuration import RuntimeContext
from ktoolbox.webui.auth import require_session
from ktoolbox.webui.database import WebUISession
from ktoolbox.webui.media import MediaPayload, MediaProxyError, MediaProxyService, MediaVariant

SessionDependency = Annotated[WebUISession, Depends(require_session)]
VariantQuery = Annotated[MediaVariant, Query()]

IMAGE_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Validated image bytes.",
        "content": {
            "image/webp": {},
            "image/jpeg": {},
            "image/png": {},
            "image/gif": {},
        },
    }
}


def create_media_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/media")

    def runtime(request: Request) -> RuntimeContext:
        return cast(RuntimeContext, request.app.state.runtime_context).snapshot()

    def service(request: Request) -> MediaProxyService:
        return cast(MediaProxyService, request.app.state.media_proxy)

    @router.get(
        "/creators/{platform}/{creator_id}/avatar",
        response_class=Response,
        responses=IMAGE_RESPONSES,
    )
    async def creator_avatar(
        platform: str,
        creator_id: str,
        variant: VariantQuery,
        request: Request,
        _: SessionDependency,
    ) -> Response:
        return media_response(
            await _fetch_creator(service(request), runtime(request), platform, creator_id, "avatar", variant)
        )

    @router.get(
        "/creators/{platform}/{creator_id}/banner",
        response_class=Response,
        responses=IMAGE_RESPONSES,
    )
    async def creator_banner(
        platform: str,
        creator_id: str,
        variant: VariantQuery,
        request: Request,
        _: SessionDependency,
    ) -> Response:
        return media_response(
            await _fetch_creator(service(request), runtime(request), platform, creator_id, "banner", variant)
        )

    @router.get("/files", response_class=Response, responses=IMAGE_RESPONSES)
    async def media_file(
        path: str,
        variant: VariantQuery,
        request: Request,
        _: SessionDependency,
    ) -> Response:
        try:
            payload = await service(request).fetch_file(runtime(request), path, variant)
        except MediaProxyError as error:
            raise media_http_error(error) from error
        return media_response(payload)

    return router


async def _fetch_creator(
    service: MediaProxyService,
    context: RuntimeContext,
    platform: str,
    creator_id: str,
    kind: Literal["avatar", "banner"],
    variant: MediaVariant,
) -> MediaPayload:
    try:
        return await service.fetch_creator(context, platform, creator_id, kind, variant)
    except MediaProxyError as error:
        raise media_http_error(error) from error


def media_http_error(error: MediaProxyError) -> HTTPException:
    return HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": "The requested media preview is unavailable."},
    )


def media_response(payload: MediaPayload) -> Response:
    return Response(
        content=payload.content,
        media_type=payload.media_type,
        headers={
            "Cache-Control": "private, no-store",
            "Cross-Origin-Resource-Policy": "same-origin",
        },
    )
