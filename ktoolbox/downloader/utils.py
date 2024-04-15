import cgi
import os
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Tuple

from ktoolbox.configuration import config

__all__ = ["filename_from_headers", "duplicate_file_check"]


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


def duplicate_file_check(local_file_path: Path, bucket_file_path: Path = None) -> Tuple[bool, Optional[str]]:
    """
    Check if the file existed, and link the bucket filepath to local filepath \
    if ``DownloaderConfiguration.use_bucket`` enabled.

    :param local_file_path: Download target path
    :param bucket_file_path: The bucket filepath of the local download path
    :return: ``(if file existed, message)``
    """
    duplicate_check_path = bucket_file_path or local_file_path
    if duplicate_check_path.is_file():
        if config.downloader.use_bucket:
            ret_msg = "Download file already exists in both bucket and local, skipping"
            if not local_file_path.is_file():
                ret_msg = "Download file already exists in bucket, linking to local path"
                os.link(bucket_file_path, local_file_path)
        else:
            ret_msg = "Download file already exists, skipping"
        return True, ret_msg
    else:
        return False, None
