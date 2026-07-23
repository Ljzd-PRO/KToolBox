from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from copy import deepcopy
from typing import Any

import httpx
from fastmcp import FastMCP
from fastmcp.server.auth import AccessToken, TokenVerifier, require_scopes
from fastmcp.server.providers.openapi import MCPType
from fastmcp.utilities.openapi.models import HTTPRoute
from mcp.types import ToolAnnotations

from ktoolbox.webui.mcp_tokens import MCPTokenStore


class DatabaseTokenVerifier(TokenVerifier):
    def __init__(self, store: MCPTokenStore) -> None:
        super().__init__(required_scopes=["mcp:read"])
        self.store = store

    async def verify_token(self, token: str) -> AccessToken | None:
        record = await self.store.verify(token)
        if record is None:
            return None
        return AccessToken(
            token=token,
            client_id=record.id,
            subject=record.username,
            scopes=list(record.scopes),
            expires_at=int(record.expires_at.timestamp()) if record.expires_at else None,
            claims={"name": record.name, "permission": record.permission},
        )


def create_mcp_server(
    app: Any,
    token_store: MCPTokenStore,
    internal_token: str,
) -> FastMCP:
    schema = _mcp_schema(app.openapi())
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://ktoolbox.internal",
        headers={"Authorization": f"Bearer {internal_token}"},
        timeout=30,
    )

    @asynccontextmanager
    async def lifespan(_: FastMCP) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await client.aclose()

    return FastMCP.from_openapi(
        openapi_spec=schema,
        client=client,
        name="KToolBox",
        auth=DatabaseTokenVerifier(token_store),
        lifespan=lifespan,
        route_map_fn=_route_map,
        mcp_component_fn=_configure_component,
        mcp_names=_mcp_names(schema),
        instructions=(
            "Manage the active KToolBox project. Read tools inspect Pawchive and local project state; "
            "write tools change the persistent task queue, creator roster, or ignore rules."
        ),
        mask_error_details=True,
    )


def _mcp_schema(schema: dict[str, Any]) -> dict[str, Any]:
    filtered = deepcopy(schema)
    filtered.get("components", {}).get("securitySchemes", {}).clear()
    for path_item in filtered.get("paths", {}).values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete", "options", "head", "trace"}:
                continue
            operation.pop("security", None)
            operation["parameters"] = [
                parameter
                for parameter in operation.get("parameters", [])
                if parameter.get("name", "").casefold() != "x-csrf-token"
            ]
    return filtered


def _route_map(route: HTTPRoute, _: MCPType) -> MCPType:
    metadata = route.extensions.get("x-ktoolbox-mcp", {})
    return MCPType.TOOL if metadata.get("enabled") is True else MCPType.EXCLUDE


def _configure_component(route: HTTPRoute, component: Any) -> None:
    metadata = route.extensions["x-ktoolbox-mcp"]
    scope = str(metadata["scope"])
    safety = str(metadata["safety"])
    component.auth = require_scopes(scope)
    component.tags = {str(route.tags[0]), scope, safety}
    component.annotations = ToolAnnotations(
        title=route.summary,
        readOnlyHint=safety == "read",
        destructiveHint=safety == "destructive",
        idempotentHint=route.method in {"GET", "PUT", "DELETE"},
        openWorldHint=bool(metadata.get("openWorld")),
    )


def _mcp_names(schema: dict[str, Any]) -> dict[str, str]:
    names: dict[str, str] = {}
    for path_item in schema.get("paths", {}).values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete", "options", "head", "trace"}:
                continue
            metadata = operation.get("x-ktoolbox-mcp", {})
            if metadata.get("enabled"):
                names[operation["operationId"]] = metadata["name"]
    return names
