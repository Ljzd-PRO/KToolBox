from __future__ import annotations

import httpx


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
        super().__init__(f"Pawchive returned an invalid response for {operation}")
