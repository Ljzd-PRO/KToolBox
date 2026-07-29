from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from ktoolbox.naming_sources import NamingSourceParseError
from ktoolbox.webui.auth import require_csrf, require_session
from ktoolbox.webui.database import WebUISession
from ktoolbox.webui.naming_models import (
    LegacyNamingMigrationApplyRequest,
    LegacyNamingMigrationResponse,
    LegacyNamingMigrationResultResponse,
    NamingApplyRequest,
    NamingConfigurationResponse,
    NamingConversionResponse,
    NamingLayoutVersionResponse,
    NamingLegacyContextResponse,
    NamingPreviewRequest,
    NamingPreviewResponse,
    NamingSourceParseRequest,
    NamingSourceParseResponse,
    NamingUpdateRequest,
    StartupNoticeResolveRequest,
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
        _: SessionDependency,
        service: NamingServiceDependency,
    ) -> NamingConfigurationResponse:
        return await service.configuration()

    @router.patch("/naming", response_model=NamingConfigurationResponse)
    async def update_naming(
        payload: NamingUpdateRequest,
        _: CsrfDependency,
        service: NamingServiceDependency,
    ) -> NamingConfigurationResponse:
        try:
            return await service.update_naming(
                payload.section,
                payload.naming,
                payload.revision,
                default_output=payload.default_output,
            )
        except NamingPreviewStaleError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
        except NamingConversionError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(error),
            ) from error

    @router.get("/naming/legacy-context", response_model=NamingLegacyContextResponse)
    async def get_naming_legacy_context(
        _: SessionDependency,
        service: NamingServiceDependency,
    ) -> NamingLegacyContextResponse:
        return await service.legacy_context()

    @router.get(
        "/naming/layout-versions",
        response_model=list[NamingLayoutVersionResponse],
    )
    async def get_naming_layout_versions(
        _: SessionDependency,
        service: NamingServiceDependency,
    ) -> list[NamingLayoutVersionResponse]:
        return await service.layout_versions()

    @router.post(
        "/naming/source/parse",
        response_model=NamingSourceParseResponse,
    )
    async def parse_naming_source(
        payload: NamingSourceParseRequest,
        _: CsrfDependency,
        service: NamingServiceDependency,
    ) -> NamingSourceParseResponse:
        try:
            return await service.parse_source(payload.format, payload.content)
        except NamingSourceParseError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "code": "invalid_naming_source",
                    "issues": [
                        {
                            "code": issue.code,
                            "message": issue.message,
                            "path": issue.path,
                            "line": issue.line,
                            "column": issue.column,
                        }
                        for issue in error.issues
                    ],
                },
            ) from error

    @router.get(
        "/naming/legacy-migration",
        response_model=LegacyNamingMigrationResponse,
    )
    async def get_legacy_naming_migration(
        _: SessionDependency,
        service: NamingServiceDependency,
    ) -> LegacyNamingMigrationResponse:
        return await service.legacy_migration()

    @router.post(
        "/naming/legacy-migration/apply",
        response_model=LegacyNamingMigrationResultResponse,
    )
    async def apply_legacy_naming_migration(
        payload: LegacyNamingMigrationApplyRequest,
        _: CsrfDependency,
        service: NamingServiceDependency,
    ) -> LegacyNamingMigrationResultResponse:
        try:
            return await service.apply_legacy_migration(
                selected_fields=payload.selected_fields,
                project_revision=payload.project_revision,
                source_revisions=payload.source_revisions,
            )
        except NamingPreviewStaleError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error

    @router.post("/naming/preview", response_model=NamingPreviewResponse)
    async def preview_naming(
        payload: NamingPreviewRequest,
        _: CsrfDependency,
        service: NamingServiceDependency,
    ) -> NamingPreviewResponse:
        try:
            return await service.preview(payload.roots)
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
        "/naming/conversions/{conversion_id}/pause",
        response_model=NamingConversionResponse,
    )
    async def pause_naming_conversion(
        conversion_id: str,
        _: CsrfDependency,
        service: NamingServiceDependency,
    ) -> NamingConversionResponse:
        try:
            return await service.pause(conversion_id)
        except LookupError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversion not found") from error
        except NamingConversionError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

    @router.post(
        "/naming/conversions/{conversion_id}/resume",
        response_model=NamingConversionResponse,
    )
    async def resume_naming_conversion(
        conversion_id: str,
        _: CsrfDependency,
        service: NamingServiceDependency,
    ) -> NamingConversionResponse:
        try:
            return await service.resume(conversion_id)
        except LookupError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversion not found") from error
        except NamingPreviewStaleError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
        except NamingConversionError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

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

    @router.post(
        "/startup-notices/{notice_id}/resolve",
        response_model=StartupNoticeResponse,
    )
    async def resolve_startup_notice(
        notice_id: str,
        payload: StartupNoticeResolveRequest,
        _: CsrfDependency,
        service: NamingServiceDependency,
    ) -> StartupNoticeResponse:
        try:
            return await service.resolve_notice(notice_id, payload.action)
        except LookupError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="notice not found") from error

    return router
