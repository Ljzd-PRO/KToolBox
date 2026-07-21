from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status

from ktoolbox.blocker.model import BlockerSpec
from ktoolbox.configuration import RuntimeContext
from ktoolbox.project_config import CreatorReference, ProjectConfigError, ProjectConfigStore, ProjectConfiguration
from ktoolbox.webui.auth import require_csrf, require_session
from ktoolbox.webui.config_schema import Locale, build_config_schema
from ktoolbox.webui.config_store import (
    ConfigurationConflictError,
    ConfigurationDocument,
    ConfigurationFileError,
    DotenvFileStore,
    content_revision,
)
from ktoolbox.webui.database import WebUISession
from ktoolbox.webui.models import (
    BlockerListResponse,
    ConfigSchemaResponse,
    CreatorUpdateRequest,
    DotenvPatchRequest,
    ProjectDocumentResponse,
    TextDocumentResponse,
    TextDocumentUpdate,
)

SessionDependency = Annotated[WebUISession, Depends(require_session)]
CsrfDependency = Annotated[WebUISession, Depends(require_csrf)]
IfMatch = Annotated[str | None, Header(alias="If-Match")]


def create_project_router(project_root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    dotenv_store = DotenvFileStore(project_root)
    project_store = ProjectConfigStore(project_root / "ktoolbox.toml")

    def require_revision(value: str | None) -> str:
        if value is None:
            raise HTTPException(status_code=status.HTTP_428_PRECONDITION_REQUIRED, detail="If-Match is required")
        return value

    def current_context(request: Request) -> RuntimeContext:
        return cast(RuntimeContext, request.app.state.runtime_context)

    def reload_context(request: Request, context: RuntimeContext) -> None:
        request.app.state.runtime_context = context

    @router.get("/config/schema", response_model=ConfigSchemaResponse)
    async def config_schema(
        request: Request,
        _: SessionDependency,
        locale: Locale = "en",
    ) -> ConfigSchemaResponse:
        return build_config_schema(current_context(request).configuration, project_root, locale)

    @router.get("/config/dotenv/{name}", response_model=TextDocumentResponse)
    async def get_dotenv(
        name: Literal["dotenv", "production"],
        response: Response,
        _: SessionDependency,
    ) -> TextDocumentResponse:
        document = dotenv_store.read(name)
        response.headers["ETag"] = f'"{document.revision}"'
        return _document_response(document)

    @router.put("/config/dotenv/{name}", response_model=TextDocumentResponse)
    async def replace_dotenv(
        name: Literal["dotenv", "production"],
        payload: TextDocumentUpdate,
        request: Request,
        response: Response,
        _: CsrfDependency,
        if_match: IfMatch = None,
    ) -> TextDocumentResponse:
        try:
            context = dotenv_store.replace(name, payload.content, require_revision(if_match))
        except ConfigurationConflictError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
        except ConfigurationFileError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
        reload_context(request, context)
        document = dotenv_store.read(name)
        response.headers["ETag"] = f'"{document.revision}"'
        return _document_response(document)

    @router.patch("/config/dotenv/{name}", response_model=TextDocumentResponse)
    async def patch_dotenv(
        name: Literal["dotenv", "production"],
        payload: DotenvPatchRequest,
        request: Request,
        response: Response,
        _: CsrfDependency,
        if_match: IfMatch = None,
    ) -> TextDocumentResponse:
        try:
            context = dotenv_store.patch(name, payload.values, require_revision(if_match))
        except ConfigurationConflictError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
        except ConfigurationFileError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
        reload_context(request, context)
        document = dotenv_store.read(name)
        response.headers["ETag"] = f'"{document.revision}"'
        return _document_response(document)

    @router.get("/config/project", response_model=ProjectDocumentResponse)
    async def get_project_config(response: Response, _: SessionDependency) -> ProjectDocumentResponse:
        content = project_store.load_text()
        revision = content_revision(content)
        response.headers["ETag"] = f'"{revision}"'
        return ProjectDocumentResponse(
            path=project_store.path,
            content=content,
            revision=revision,
            configuration=project_store.load(),
        )

    @router.put("/config/project", response_model=ProjectDocumentResponse)
    async def replace_project_config(
        payload: TextDocumentUpdate,
        response: Response,
        _: CsrfDependency,
        if_match: IfMatch = None,
    ) -> ProjectDocumentResponse:
        current = project_store.load_text()
        if content_revision(current) != require_revision(if_match).strip().strip('"'):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="ktoolbox.toml changed since it was loaded"
            )
        try:
            configuration = project_store.replace_text(payload.content)
        except ProjectConfigError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
        content = project_store.load_text()
        revision = content_revision(content)
        response.headers["ETag"] = f'"{revision}"'
        return ProjectDocumentResponse(
            path=project_store.path,
            content=content,
            revision=revision,
            configuration=configuration,
        )

    @router.get("/creators", response_model=list[CreatorReference])
    async def list_creators(_: SessionDependency) -> list[CreatorReference]:
        return project_store.load().creators

    @router.post("/creators", response_model=CreatorReference, status_code=status.HTTP_201_CREATED)
    async def add_creator(creator: CreatorReference, _: CsrfDependency) -> CreatorReference:
        try:
            project_store.add_creator(creator)
        except ProjectConfigError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
        return creator

    @router.put("/creators/{service}/{creator_id}", response_model=CreatorReference)
    async def update_creator(
        service: str,
        creator_id: str,
        payload: CreatorUpdateRequest,
        _: CsrfDependency,
    ) -> CreatorReference:
        configuration = project_store.load()
        creator = configuration.find_creator(f"{service}:{creator_id}")
        if creator is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="creator not found")
        creator.alias = payload.alias
        creator.enabled = payload.enabled
        try:
            project_store.save(ProjectConfiguration.model_validate(configuration.model_dump()))
        except (ProjectConfigError, ValueError) as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
        return creator

    @router.delete("/creators/{service}/{creator_id}", response_model=CreatorReference)
    async def delete_creator(service: str, creator_id: str, _: CsrfDependency) -> CreatorReference:
        try:
            return project_store.remove_creator(f"{service}:{creator_id}")
        except ProjectConfigError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    @router.get("/blockers", response_model=BlockerListResponse)
    async def list_blockers(_: SessionDependency) -> BlockerListResponse:
        return BlockerListResponse(blockers=project_store.load().blockers)

    @router.put("/blockers", response_model=BlockerListResponse)
    async def replace_blockers(blockers: list[BlockerSpec], _: CsrfDependency) -> BlockerListResponse:
        configuration = project_store.load()
        configuration.blockers = blockers
        try:
            configuration = ProjectConfiguration.model_validate(configuration.model_dump())
            project_store.save(configuration)
        except (ProjectConfigError, ValueError) as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
        return BlockerListResponse(blockers=configuration.blockers)

    return router


def _document_response(document: ConfigurationDocument) -> TextDocumentResponse:
    return TextDocumentResponse(
        name=document.name,
        path=document.path,
        content=document.content,
        revision=document.revision,
    )
