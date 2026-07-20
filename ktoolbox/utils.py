import asyncio
import html
import logging
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Generic, TypeVar
from urllib.parse import urlparse

import aiofiles  # type: ignore[import-untyped]
from loguru import logger
from pydantic import BaseModel, ConfigDict
from rich.console import Console
from rich.logging import RichHandler

from ktoolbox._enum import DataStorageNameEnum, RetCodeEnum
from ktoolbox.configuration import config
from ktoolbox.model import SearchResult

__all__ = [
    "BaseRet",
    "generate_msg",
    "logger_init",
    "dump_search",
    "parse_webpage_url",
    "uvloop_init",
    "extract_external_links",
    "check_for_updates",
]

_T = TypeVar("_T")


class BaseRet(BaseModel, Generic[_T]):
    """Base data model of function return value"""

    code: int = RetCodeEnum.Success.value
    message: str = ""
    exception: Exception | None = None
    data: _T | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __bool__(self) -> bool:
        return self.code == RetCodeEnum.Success


def generate_msg(title: str | None = None, **kwargs: object) -> str:
    """
    Generate message for ``BaseRet`` and logger

    :param title: Message title
    :param kwargs: Extra data
    """
    title = title or ""
    extra_data = ", ".join(f"{k}: {v}" for k, v in kwargs.items())
    if title:
        return f"{title} - {extra_data}" if kwargs else title
    else:
        return extra_data if kwargs else ""


def logger_init(
    cli_use: bool = False,
    disable_stdout: bool = False,
    *,
    console: Console | None = None,
) -> None:
    """
    Initialize ``loguru`` logger

    :param cli_use: Set logger level ``INFO`` and filter out ``SUCCESS``
    :param disable_stdout: Disable default output stream
    """
    if disable_stdout:
        logger.remove()
    elif cli_use:
        logger.remove()
        handler = RichHandler(
            console=console or Console(stderr=True),
            show_path=False,
            rich_tracebacks=False,
            markup=False,
        )
        logger.add(
            handler,
            format="{message}",
            level=logging.INFO,
            filter=lambda record: record["level"].name != "DEBUG",
        )
    if path := config.logger.path:
        path.mkdir(exist_ok=True)
        if path is not None:
            logger.add(
                path / DataStorageNameEnum.LogData.value,
                level=config.logger.level,
                rotation=config.logger.rotation,
                diagnose=True,
            )


async def dump_search(result: Sequence[BaseModel], path: Path) -> None:
    async with aiofiles.open(str(path), "w", encoding="utf-8") as f:
        await f.write(SearchResult(result=list(result)).model_dump_json(indent=config.json_dump_indent))


def parse_webpage_url(url: str) -> tuple[str | None, str | None, str | None, str | None]:
    # noinspection SpellCheckingInspection
    """
    Fetch **service**, **user_id**, **post_id**, **revision_id** from webpage url

    Each part can be ``None`` if not found in url.

    :param url: Pawchive post or creator URL
    :return: Tuple of **service**, **user_id**, **post_id**, **revision_id**
    """
    parts = [part for part in urlparse(url).path.split("/") if part]
    service = parts[0] if parts else None
    user_id = parts[2] if len(parts) > 2 and parts[1] == "user" else None
    post_id = parts[4] if len(parts) > 4 and parts[3] == "post" else None
    revision_id = parts[6] if len(parts) > 6 and parts[5] == "revision" else None

    # Only return revision_id if we have the revision keyword
    if len(parts) <= 5 or parts[5] != "revision":
        revision_id = None

    return service, user_id, post_id, revision_id


