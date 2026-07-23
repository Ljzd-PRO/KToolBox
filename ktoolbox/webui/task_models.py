from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator, model_validator

from ktoolbox.failures import TaskFailureReport
from ktoolbox.project_config import CreatorReference
from ktoolbox.utils import parse_webpage_url


class TaskStatus(str, Enum):
    queued = "queued"
    blocked = "blocked"
    running = "running"
    pause_requested = "pause_requested"
    paused = "paused"
    stop_requested = "stop_requested"
    stopped = "stopped"
    completed = "completed"
    failed = "failed"
    interrupted = "interrupted"


ACTIVE_TASK_STATUSES = {
    TaskStatus.queued,
    TaskStatus.blocked,
    TaskStatus.running,
    TaskStatus.pause_requested,
    TaskStatus.stop_requested,
}
RUNNING_TASK_STATUSES = {
    TaskStatus.running,
    TaskStatus.pause_requested,
    TaskStatus.stop_requested,
}
TERMINAL_TASK_STATUSES = {
    TaskStatus.paused,
    TaskStatus.stopped,
    TaskStatus.completed,
    TaskStatus.failed,
    TaskStatus.interrupted,
}


class DownloadTaskSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["download"] = "download"
    post: str | None = None
    service: str | None = None
    creator_id: str | None = None
    post_id: str | None = None
    revision_id: str | None = None
    output: Path = Path(".")
    dump_post_data: bool = True

    @model_validator(mode="after")
    def validate_identity(self) -> DownloadTaskSpec:
        if self.post:
            return self
        if not all((self.service, self.creator_id, self.post_id)):
            raise ValueError("provide a post URL or service, creator_id, and post_id")
        return self


class SyncTaskSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["sync"] = "sync"
    creators: list[CreatorReference] = Field(default_factory=list)
    output: Path = Path(".")
    save_creator_indices: bool = False
    mix_posts: bool | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    offset: int = Field(default=0, ge=0)
    length: int | None = Field(default=None, ge=1)
    keywords: set[str] = Field(default_factory=set)
    keywords_exclude: set[str] = Field(default_factory=set)

    @model_validator(mode="after")
    def validate_dates(self) -> SyncTaskSpec:
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValueError("start_time must not be later than end_time")
        return self


TaskSpec = Annotated[DownloadTaskSpec | SyncTaskSpec, Field(discriminator="kind")]
TASK_SPEC_ADAPTER: TypeAdapter[TaskSpec] = TypeAdapter(TaskSpec)


class TaskPresentationSnapshot(BaseModel):
    """Non-executable labels captured when a task is created from Pawchive data."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    target_key: Annotated[str, Field(min_length=1, max_length=1024)]
    title: Annotated[str, Field(max_length=500)] | None = None
    creator_name: Annotated[str, Field(max_length=200)] | None = None

    @field_validator("title", "creator_name", mode="before")
    @classmethod
    def empty_label_to_none(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value


def task_target_key(spec: TaskSpec) -> str | None:
    """Return a canonical key for display metadata without changing task identity."""

    if not isinstance(spec, DownloadTaskSpec):
        return None
    if spec.post:
        service, creator_id, post_id, parsed_revision = parse_webpage_url(spec.post)
        revision_id = parsed_revision or spec.revision_id
    else:
        service, creator_id, post_id, revision_id = (
            spec.service,
            spec.creator_id,
            spec.post_id,
            spec.revision_id,
        )
    if not service or not creator_id or not post_id:
        return None
    values = (service.casefold(), creator_id, post_id, revision_id or "")
    return "download/" + "/".join(quote(value, safe="") for value in values)


def validate_task_presentation(
    spec: TaskSpec,
    presentation: TaskPresentationSnapshot | None,
) -> TaskPresentationSnapshot | None:
    if presentation is None:
        return None
    expected = task_target_key(spec)
    if expected is None:
        raise ValueError("presentation snapshots are only supported for download tasks")
    if presentation.target_key != expected:
        raise ValueError("presentation target_key does not match the task target")
    return presentation


class TaskCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec: TaskSpec
    presentation: TaskPresentationSnapshot | None = None


class ActiveDownload(BaseModel):
    creator_key: str
    filename: str
    total: int | None = None
    completed: int = 0
    speed_bps: float = 0


class WaitingRetry(BaseModel):
    creator_key: str
    filename: str
    retry_count: int = Field(ge=0)
    status_code: int | None = Field(default=None, ge=100, le=599)


class TaskProgress(BaseModel):
    queued_files: int = 0
    processed_files: int = 0
    completed_files: int = 0
    existing_files: int = 0
    failed_files: int = 0
    transferred_bytes: int = 0
    total_bytes: int | None = None
    speed_bps: float = 0
    eta_seconds: float | None = None
    active_creators: list[str] = Field(default_factory=list)
    active_downloads: dict[str, ActiveDownload] = Field(default_factory=dict)
    waiting_retries: dict[str, WaitingRetry] = Field(default_factory=dict)


class TaskRecord(BaseModel):
    id: str
    kind: Literal["download", "sync"]
    status: TaskStatus
    spec: TaskSpec
    presentation: TaskPresentationSnapshot | None = None
    position: int
    revision: int
    progress: TaskProgress = Field(default_factory=TaskProgress)
    error: str | None = None
    failure: TaskFailureReport | None = None
    blocked_by: str | None = None
    created_at: datetime
    updated_at: datetime


class TaskAttempt(BaseModel):
    id: int
    task_id: str
    sequence: int
    status: TaskStatus
    spec: TaskSpec
    configuration: dict[str, object]
    started_at: datetime
    finished_at: datetime | None = None
    error: str | None = None
    failure: TaskFailureReport | None = None


class TaskEvent(BaseModel):
    id: int
    task_id: str | None = None
    event_type: str
    resource: str | None = None
    resource_id: str | None = None
    data: dict[str, object]
    created_at: datetime


class TaskArtifact(BaseModel):
    path: Path
    size: int
    mtime_ns: int
    removable: bool
    reason: str | None = None


class TaskCleanupPreview(BaseModel):
    task_id: str
    artifacts: list[TaskArtifact]
    removable_files: int
    removable_bytes: int


class TaskUpdateRequest(BaseModel):
    spec: TaskSpec
    presentation: TaskPresentationSnapshot | None = None


class TaskDeleteRequest(BaseModel):
    delete_output: bool = False
    confirmation: str | None = None
