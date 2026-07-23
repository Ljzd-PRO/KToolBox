from __future__ import annotations

import json
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from ktoolbox.api.generated import Post, Revision
from ktoolbox.configuration import RuntimeContext
from ktoolbox.webui.auth import AuthService, client_identifier, require_csrf, require_session
from ktoolbox.webui.config_monitor import ConfigurationChangeMonitor
from ktoolbox.webui.config_schema import Locale, build_config_schema
from ktoolbox.webui.config_store import ConfigurationFileError, DotenvFileStore
from ktoolbox.webui.database import WebUISession
from ktoolbox.webui.filesystem import FilesystemBrowser, FilesystemBrowserError, FilesystemMode
from ktoolbox.webui.mcp_tokens import MCPTokenRecord, MCPTokenStore
from ktoolbox.webui.models import (
    ConfigSchemaResponse,
    FilesystemBrowseResponse,
    MCPConfigurationPatchRequest,
    MCPStatusResponse,
    MCPTokenCreatedResponse,
    MCPTokenCreateRequest,
    MCPTokenResponse,
    MCPToolResponse,
)
from ktoolbox.webui.openapi_contract import dump_openapi_yaml, mcp_tool_catalog
from ktoolbox.webui.pawchive_routes import fetch_post
from ktoolbox.webui.task_models import TaskCleanupPreview
from ktoolbox.webui.task_store import InvalidTaskStateError, TaskNotFoundError, TaskStore

SessionDependency = Annotated[WebUISession, Depends(require_session)]
CsrfDependency = Annotated[WebUISession, Depends(require_csrf)]


