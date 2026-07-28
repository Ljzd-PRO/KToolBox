from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from ktoolbox.project_config import ProjectNamingConfiguration

NamingConversionStatus = Literal[
    "preview",
    "queued",
    "running",
    "pause_requested",
    "paused",
    "rolling_back",
    "completed",
    "failed",
    "cancelled",
]
NamingSection = Literal["structure", "templates"]
StartupNoticeResolution = Literal["ignored", "convert_selected"]


class NamingConfigurationResponse(BaseModel):
    naming: ProjectNamingConfiguration
    revision: str
    conversion_pending: bool = False


class NamingUpdateRequest(BaseModel):
    section: NamingSection
    naming: ProjectNamingConfiguration
    revision: str


class NamingLegacyContextResponse(BaseModel):
    roots: list[Path] = Field(default_factory=list)
    conversion_pending: bool = False


class LegacyNamingSourceResponse(BaseModel):
    name: str
    path: Path
    revision: str
    keys: list[str]


class LegacyNamingFieldResponse(BaseModel):
    path: str
    env_key: str
    legacy_value: Any
    current_value: Any
    sources: list[str]


class LegacyNamingMigrationResponse(BaseModel):
    pending: bool
    project_revision: str
    sources: list[LegacyNamingSourceResponse]
    fields: list[LegacyNamingFieldResponse]
    ignored_environment_keys: list[str]


class LegacyNamingMigrationApplyRequest(BaseModel):
    selected_fields: list[str]
    project_revision: str
    source_revisions: dict[str, str]


class LegacyNamingMigrationResultResponse(BaseModel):
    migrated: bool
    backup_paths: list[Path]
    naming: ProjectNamingConfiguration
    project_revision: str
    ignored_environment_keys: list[str]


class NamingPreviewRequest(BaseModel):
    roots: list[Path]


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
    kind: Literal["naming_migrated", "legacy_layout_conversion"]
    payload: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    acknowledged_at: datetime | None = None
    resolution: StartupNoticeResolution | None = None
    resolved_at: datetime | None = None


class StartupNoticeResolveRequest(BaseModel):
    action: StartupNoticeResolution
