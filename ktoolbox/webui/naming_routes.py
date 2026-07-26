from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from ktoolbox.project_config import ProjectConfigStore
from ktoolbox.webui.auth import require_csrf, require_session
from ktoolbox.webui.config_store import content_revision
from ktoolbox.webui.database import WebUISession
from ktoolbox.webui.naming_models import (
    NamingApplyRequest,
    NamingConfigurationResponse,
    NamingConversionResponse,
    NamingPreviewRequest,
    NamingPreviewResponse,
    StartupNoticeResponse,
)
from ktoolbox.webui.naming_service import (
    NamingConversionError,
    NamingConversionService,
    NamingPreviewStaleError,
)


def naming_service(request: Request) -> NamingConversionService:
    return cast(NamingConversionService, request.app.state.naming_service)


SessionDependency = Annotated[WebUISession, Depends(require_session)]
CsrfDependency = Annotated[WebUISession, Depends(require_csrf)]
NamingServiceDependency = Annotated[NamingConversionService, Depends(naming_service)]


def create_naming_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["naming"])

    @router.get("/naming", response_model=NamingConfigurationResponse)
    async def get_naming(
        request: Request,
        _: SessionDependency,
        service: NamingServiceDependency,
    ) -> NamingConfigurationResponse:
        store = ProjectConfigStore(request.app.state.runtime_context.project_root / "ktoolbox.toml")
        project = store.load()
        return NamingConfigurationResponse(
            naming=project.naming,
            revision=content_revision(store.load_text()),
            suggested_download_roots=await service.suggested_download_roots(),
        )

    @router.post("/naming/preview", response_model=NamingPreviewResponse)
    async def preview_naming(
        payload: NamingPreviewRequest,
        _: CsrfDependency,
        service: NamingServiceDependency,
    ) -> NamingPreviewResponse:
        try:
            return await service.preview(payload.naming)
        except NamingConversionError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(error),
            ) from error

    @router.post(
        "/naming/apply",
        response_model=NamingConversionResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def apply_naming(
        payload: NamingApplyRequest,
        _: CsrfDependency,
        service: NamingServiceDependency,
    ) -> NamingConversionResponse:
        try:
            return await service.apply(
                payload.preview_id,
                payload.selected_creators,
                convert_existing=payload.convert_existing,
            )
        except NamingPreviewStaleError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
        except LookupError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="preview not found") from error
        except NamingConversionError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(error),
            ) from error

    @router.get("/naming/conversions", response_model=list[NamingConversionResponse])
    async def list_naming_conversions(
        _: SessionDependency,
        service: NamingServiceDependency,
    ) -> list[NamingConversionResponse]:
        return await service.list_conversions()

    @router.get("/naming/conversions/{conversion_id}", response_model=NamingConversionResponse)
    async def get_naming_conversion(
        conversion_id: str,
        _: SessionDependency,
        service: NamingServiceDependency,
    ) -> NamingConversionResponse:
        try:
            return await service.get(conversion_id)
        except LookupError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversion not found") from error

    @router.post(
        "/naming/conversions/{conversion_id}/cancel",
        response_model=NamingConversionResponse,
    )
    async def cancel_naming_conversion(
        conversion_id: str,
        _: CsrfDependency,
        service: NamingServiceDependency,
    ) -> NamingConversionResponse:
        try:
            return await service.cancel(conversion_id)
        except LookupError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversion not found") from error
        except NamingConversionError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error

    @router.delete(
        "/naming/conversions/{conversion_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def delete_naming_conversion(
        conversion_id: str,
        _: CsrfDependency,
        service: NamingServiceDependency,
    ) -> Response:
        try:
            await service.delete(conversion_id)
        except LookupError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversion not found") from error
        except NamingConversionError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.get("/startup-notices", response_model=list[StartupNoticeResponse])
    async def list_startup_notices(
        _: SessionDependency,
        service: NamingServiceDependency,
    ) -> list[StartupNoticeResponse]:
        return await service.notices()

    @router.post(
        "/startup-notices/{notice_id}/acknowledge",
        response_model=StartupNoticeResponse,
    )
    async def acknowledge_startup_notice(
        notice_id: str,
        _: CsrfDependency,
        service: NamingServiceDependency,
    ) -> StartupNoticeResponse:
        try:
            return await service.acknowledge_notice(notice_id)
        except LookupError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="notice not found") from error

    return router