def uvloop_init() -> bool:
    """
    Set event loop policy to uvloop or winloop if available.

    Uses winloop on Windows and uvloop on Unix-like systems for performance optimization.

    :return: If event loop policy was set successfully
    """
    if config.use_uvloop:
        if sys.platform == "win32":
            # Try to use winloop on Windows
            try:
                # noinspection PyUnresolvedReferences
                import winloop
            except ModuleNotFoundError:
                logger.debug(
                    "winloop is not installed, but it's optional. "
                    "You can install it with `pip install ktoolbox[winloop]`"
                )
            else:
                asyncio.set_event_loop_policy(winloop.EventLoopPolicy())
                logger.success("Set event loop policy to winloop successfully.")
                return True
        else:
            # Try to use uvloop on Unix-like systems
            try:
                # noinspection PyUnresolvedReferences
                import uvloop
            except ModuleNotFoundError:
                logger.debug(
                    "uvloop is not installed, but it's optional. You can install it with `pip install ktoolbox[uvloop]`"
                )
            else:
                asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
                logger.success("Set event loop policy to uvloop successfully.")
                return True
    return False


def extract_external_links(content: str, custom_patterns: list[str] | None = None) -> set[str]:
    """
    Extract external file sharing links from text content.

    Targets common cloud storage and file sharing services like:
    - Google Drive
    - MEGA
    - Dropbox
    - OneDrive
    - MediaFire
    - And other common file hosting services

    :param content: Text content to extract links from
    :param custom_patterns: Custom regex patterns to use.
    :return: Set of unique external links found
    """
    if not content:
        return set()

    external_link_patterns = custom_patterns if custom_patterns is not None else []

    links = set()

    # Combine all patterns
    combined_pattern = "|".join(f"({pattern})" for pattern in external_link_patterns)

    # Find all matches
    matches = re.finditer(combined_pattern, content, re.IGNORECASE)

    for match in matches:
        # Get the full matched URL
        url = match.group(0)

        # Clean up HTML markup and common trailing punctuation that might be part of text
        # Stop at common HTML boundary characters and quotes
        url = re.sub(r'["\'>][^<]*$', "", url)  # Remove quote + content to end

        # Additional cleanup: Remove HTML tags that might have been captured
        url = re.sub(r"<[^>]*>.*$", "", url)  # Remove any HTML tags and everything after
        url = re.sub(r'"[^"]*$', "", url)  # Remove quote and everything after it

        # Remove trailing HTML tag fragments and punctuation
        url = re.sub(r"</[^>]*>?$", "", url)  # Remove closing tags or partial tags at end
        url = re.sub(r'[.,;!?)\]}>"\'\s]+$', "", url)  # Remove trailing punctuation

        # Decode HTML entities (like &amp; -> &, &lt; -> <, etc.)
        url = html.unescape(url)

        # Validate that it looks like a proper URL
        if len(url) > 10 and "." in url:
            links.add(url)

    return links


async def check_for_updates() -> None:
    """
    Check for updates from GitHub and PyPI (backup).
    Show information if a newer version is available.
    """
    try:
        import httpx

        from ktoolbox import __version__

        current_version = __version__.lstrip("v")  # Remove 'v' prefix if present

        # First try GitHub API
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("https://api.github.com/repos/Ljzd-PRO/KToolBox/releases/latest")
                if response.status_code == 200:
                    data = response.json()
                    latest_version = data["tag_name"].lstrip("v")
                    if latest_version != current_version:
                        logger.info(f"Update available: {latest_version} (current: {current_version})")
                        logger.info(f"Release URL: {data['html_url']}")
                        return
                    else:
                        logger.debug("You are using the latest version")
                        return
        except Exception as e:
            logger.debug(f"Failed to check GitHub for updates: {e}")

        # Fallback to PyPI API
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("https://pypi.org/pypi/ktoolbox/json")
                if response.status_code == 200:
                    data = response.json()
                    latest_version = data["info"]["version"].lstrip("v")
                    if latest_version != current_version:
                        logger.info(f"Update available: {latest_version} (current: {current_version})")
                        logger.info("Run 'pip install --upgrade ktoolbox' or 'pipx upgrade ktoolbox' to update")
                    else:
                        logger.debug("You are using the latest version")
        except Exception as e:
            logger.debug(f"Failed to check PyPI for updates: {e}")

    except Exception as e:
        logger.warning(f"Update check encountered an unexpected error: {e!r}")
