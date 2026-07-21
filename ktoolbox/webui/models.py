from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from ktoolbox.blocker.model import BlockerSpec
from ktoolbox.project_config import ProjectConfiguration


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


class ConfigSchemaResponse(BaseModel):
    locale: Literal["en", "zh-CN"]
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


class BlockerListResponse(BaseModel):
    blockers: list[BlockerSpec]


class SiteVersionResponse(BaseModel):
    version: str
