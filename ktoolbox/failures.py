from __future__ import annotations

import errno
from enum import Enum

import httpx
from pydantic import BaseModel, ConfigDict, Field

from ktoolbox.api.errors import (
    PawchiveAuthenticationError,
    PawchiveHTTPError,
    PawchiveResponseValidationError,
    PawchiveTransportError,
)


class FailureCode(str, Enum):
    network = "network"
    timeout = "timeout"
    rate_limited = "rate_limited"
    http_error = "http_error"
    response_incompatible = "response_incompatible"
    permission_denied = "permission_denied"
    disk_full = "disk_full"
    download_failed = "download_failed"
    resource_not_found = "resource_not_found"
    unknown = "unknown"


class FailureStage(str, Enum):
    creator_profile = "creator_profile"
    work_list = "work_list"
    work_detail = "work_detail"
    revisions = "revisions"
    job_generation = "job_generation"
    file_request = "file_request"
    file_write = "file_write"
    index_write = "index_write"


class FailureItem(BaseModel):
    """A bounded, value-free diagnostic suitable for persistence and display."""

    model_config = ConfigDict(extra="forbid")

    code: FailureCode
    stage: FailureStage
    message: str = Field(max_length=500)
    retryable: bool
    platform: str | None = Field(default=None, max_length=100)
    creator_id: str | None = Field(default=None, max_length=200)
    file_name: str | None = Field(default=None, max_length=500)
    http_status: int | None = Field(default=None, ge=100, le=599)
    operation: str | None = Field(default=None, max_length=100)
    fields: list[str] = Field(default_factory=list, max_length=20)


class TaskFailureReport(BaseModel):
    """Persisted task failure details with bounded diagnostic entries."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(max_length=500)
    creator_failures: int = Field(default=0, ge=0)
    file_failures: int = Field(default=0, ge=0)
    items: list[FailureItem] = Field(default_factory=list, max_length=100)


class TaskExecutionError(RuntimeError):
    def __init__(self, report: TaskFailureReport) -> None:
        self.report = report
        super().__init__(report.summary)


class StagedFailure(RuntimeError):
    def __init__(self, stage: FailureStage, cause: Exception) -> None:
        self.stage = stage
        self.cause = cause
        super().__init__(f"{stage.value} failed")


_OPERATION_STAGES = {
    "get_creator_profile": FailureStage.creator_profile,
    "list_creator_posts": FailureStage.work_list,
    "get_post": FailureStage.work_detail,
    "list_post_revisions": FailureStage.revisions,
}


def classify_failure(
    error: Exception,
    *,
    stage: FailureStage,
    platform: str | None = None,
    creator_id: str | None = None,
    file_name: str | None = None,
) -> FailureItem:
    if isinstance(error, StagedFailure):
        return classify_failure(
            error.cause,
            stage=error.stage,
            platform=platform,
            creator_id=creator_id,
            file_name=file_name,
        )

    operation: str | None = None
    fields: list[str] = []
    http_status: int | None = None

    if isinstance(error, PawchiveResponseValidationError):
        operation = error.operation
        stage = _OPERATION_STAGES.get(operation, stage)
        fields = [issue.path for issue in error.issues[:20]]
        code = FailureCode.response_incompatible
        message = "Pawchive returned data in an unsupported format"
        retryable = False
    elif isinstance(error, PawchiveTransportError):
        code = FailureCode.timeout if isinstance(error.cause, httpx.TimeoutException) else FailureCode.network
        message = "The Pawchive request timed out" if code is FailureCode.timeout else "Could not connect to Pawchive"
        retryable = True
    elif isinstance(error, PawchiveHTTPError):
        http_status = error.status_code
        if isinstance(error, PawchiveAuthenticationError):
            code = FailureCode.permission_denied
            message = "Pawchive rejected the request"
            retryable = False
        elif http_status == 404:
            code = FailureCode.resource_not_found
            message = "The requested Pawchive resource was not found"
            retryable = False
        elif http_status == 429:
            code = FailureCode.rate_limited
            message = "Pawchive rate-limited the request"
            retryable = True
        else:
            code = FailureCode.http_error
            message = f"Pawchive returned HTTP {http_status}"
            retryable = http_status >= 500
    elif isinstance(error, httpx.TimeoutException):
        code = FailureCode.timeout
        message = "The file request timed out" if stage is FailureStage.file_request else "The request timed out"
        retryable = True
    elif isinstance(error, httpx.TransportError):
        code = FailureCode.network
        message = (
            "The file server could not be reached"
            if stage is FailureStage.file_request
            else "The network request failed"
        )
        retryable = True
    elif isinstance(error, PermissionError) or (
        isinstance(error, OSError) and error.errno in {errno.EACCES, errno.EPERM, errno.EROFS}
    ):
        code = FailureCode.permission_denied
        message = "KToolBox does not have permission to write the output"
        retryable = False
    elif isinstance(error, OSError) and error.errno in {errno.ENOSPC, errno.EDQUOT}:
        code = FailureCode.disk_full
        message = "There is not enough free disk space"
        retryable = False
    elif isinstance(error, LookupError):
        code = FailureCode.resource_not_found
        message = (
            "The requested revision was not found"
            if stage is FailureStage.revisions
            else "The requested resource was not found"
        )
        retryable = False
    else:
        code = FailureCode.unknown
        message = f"Unexpected {error.__class__.__name__} during {stage.value.replace('_', ' ')}"
        retryable = False

    return FailureItem(
        code=code,
        stage=stage,
        message=message,
        retryable=retryable,
        platform=platform,
        creator_id=creator_id,
        file_name=file_name,
        http_status=http_status,
        operation=operation,
        fields=fields,
    )


def failure_from_http_status(
    status: int,
    *,
    stage: FailureStage,
    file_name: str | None = None,
) -> FailureItem:
    if status == 429:
        code = FailureCode.rate_limited
        message = "The file server rate-limited the request"
        retryable = True
    else:
        code = FailureCode.http_error
        message = f"The file server returned HTTP {status}"
        retryable = status >= 500
    return FailureItem(
        code=code,
        stage=stage,
        message=message,
        retryable=retryable,
        file_name=file_name,
        http_status=status,
    )


def generic_failure(
    *,
    stage: FailureStage,
    message: str,
    code: FailureCode = FailureCode.unknown,
    retryable: bool = False,
    platform: str | None = None,
    creator_id: str | None = None,
    file_name: str | None = None,
) -> FailureItem:
    return FailureItem(
        code=code,
        stage=stage,
        message=message[:500],
        retryable=retryable,
        platform=platform,
        creator_id=creator_id,
        file_name=file_name,
    )


def failure_report(
    items: list[FailureItem],
    *,
    creator_failures: int = 0,
    file_failures: int = 0,
    summary: str | None = None,
) -> TaskFailureReport:
    bounded = items[:100]
    if summary is None:
        if creator_failures or file_failures:
            summary = f"Task finished with {creator_failures} creator failures and {file_failures} file failures"
        elif bounded:
            summary = bounded[0].message
        else:
            summary = "Task failed"
    return TaskFailureReport(
        summary=summary,
        creator_failures=creator_failures,
        file_failures=file_failures,
        items=bounded,
    )


__all__ = [
    "FailureCode",
    "FailureItem",
    "FailureStage",
    "StagedFailure",
    "TaskExecutionError",
    "TaskFailureReport",
    "classify_failure",
    "failure_from_http_status",
    "failure_report",
    "generic_failure",
]
