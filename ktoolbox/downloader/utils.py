import cgi
import urllib.parse
from typing import Optional, Dict

from ktoolbox.configuration import config

__all__ = ["filename_from_headers"]


def parse_header(line: str) -> Dict[str, Optional[str]]:
    """
    Alternative resolution for parsing header line.

    Apply when ``cgi.parse_header`` is unable to use due to the deprecation of `cgi` module.

    https://peps.python.org/pep-0594/#cgi

    - Example:
    ```
    parse_header("text/html; charset=utf-8")
    ```

    - Return:
    ```
    {'text/html': None, 'charset': 'utf-8'}
    ```

    :param line: Header line
    :return: Dict of header line
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

    - Example:
    ```
    filename_from_headers('attachment;filename*=utf-8\\'\\'README%2Emd;filename="README.md"')
    ```

    - Return:
    ```
    README.md
    ```

    :param headers: HTTP headers
    :return: File name
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
