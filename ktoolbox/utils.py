import asyncio
import html
import logging
import re
import sys
from pathlib import Path
from typing import Generic, TypeVar, Optional, List, Tuple, Set

import aiofiles
from loguru import logger
from pydantic import BaseModel, ConfigDict
from tqdm import tqdm

from ktoolbox._enum import RetCodeEnum, DataStorageNameEnum
from ktoolbox.configuration import config
from ktoolbox.model import SearchResult

__all__ = [
    "BaseRet",
    "generate_msg",
    "logger_init",
    "dump_search",
    "parse_webpage_url",
    "uvloop_init",
    "extract_external_links"
]

_T = TypeVar('_T')


class BaseRet(BaseModel, Generic[_T]):
    """Base data model of function return value"""
    code: int = RetCodeEnum.Success.value
    message: str = ''
    exception: Optional[Exception] = None
    data: Optional[_T] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __bool__(self):
        return self.code == RetCodeEnum.Success


def generate_msg(title: str = None, **kwargs):
    """
    Generate message for ``BaseRet`` and logger

    :param title: Message title
    :param kwargs: Extra data
    """
    title: str = title or ""
    extra_data = ", ".join(f"{k}: {v}" for k, v in kwargs.items())
    if title:
        return f"{title} - {extra_data}" if kwargs else title
    else:
        return extra_data if kwargs else ""


def logger_init(cli_use: bool = False, disable_stdout: bool = False):
    """
    Initialize ``loguru`` logger

    :param cli_use: Set logger level ``INFO`` and filter out ``SUCCESS``
    :param disable_stdout: Disable default output stream
    """
    if disable_stdout:
        logger.remove()
    elif cli_use:
        logger.remove()
        logger.add(
            tqdm.write,
            colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan> - <level>{message}</level>",
            level=logging.INFO,
            filter=lambda record: record["level"].name != "SUCCESS"
        )
    if path := config.logger.path:
        path.mkdir(exist_ok=True)
        if path is not None:
            logger.add(
                path / DataStorageNameEnum.LogData.value,
                level=config.logger.level,
                rotation=config.logger.rotation,
                diagnose=True
            )


async def dump_search(result: List[BaseModel], path: Path):
    async with aiofiles.open(str(path), "w", encoding="utf-8") as f:
        await f.write(
            SearchResult(result=result)
            .model_dump_json(indent=config.json_dump_indent)
        )


def parse_webpage_url(url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    # noinspection SpellCheckingInspection
    """
    Fetch **service**, **user_id**, **post_id**, **revision_id** from webpage url

    Each part can be ``None`` if not found in url.

    :param url: Kemono Webpage url
    :return: Tuple of **service**, **user_id**, **post_id**, **revision_id**
    """
    path_url = Path(url)
    parts = path_url.parts
    if (url_parts_len := len(parts)) < 9:
        # Pad to full size (now supporting revision URLs)
        parts += tuple(None for _ in range(9 - url_parts_len))
    _scheme, _netloc, service, _user_key, user_id, _post_key, post_id, _revision_key, revision_id = parts
    
    # Only return revision_id if we have the revision keyword
    if _revision_key != "revision":
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
                    "uvloop is not installed, but it's optional. "
                    "You can install it with `pip install ktoolbox[uvloop]`"
                )
            else:
                asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
                logger.success("Set event loop policy to uvloop successfully.")
                return True
    return False


def extract_external_links(content: str, custom_patterns: Optional[List[str]] = None) -> Set[str]:
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
    combined_pattern = '|'.join(f'({pattern})' for pattern in external_link_patterns)

    # Find all matches
    matches = re.finditer(combined_pattern, content, re.IGNORECASE)

    for match in matches:
        # Get the full matched URL
        url = match.group(0)

        # Clean up HTML markup and common trailing punctuation that might be part of text
        # Stop at common HTML boundary characters and quotes
        url = re.sub(r'["\'>][^<]*$', '', url)  # Remove quote + content to end  
        
        # Additional cleanup: Remove HTML tags that might have been captured  
        url = re.sub(r'<[^>]*>.*$', '', url)  # Remove any HTML tags and everything after
        url = re.sub(r'"[^"]*$', '', url)  # Remove quote and everything after it
        
        # Remove trailing HTML tag fragments and punctuation
        url = re.sub(r'</[^>]*>?$', '', url)  # Remove closing tags or partial tags at end
        url = re.sub(r'[.,;!?)\]}>"\'\s]+$', '', url)  # Remove trailing punctuation
        
        # Decode HTML entities (like &amp; -> &, &lt; -> <, etc.)
        url = html.unescape(url)

        # Validate that it looks like a proper URL
        if len(url) > 10 and '.' in url:
            links.add(url)

    return links
