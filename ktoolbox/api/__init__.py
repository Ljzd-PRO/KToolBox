"""Public Pawchive API client surface."""

from .client import PawchiveClient, ResponseDrift
from .errors import (
    PawchiveAuthenticationError,
    PawchiveConflictError,
    PawchiveError,
    PawchiveHTTPError,
    PawchiveNotFoundError,
    PawchiveResponseValidationError,
    PawchiveTransportError,
    ResponseValidationIssue,
)
from .generated import (
    Announcement,
    Comment,
    CreatorProfile,
    CreatorSummary,
    Fancard,
    FileReference,
    FileSearchResult,
    Post,
    Revision,
)

__all__ = [
    "Announcement",
    "Comment",
    "CreatorProfile",
    "CreatorSummary",
    "Fancard",
    "FileReference",
    "FileSearchResult",
    "PawchiveAuthenticationError",
    "PawchiveClient",
    "PawchiveConflictError",
    "PawchiveError",
    "PawchiveHTTPError",
    "PawchiveNotFoundError",
    "PawchiveResponseValidationError",
    "PawchiveTransportError",
    "Post",
    "ResponseDrift",
    "ResponseValidationIssue",
    "Revision",
]
