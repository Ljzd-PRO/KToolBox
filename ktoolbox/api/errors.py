from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import ValidationError

_SAFE_FIELD_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")


@dataclass(frozen=True, slots=True)
class ResponseValidationIssue:
    """A response validation issue that contains no upstream values."""

    path: str
    error_type: str


def _safe_validation_path(location: tuple[Any, ...]) -> str:
    path = "$"
    for segment in location:
        if isinstance(segment, int):
            path += f"[{segment}]"
        elif isinstance(segment, str) and _SAFE_FIELD_NAME.fullmatch(segment):
            path += f".{segment}"
        else:
            path += ".field"
    return path


def _validation_issues(cause: Exception) -> tuple[ResponseValidationIssue, ...]:
    if not isinstance(cause, ValidationError):
        return (ResponseValidationIssue(path="$", error_type="invalid_json"),)
    return tuple(
        ResponseValidationIssue(
            path=_safe_validation_path(tuple(error.get("loc", ()))),
            error_type=str(error.get("type", "validation_error")),
        )
        for error in cause.errors(include_url=False, include_context=False, include_input=False)
    )


class PawchiveError(Exception):
    """Base exception for Pawchive client failures."""


class PawchiveTransportError(PawchiveError):
    """Raised after a transport failure exhausts configured retries."""

    def __init__(self, method: str, url: httpx.URL, cause: httpx.TransportError) -> None:
        self.method = method
        self.url = url
        self.cause = cause
        super().__init__(f"Pawchive transport failure for {method} {url.path}")


class PawchiveHTTPError(PawchiveError):
    """Raised when Pawchive returns an unexpected HTTP status."""

    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        request = response.request
        super().__init__(f"Pawchive returned HTTP {response.status_code} for {request.method} {request.url.path}")

    @property
    def status_code(self) -> int:
        return self.response.status_code


class PawchiveAuthenticationError(PawchiveHTTPError):
    """Raised for authentication or authorization failures."""


class PawchiveNotFoundError(PawchiveHTTPError):
    """Raised when a Pawchive resource does not exist."""


class PawchiveConflictError(PawchiveHTTPError):
    """Raised when a Pawchive state-changing operation conflicts."""


class PawchiveResponseValidationError(PawchiveError):
    """Raised when a successful response does not satisfy its response model."""

    def __init__(self, operation: str, response: httpx.Response, cause: Exception) -> None:
        self.operation = operation
        self.response = response
        self.cause = cause
        self.issues = _validation_issues(cause)
        detail = ", ".join(f"{issue.path}: {issue.error_type}" for issue in self.issues[:3])
        suffix = f" ({detail})" if detail else ""
        super().__init__(f"Pawchive returned an invalid response for {operation}{suffix}")
