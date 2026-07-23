from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from ktoolbox.blocker.model import BlockerSpec
from ktoolbox.project_config import CreatorReference, ProjectConfiguration


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=256)
    password: str = Field(min_length=1, max_length=4096)


class SessionResponse(BaseModel):
    authenticated: bool = True
    username: str
    csrf_token: str
    created_at: datetime


class ProjectSummaryResponse(BaseModel):
    name: str
    root: Path
    project_config: Path
    dotenv_files: list[Path]
    version: str


class HealthResponse(BaseModel):
    status: str = "ok"


class PathSelectorResponse(BaseModel):
    kind: Literal["directory", "file"]
    scope: Literal["project", "host"]
    value_mode: Literal["absolute", "project_relative"]


class ConfigFieldResponse(BaseModel):
    path: str
    env_name: str
    section: str
    label: str
    description: str
    json_schema: dict[str, Any]
    default: Any = None
    value: Any = None
    is_set: bool
    secret: bool
    source: Literal["default", ".env", "prod.env", "environment"] | str
    apply_mode: Literal["next_task", "restart"]
    path_selector: PathSelectorResponse | None = None


class FilesystemBreadcrumbResponse(BaseModel):
    label: str
    path: str


class FilesystemLocationResponse(BaseModel):
    id: str
    label: str
    path: str


class FilesystemEntryResponse(BaseModel):
    name: str
    path: str
    project_relative_path: str | None = None
    kind: Literal["directory", "file", "other"]
    is_symlink: bool
    navigable: bool
    deletable: bool


class FilesystemBrowseResponse(BaseModel):
    scope: Literal["project", "host"]
    mode: Literal["directory", "file"]
    path: str
    project_relative_path: str | None = None
    parent: str | None = None
    separator: str
    breadcrumbs: list[FilesystemBreadcrumbResponse]
    locations: list[FilesystemLocationResponse]
    entries: list[FilesystemEntryResponse]
    suggested_name: str | None = None
    offset: int
    limit: int
    has_more: bool


class FilesystemCreateDirectoryRequest(BaseModel):
    scope: Literal["project", "host"]
    parent: str
    name: str = Field(min_length=1, max_length=255)


class FilesystemDeleteDirectoryRequest(BaseModel):
    scope: Literal["project", "host"]
    path: str = Field(min_length=1, max_length=4096)


class ConfigSchemaResponse(BaseModel):
    locale: Literal["zh-CN", "zh-Hant", "en", "ja", "ko", "fr", "ru"]
    sections: dict[str, str]
    fields: list[ConfigFieldResponse]


class TextDocumentResponse(BaseModel):
    name: str
    path: Path
    content: str
    revision: str


class TextDocumentUpdate(BaseModel):
    content: str


class ValidationResponse(BaseModel):
    valid: bool = True


class DotenvPatchRequest(BaseModel):
    values: dict[str, str | None]


class ProjectDocumentResponse(BaseModel):
    path: Path
    content: str
    revision: str
    configuration: ProjectConfiguration


class CreatorUpdateRequest(BaseModel):
    alias: str | None = None
    enabled: bool = True


class CreatorRosterItemResponse(CreatorReference):
    name: str | None = None


class BlockerListResponse(BaseModel):
    blockers: list[BlockerSpec]


class SiteVersionResponse(BaseModel):
    version: str


class MCPTokenCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=4096)
    permission: Literal["read", "manage"]
    expires_in_days: Literal[7, 30, 90, 365] | None = None


class MCPTokenResponse(BaseModel):
    id: str
    name: str
    username: str
    permission: Literal["read", "manage"]
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None
    revoked_at: datetime | None
    active: bool


class MCPTokenCreatedResponse(MCPTokenResponse):
    token: str


class MCPStatusResponse(BaseModel):
    running: bool = True
    endpoint_path: str = "/mcp"
    openapi_path: str = "/api/v1/openapi.yaml"
    transport: Literal["streamable-http"] = "streamable-http"
    tool_count: int


class MCPToolResponse(BaseModel):
    name: str
    operation_id: str
    description: str
    category: str
    scope: Literal["mcp:read", "mcp:write"]
    safety: Literal["read", "write", "destructive"]
    open_world: bool


MCPConfigValue = str | int | float | bool | list[str] | None


class MCPConfigurationPatchRequest(BaseModel):
    values: dict[str, MCPConfigValue] = Field(min_length=1)
