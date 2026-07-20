from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from urllib.parse import quote, urlsplit, urlunsplit

from ktoolbox.api.client import PawchiveClient
from ktoolbox.configuration import config

__all__ = [
    "SEARCH_STEP",
    "create_pawchive_client",
    "get_creator_banner",
    "get_creator_icon",
    "get_file_url",
    "pawchive_client_scope",
]

SEARCH_STEP = 50
"""Number of results returned by one paginated Pawchive request."""


def _host_url(scheme: str, netloc: str, path: str, query: str = "") -> str:
    return urlunsplit((scheme, netloc, path, query, ""))


def create_pawchive_client() -> PawchiveClient:
    """Create a Pawchive client from the active KToolBox configuration."""
    base_url = _host_url(config.api.scheme, config.api.netloc, config.api.path.rstrip("/"))
    return PawchiveClient(
        base_url=base_url,
        timeout=config.api.timeout,
        max_retries=config.api.retry_times,
        retry_interval=config.api.retry_interval,
        verify=config.ssl_verify,
    )


@asynccontextmanager
async def pawchive_client_scope(client: PawchiveClient | None) -> AsyncIterator[PawchiveClient]:
    """Reuse an injected client or own one for the duration of the scope."""
    if client is not None:
        yield client
        return
    async with create_pawchive_client() as created_client:
        yield created_client


def get_creator_icon(creator_id: str, service: str) -> str:
    """Build the URL of a Pawchive creator icon."""
    path = f"/icons/{quote(service, safe='')}/{quote(creator_id, safe='')}"
    return _host_url(config.api.scheme, config.api.statics_netloc, path)


def get_creator_banner(creator_id: str, service: str) -> str:
    """Build the URL of a Pawchive creator banner."""
    path = f"/banners/{quote(service, safe='')}/{quote(creator_id, safe='')}"
    return _host_url(config.api.scheme, config.api.statics_netloc, path)


def get_file_url(server_path: str) -> str:
    """Build a Pawchive file-host URL from a path returned by the API."""
    parsed_path = urlsplit(server_path)
    prefix = f"/{config.downloader.file_path_prefix.strip('/')}"
    path = f"/{parsed_path.path.lstrip('/')}"
    if path != prefix and not path.startswith(f"{prefix}/"):
        path = f"{prefix}{path}"
    return _host_url(config.downloader.scheme, config.downloader.files_netloc, path, parsed_path.query)
