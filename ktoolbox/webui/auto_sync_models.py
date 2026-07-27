from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from ktoolbox.project_config import AutomaticSyncPlan


class AutomaticSyncRunTrigger(str, Enum):
    scheduled = "scheduled"
    immediate = "immediate"


class AutomaticSyncRunStatus(str, Enum):
    queued = "queued"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"
    interrupted = "interrupted"


ACTIVE_AUTOMATIC_RUN_STATUSES = {
    AutomaticSyncRunStatus.queued,
    AutomaticSyncRunStatus.running,
    AutomaticSyncRunStatus.paused,
}


class AutomaticSyncRunRecord(BaseModel):
    id: str
    plan_id: str
    plan_name: str
    trigger: AutomaticSyncRunTrigger
    status: AutomaticSyncRunStatus
    task_id: str | None = None
    scheduled_for: datetime | None = None
    cutoff_at: datetime
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None


class AutomaticSyncUpdateSummary(BaseModel):
    service: str
    creator_id: str
    creator_name: str | None = None
    new_posts: int = Field(ge=0)
    last_discovered_at: datetime


class AutomaticSyncPlanListResponse(BaseModel):
    plans: list[AutomaticSyncPlan]
    revision: str
    next_runs: dict[str, datetime | None]


class AutomaticSyncRunNowResponse(BaseModel):
    task_id: str


AutomaticSyncUpdateRange = Literal["today", "1d", "7d", "14d", "30d"]
