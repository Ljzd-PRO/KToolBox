from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from ktoolbox.project_config import ProjectNamingConfiguration

NamingConversionStatus = Literal[
    "preview",
    "queued",
    "running",
    "rolling_back",
    "completed",
    "failed",
    "cancelled",
]


class NamingConfigurationResponse(BaseModel):
    naming: ProjectNamingConfiguration
    revision: str
    suggested_download_roots: list[Path] = Field(default_factory=list)


class NamingPreviewRequest(BaseModel):
    naming: ProjectNamingConfiguration


class NamingCreatorPreview(BaseModel):
    key: str
    name: str
    source: Path
    target: Path
    works: int = 0
    files: int = 0
    bytes: int = 0
    operations: int = 0
    skipped: int = 0
    conflicts: list[str] = Field(default_factory=list)
    selectable: bool = True


class NamingPreviewResponse(BaseModel):
    id: str
    revision: str
    fingerprint: str
    roots: list[Path]
    creators: list[NamingCreatorPreview]
    creator_count: int
    work_count: int
    file_count: int
    total_bytes: int
    skipped_count: int
    conflict_count: int
    created_at: datetime


class NamingApplyRequest(BaseModel):
    preview_id: str
    selected_creators: list[str]
    convert_existing: bool = True


class NamingConversionProgress(BaseModel):
    completed_operations: int = 0
    total_operations: int = 0
    current_creator: str | None = None


class NamingConversionResponse(BaseModel):
    id: str
    status: NamingConversionStatus
    preview: NamingPreviewResponse
    selected_creators: list[str]
    progress: NamingConversionProgress = Field(default_factory=NamingConversionProgress)
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class StartupNoticeResponse(BaseModel):
    id: str
    kind: Literal["naming_migrated"] = "naming_migrated"
    payload: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    acknowledged_at: datetime | None = None
