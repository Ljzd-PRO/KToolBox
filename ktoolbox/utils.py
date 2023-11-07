import cgi
import urllib.parse
from typing import Generic, TypeVar, Optional, Dict

from pydantic import BaseModel, ConfigDict

from ktoolbox.configuration import config
from ktoolbox.enum import RetCodeEnum

__all__ = ["BaseRet", "file_name_from_headers", "generate_message"]
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

    Apply when `cgi.parse_header` is unable to use due to the deprecation of `cgi` module.

    https://peps.python.org/pep-0594/#cgi

    :param line: Header line
    :return: Dict of header line

    * Example:
    ```
    parse_header("text/html; charset=utf-8")
    ```

    * Return:
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


def file_name_from_headers(headers: Dict[str, str]) -> Optional[str]:
    """
    Get file name from headers.

    Parse from `Content-Disposition`.

    :param headers: HTTP headers
    :return: File name

    * Example:
    ```
    file_name_from_headers('attachment;filename*=utf-8\\'\\'README%2Emd;filename="README.md"')
    ```

    * Return:
    ```
    README.md
    ```
    """
    if not (disposition := headers.get("Content-Disposition")):
        if not (disposition := headers.get("content-disposition")):
            return None
    _, options = cgi.parse_header(disposition)  # alternative: `parse_header` in `utils.py`
    if file_name := options.get("filename*"):
        if len(name_with_charset := file_name.split("''")) == 2:
            charset, name = name_with_charset
            return urllib.parse.unquote(name, charset)
    if file_name := options.get("filename"):
        return urllib.parse.unquote(file_name, config.downloader.encoding)
    return None


def generate_message(title: str = None, **kwargs):
    """
    Generate message for `BaseRet` and logger

    :param title:
    :param kwargs:
    :return:
    """
    title: str = title or ""
    return f"{title} - {kwargs}" if kwargs else title
