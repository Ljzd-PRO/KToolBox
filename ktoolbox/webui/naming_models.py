from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, model_validator

from ktoolbox.naming_sources import NamingSourceFormat
from ktoolbox.project_config import ProjectNamingConfiguration
from ktoolbox.publication_time import PublishedTimePolicy

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
NamingLayoutVersionOrigin = Literal[
    "project_current",
    "project_change",
    "legacy_migration",
    "recovered",
    "legacy_raw",
]


class PublishedTimePolicySnapshot(BaseModel):
    mode: Literal["normalized", "legacy_raw", "kemono_utc"] = "normalized"
    target_timezone: str = "UTC"
    fallback_service_timezone: str = "UTC"
    service_timezones: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy(self) -> PublishedTimePolicySnapshot:
        if self.mode != "normalized":
            return self
        policy = PublishedTimePolicy.from_values(
            target_timezone=self.target_timezone,
            fallback_service_timezone=self.fallback_service_timezone,
            service_timezones=self.service_timezones,
        )
        self.target_timezone = policy.target_timezone
        self.fallback_service_timezone = policy.fallback_service_timezone
        self.service_timezones = dict(policy.service_timezones)
        return self


class NamingConfigurationResponse(BaseModel):
    default_output: Path
    resolved_default_output: Path
    naming: ProjectNamingConfiguration
    published_time: PublishedTimePolicySnapshot
    revision: str
    conversion_pending: bool = False


class NamingUpdateRequest(BaseModel):
    section: NamingSection
    naming: ProjectNamingConfiguration
    revision: str
    default_output: Path | None = None


class NamingLegacyContextResponse(BaseModel):
    roots: list[Path] = Field(default_factory=list)
    conversion_pending: bool = False


class NamingLayoutVersionResponse(BaseModel):
    id: str
    revision: str
    naming: ProjectNamingConfiguration
    published_time: PublishedTimePolicySnapshot
    origin: NamingLayoutVersionOrigin
    created_at: datetime
    is_current: bool = False


class NamingSourceParseRequest(BaseModel):
    format: NamingSourceFormat
    content: str


class NamingSourceWarningResponse(BaseModel):
    code: str
    count: int


class NamingSourceDifferenceResponse(BaseModel):
    path: str
    source_value: Any
    target_value: Any


class NamingSourceParseResponse(BaseModel):
    format: NamingSourceFormat
    naming: ProjectNamingConfiguration
    digest: str
    recognized_fields: list[str]
    defaulted_fields: list[str]
    warnings: list[NamingSourceWarningResponse]
    differences: list[NamingSourceDifferenceResponse]
    default_published_time_mode: Literal["kemono_utc", "pawchive_raw"]


class ProjectLayoutConversionSource(BaseModel):
    kind: Literal["project_layout"] = "project_layout"
    version_ids: list[str] = Field(min_length=1)


class PastedConfigConversionSource(BaseModel):
    kind: Literal["pasted_config"] = "pasted_config"
    format: NamingSourceFormat
    naming: ProjectNamingConfiguration
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    published_time_mode: Literal["kemono_utc", "pawchive_raw", "custom"] | None = None
    published_time: PublishedTimePolicySnapshot | None = None


NamingConversionSource = Annotated[
    ProjectLayoutConversionSource | PastedConfigConversionSource,
    Field(discriminator="kind"),
]


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
    source: NamingConversionSource


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
    target_layout_revision: str = ""
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
    source: NamingConversionSource | None = None
    resolves_pending_layout: bool = False


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
