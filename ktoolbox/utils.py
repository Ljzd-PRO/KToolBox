import cgi
import sys
import urllib.parse
from pathlib import Path
from typing import Generic, TypeVar, Optional, Dict, List, Union, Tuple

import aiofiles
from loguru import logger
from pydantic import BaseModel, ConfigDict

from ktoolbox.configuration import config
from ktoolbox.enum import RetCodeEnum, DataStorageNameEnum
from ktoolbox.model import SearchResult

__all__ = ["BaseRet", "filename_from_headers", "generate_msg", "logger_init", "dump_search", "parse_webpage_url"]

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


def parse_header(line: str) -> Dict[str, Optional[str]]:
    """
    Alternative resolution for parsing header line.

    Apply when ``cgi.parse_header`` is unable to use due to the deprecation of `cgi` module.

    https://peps.python.org/pep-0594/#cgi

    :param line: Header line
    :return: Dict of header line

    .. rubric:: Example:
    ```
    parse_header("text/html; charset=utf-8")
    ```

    .. rubric:: Return:
    ```
    {'text/html': None, 'charset': 'utf-8'}
    ```
    """
    dict_value: Dict[str, Optional[str]] = {}
    for item in line.split(";"):
        if len(pair := item.split("=")) == 1:
            dict_value[pair[0]] = None
        else:
            dict_value.setdefault(*pair)
    return dict_value


def filename_from_headers(headers: Dict[str, str]) -> Optional[str]:
    """
    Get file name from headers.

    Parse from ``Content-Disposition``.

    :param headers: HTTP headers
    :return: File name

    .. rubric:: Example:
    ```
    filename_from_headers('attachment;filename*=utf-8\\'\\'README%2Emd;filename="README.md"')
    ```

    .. rubric:: Return:
    ```
    README.md
    ```
    """
    if not (disposition := headers.get("Content-Disposition")):
        if not (disposition := headers.get("content-disposition")):
            return None
    _, options = cgi.parse_header(disposition)  # alternative: `parse_header` in `utils.py`
    if filename := options.get("filename*"):
        if len(name_with_charset := filename.split("''")) == 2:
            charset, name = name_with_charset
            return urllib.parse.unquote(name, charset)
    if filename := options.get("filename"):
        return urllib.parse.unquote(filename, config.downloader.encoding)
    return None


def generate_msg(title: str = None, **kwargs):
    """
    Generate message for ``BaseRet`` and logger

    :param title: Message title
    :param kwargs: Extra data
    """
    title: str = title or ""
    return f"{title} - {kwargs}" if kwargs else title


def logger_init(std_level: Union[str, int] = None, disable_stdout: bool = False):
    """
    Initialize ``loguru`` logger

    :param std_level: Standard output log filter level
    :param disable_stdout: Disable default output stream
    """
    if disable_stdout:
        logger.remove()
    elif std_level is not None:
        logger.remove()
        logger.add(
            sys.stderr,
            level=std_level
        )
    path = config.logger.path
    if not path.is_dir():
        path.mkdir()
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
