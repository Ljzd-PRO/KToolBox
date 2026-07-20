from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import TypeVar
from urllib.parse import quote

import httpx
from pydantic import BaseModel, TypeAdapter, ValidationError

from .errors import (
    PawchiveAuthenticationError,
    PawchiveConflictError,
    PawchiveHTTPError,
    PawchiveNotFoundError,
    PawchiveResponseValidationError,
    PawchiveTransportError,
)
from .generated import (
    Announcement,
    Comment,
    CreatorProfile,
    CreatorSummary,
    Fancard,
    FileSearchResult,
    Post,
    Revision,
)
from .parameters import CreatorParameters, CreatorPostListParameters, FileHashParameters, PageParameters, PostParameters

DEFAULT_API_BASE_URL = "https://pawchive.pw/api/v1"

ResponseT = TypeVar("ResponseT")
Sleep = Callable[[float], Awaitable[None]]

CREATOR_LIST_ADAPTER = TypeAdapter(list[CreatorSummary])
POST_LIST_ADAPTER = TypeAdapter(list[Post])
PROFILE_ADAPTER = TypeAdapter(CreatorProfile)
PROFILE_LIST_ADAPTER = TypeAdapter(list[CreatorProfile])
ANNOUNCEMENT_LIST_ADAPTER = TypeAdapter(list[Announcement])
FANCARD_LIST_ADAPTER = TypeAdapter(list[Fancard])
POST_ADAPTER = TypeAdapter(Post)
FILE_SEARCH_ADAPTER = TypeAdapter(FileSearchResult)
REVISION_LIST_ADAPTER = TypeAdapter(list[Revision])
COMMENT_LIST_ADAPTER = TypeAdapter(list[Comment])

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ResponseDrift:
    """Unknown model fields observed in one successful response."""

    operation: str
    fields: tuple[str, ...]


DriftReporter = Callable[[ResponseDrift], None]


def _collect_model_extras(value: object, path: str = "$") -> set[str]:
    extras: set[str] = set()
    if isinstance(value, BaseModel):
        if value.model_extra:
            extras.update(f"{path}.{name}" for name in value.model_extra)
        for field_name in type(value).model_fields:
            extras.update(_collect_model_extras(getattr(value, field_name), f"{path}.{field_name}"))
    elif isinstance(value, list):
        for item in value:
            extras.update(_collect_model_extras(item, f"{path}[]"))
    return extras


def _log_drift(drift: ResponseDrift) -> None:
    LOGGER.warning("Pawchive response drift in %s: %s", drift.operation, ", ".join(drift.fields))


