import asyncio
import logging
import sys
from pathlib import Path
from typing import Generic, TypeVar, Optional, List, Tuple

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
    "uvloop_init"
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
    return f"{title} - {kwargs}" if kwargs else title


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


def parse_webpage_url(url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    # noinspection SpellCheckingInspection
    """
    Fetch **service**, **user_id**, **post_id** from webpage url

    Each part can be ``None`` if not found in url.

    :param url: Kemono Webpage url
    :return: Tuple of **service**, **user_id**, **post_id**
    """
    path_url = Path(url)
    parts = path_url.parts
    if (url_parts_len := len(parts)) < 7:
        # Pad to full size
        parts += tuple(None for _ in range(7 - url_parts_len))
    _scheme, _netloc, service, _user_key, user_id, _post_key, post_id = parts
    return service, user_id, post_id


def uvloop_init() -> bool:
    """
    Set event loop policy to uvloop if available.

    :return: If uvloop enabled successfully
    """
    if config.use_uvloop:
        if sys.platform == "win32":
            logger.debug("uvloop is not supported on Windows, but it's optional.")
        else:
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
