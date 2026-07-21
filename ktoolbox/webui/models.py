from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


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