def create_mcp_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["mcp"])

    @router.get("/openapi.yaml", response_class=Response)
    async def download_openapi(request: Request, _: SessionDependency) -> Response:
        return Response(
            dump_openapi_yaml(request.app.openapi()),
            media_type="application/yaml",
            headers={"Content-Disposition": 'attachment; filename="ktoolbox-webui-openapi.yaml"'},
        )

    @router.get("/mcp/status", response_model=MCPStatusResponse)
    async def mcp_status(_: SessionDependency) -> MCPStatusResponse:
        return MCPStatusResponse(tool_count=len(mcp_tool_catalog()))

    @router.get("/mcp/tools", response_model=list[MCPToolResponse])
    async def list_mcp_tools(_: SessionDependency) -> list[MCPToolResponse]:
        return [MCPToolResponse.model_validate(tool) for tool in mcp_tool_catalog()]

    @router.get("/mcp/tokens", response_model=list[MCPTokenResponse])
    async def list_mcp_tokens(request: Request, session: SessionDependency) -> list[MCPTokenResponse]:
        records = await _token_store(request).list(session.username)
        return [_token_response(record) for record in records]

    @router.post("/mcp/tokens", response_model=MCPTokenCreatedResponse, status_code=status.HTTP_201_CREATED)
    async def create_mcp_token(
        payload: MCPTokenCreateRequest,
        request: Request,
        session: CsrfDependency,
    ) -> MCPTokenCreatedResponse:
        _auth(request).confirm_password(payload.password, client_identifier(request))
        created = await _token_store(request).create(
            name=payload.name.strip(),
            username=session.username,
            permission=payload.permission,
            expires_in_days=payload.expires_in_days,
        )
        return MCPTokenCreatedResponse(token=created.token, **_token_response(created.record).model_dump())

    @router.post("/mcp/tokens/{token_id}/revoke", response_model=MCPTokenResponse)
    async def revoke_mcp_token(
        token_id: str,
        request: Request,
        session: CsrfDependency,
    ) -> MCPTokenResponse:
        record = await _token_store(request).revoke(token_id, session.username)
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "MCP token not found")
        return _token_response(record)

    @router.get("/mcp/files", response_model=FilesystemBrowseResponse)
    async def browse_project_files(
        request: Request,
        _: SessionDependency,
        mode: FilesystemMode = "directory",
        path: str | None = None,
        search: str = Query(default="", max_length=256),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=200),
    ) -> FilesystemBrowseResponse:
        try:
            return await _filesystem(request).browse(
                scope="project",
                mode=mode,
                path=path,
                search=search,
                include_hidden=False,
                offset=offset,
                limit=limit,
            )
        except FilesystemBrowserError as error:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error

    @router.patch("/mcp/config/{name}", response_model=ConfigSchemaResponse)
    async def patch_mcp_configuration(
        name: Literal["dotenv", "production"],
        payload: MCPConfigurationPatchRequest,
        request: Request,
        _: CsrfDependency,
        locale: Locale = "en",
    ) -> ConfigSchemaResponse:
        context = _runtime(request)
        schema = build_config_schema(context.configuration, context.project_root, locale)
        fields = {field.path: field for field in schema.fields}
        updates: dict[str, str | None] = {}
        for path, value in payload.values.items():
            field = fields.get(path)
            if field is None:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"unknown configuration field: {path}")
            if field.secret:
                raise HTTPException(status.HTTP_403_FORBIDDEN, f"MCP cannot edit secret field: {path}")
            if field.source == "environment":
                raise HTTPException(status.HTTP_409_CONFLICT, f"process environment overrides field: {path}")
            updates[field.env_name] = _dotenv_value(value)

        store = DotenvFileStore(context.project_root)
        document = store.read(name)
        try:
            updated_context = store.patch(name, updates, document.revision)
        except ConfigurationFileError as error:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
        request.app.state.runtime_context = updated_context
        document = store.read(name)
        await _config_monitor(request).publish_change(name, document.revision, source="mcp")
        return build_config_schema(updated_context.configuration, context.project_root, locale)

    @router.delete("/mcp/tasks/{task_id}", response_model=TaskCleanupPreview)
    async def delete_task_record(
        task_id: str,
        request: Request,
        _: CsrfDependency,
    ) -> TaskCleanupPreview:
        try:
            return await _task_store(request).delete(task_id, delete_output=False)
        except TaskNotFoundError as error:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found") from error
        except InvalidTaskStateError as error:
            raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error

    @router.get("/mcp/pawchive/posts/{service}/{creator_id}/{post_id}", response_model=Post | Revision)
    async def get_mcp_work(
        service: str,
        creator_id: str,
        post_id: str,
        request: Request,
        _: SessionDependency,
        revision_id: str | None = None,
        include_content: bool = False,
        content_limit: int = Query(default=12_000, ge=1, le=20_000),
    ) -> Post | Revision:
        post = await fetch_post(_runtime(request).snapshot(), service, creator_id, post_id, revision_id)
        content = post.content
        if not include_content:
            content = None
        elif content is not None:
            content = content[:content_limit]
        return post.model_copy(update={"content": content, "substring": None})

    return router


def _auth(request: Request) -> AuthService:
    return cast(AuthService, request.app.state.auth)


def _token_store(request: Request) -> MCPTokenStore:
    return cast(MCPTokenStore, request.app.state.mcp_token_store)


def _filesystem(request: Request) -> FilesystemBrowser:
    return cast(FilesystemBrowser, request.app.state.filesystem_browser)


def _runtime(request: Request) -> RuntimeContext:
    return cast(RuntimeContext, request.app.state.runtime_context)


def _task_store(request: Request) -> TaskStore:
    return cast(TaskStore, request.app.state.task_store)


def _config_monitor(request: Request) -> ConfigurationChangeMonitor:
    return cast(ConfigurationChangeMonitor, request.app.state.config_monitor)


def _token_response(record: MCPTokenRecord) -> MCPTokenResponse:
    return MCPTokenResponse(
        id=record.id,
        name=record.name,
        username=record.username,
        permission=record.permission,
        scopes=list(record.scopes),
        created_at=record.created_at,
        expires_at=record.expires_at,
        last_used_at=record.last_used_at,
        revoked_at=record.revoked_at,
        active=record.active,
    )


def _dotenv_value(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    return str(value)