class PawchiveClient:
    """Async client for every public Pawchive API operation."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_API_BASE_URL,
        timeout: float = 5.0,
        max_retries: int = 3,
        retry_interval: float = 2.0,
        verify: bool = True,
        http_client: httpx.AsyncClient | None = None,
        drift_reporter: DriftReporter | None = None,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must not be negative")
        if retry_interval < 0:
            raise ValueError("retry_interval must not be negative")

        parsed_base_url = httpx.URL(base_url.rstrip("/"))
        if not parsed_base_url.is_absolute_url:
            raise ValueError("base_url must be absolute")

        self._base_url = parsed_base_url
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_interval = retry_interval
        self._drift_reporter = drift_reporter or _log_drift
        self._sleep = sleep
        self._owns_http_client = http_client is None
        self._http_client = http_client or httpx.AsyncClient(verify=verify)
        self._closed = False

    async def __aenter__(self) -> PawchiveClient:
        self._ensure_open()
        return self

    async def __aexit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._owns_http_client:
            await self._http_client.aclose()

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("PawchiveClient is closed")

    def _url(self, path: str) -> httpx.URL:
        return httpx.URL(f"{str(self._base_url)}{path}")

    @staticmethod
    def _segment(value: str) -> str:
        return quote(value, safe="")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str | int] | None = None,
        expected_statuses: frozenset[int] = frozenset({200}),
    ) -> httpx.Response:
        self._ensure_open()
        url = self._url(path)

        for attempt in range(self._max_retries + 1):
            try:
                response = await self._http_client.request(
                    method,
                    url,
                    params=params,
                    headers={"Accept": "application/json"},
                    timeout=self._timeout,
                    follow_redirects=False,
                )
            except httpx.TransportError as error:
                if attempt == self._max_retries:
                    raise PawchiveTransportError(method, url, error) from error
                await self._sleep(self._retry_interval)
                continue

            retryable_status = response.status_code == 429 or response.status_code >= 500
            if retryable_status and attempt < self._max_retries:
                await response.aclose()
                await self._sleep(self._retry_interval)
                continue
            if response.status_code not in expected_statuses:
                self._raise_http_error(response)
            return response

        raise AssertionError("request retry loop terminated unexpectedly")

    @staticmethod
    def _raise_http_error(response: httpx.Response) -> None:
        if response.status_code in {401, 403}:
            raise PawchiveAuthenticationError(response)
        if response.status_code == 404:
            raise PawchiveNotFoundError(response)
        if response.status_code == 409:
            raise PawchiveConflictError(response)
        raise PawchiveHTTPError(response)

    def _parse_json(
        self,
        operation: str,
        response: httpx.Response,
        adapter: TypeAdapter[ResponseT],
    ) -> ResponseT:
        try:
            payload = response.json()
            parsed = adapter.validate_python(payload)
        except (ValueError, ValidationError) as error:
            raise PawchiveResponseValidationError(operation, response, error) from error

        extras = tuple(sorted(_collect_model_extras(parsed)))
        if extras:
            self._drift_reporter(ResponseDrift(operation=operation, fields=extras))
        return parsed

    async def list_creators(self) -> list[CreatorSummary]:
        response = await self._request("GET", "/creators")
        return self._parse_json("list_creators", response, CREATOR_LIST_ADAPTER)

    async def list_recent_posts(self, *, query: str | None = None, offset: int | None = None) -> list[Post]:
        parameters = PageParameters(query=query, offset=offset)
        response = await self._request("GET", "/posts", params=parameters.query_parameters())
        return self._parse_json("list_recent_posts", response, POST_LIST_ADAPTER)

    async def get_creator_profile(self, service: str, creator_id: str) -> CreatorProfile:
        parameters = CreatorParameters(service=service, creator_id=creator_id)
        path = f"/{self._segment(parameters.service)}/user/{self._segment(parameters.creator_id)}/profile"
        response = await self._request("GET", path)
        return self._parse_json("get_creator_profile", response, PROFILE_ADAPTER)

    async def list_creator_posts(
        self,
        service: str,
        creator_id: str,
        *,
        query: str | None = None,
        offset: int | None = None,
    ) -> list[Post]:
        parameters = CreatorPostListParameters(
            service=service,
            creator_id=creator_id,
            query=query,
            offset=offset,
        )
        path = f"/{self._segment(parameters.service)}/user/{self._segment(parameters.creator_id)}"
        response = await self._request("GET", path, params=parameters.query_parameters())
        return self._parse_json("list_creator_posts", response, POST_LIST_ADAPTER)

    async def list_announcements(self, service: str, creator_id: str) -> list[Announcement]:
        parameters = CreatorParameters(service=service, creator_id=creator_id)
        path = f"/{self._segment(parameters.service)}/user/{self._segment(parameters.creator_id)}/announcements"
        response = await self._request("GET", path)
        return self._parse_json("list_announcements", response, ANNOUNCEMENT_LIST_ADAPTER)

    async def list_fancards(self, service: str, creator_id: str) -> list[Fancard]:
        parameters = CreatorParameters(service=service, creator_id=creator_id)
        path = f"/{self._segment(parameters.service)}/user/{self._segment(parameters.creator_id)}/fancards"
        response = await self._request("GET", path)
        return self._parse_json("list_fancards", response, FANCARD_LIST_ADAPTER)

    async def list_creator_links(self, service: str, creator_id: str) -> list[CreatorProfile]:
        parameters = CreatorParameters(service=service, creator_id=creator_id)
        path = f"/{self._segment(parameters.service)}/user/{self._segment(parameters.creator_id)}/links"
        response = await self._request("GET", path)
        return self._parse_json("list_creator_links", response, PROFILE_LIST_ADAPTER)

    async def get_post(self, service: str, creator_id: str, post_id: str) -> Post:
        parameters = PostParameters(service=service, creator_id=creator_id, post_id=post_id)
        path = (
            f"/{self._segment(parameters.service)}/user/{self._segment(parameters.creator_id)}"
            f"/post/{self._segment(parameters.post_id)}"
        )
        response = await self._request("GET", path)
        return self._parse_json("get_post", response, POST_ADAPTER)

    async def search_file_by_hash(self, file_hash: str) -> FileSearchResult:
        parameters = FileHashParameters(file_hash=file_hash)
        response = await self._request("GET", f"/search_hash/{parameters.file_hash}")
        return self._parse_json("search_file_by_hash", response, FILE_SEARCH_ADAPTER)

    async def flag_post(self, service: str, creator_id: str, post_id: str) -> None:
        parameters = PostParameters(service=service, creator_id=creator_id, post_id=post_id)
        path = (
            f"/{self._segment(parameters.service)}/user/{self._segment(parameters.creator_id)}"
            f"/post/{self._segment(parameters.post_id)}/flag"
        )
        await self._request("POST", path, expected_statuses=frozenset({201}))

    async def is_post_flagged(self, service: str, creator_id: str, post_id: str) -> bool:
        parameters = PostParameters(service=service, creator_id=creator_id, post_id=post_id)
        path = (
            f"/{self._segment(parameters.service)}/user/{self._segment(parameters.creator_id)}"
            f"/post/{self._segment(parameters.post_id)}/flag"
        )
        response = await self._request("GET", path, expected_statuses=frozenset({200, 404}))
        return response.status_code == 200

    async def list_post_revisions(self, service: str, creator_id: str, post_id: str) -> list[Revision]:
        parameters = PostParameters(service=service, creator_id=creator_id, post_id=post_id)
        path = (
            f"/{self._segment(parameters.service)}/user/{self._segment(parameters.creator_id)}"
            f"/post/{self._segment(parameters.post_id)}/revisions"
        )
        response = await self._request("GET", path)
        return self._parse_json("list_post_revisions", response, REVISION_LIST_ADAPTER)

    async def list_post_comments(self, service: str, creator_id: str, post_id: str) -> list[Comment]:
        parameters = PostParameters(service=service, creator_id=creator_id, post_id=post_id)
        path = (
            f"/{self._segment(parameters.service)}/user/{self._segment(parameters.creator_id)}"
            f"/post/{self._segment(parameters.post_id)}/comments"
        )
        response = await self._request("GET", path)
        return self._parse_json("list_post_comments", response, COMMENT_LIST_ADAPTER)

    async def get_app_version(self) -> str:
        response = await self._request("GET", "/app_version")
        return response.text.strip()
