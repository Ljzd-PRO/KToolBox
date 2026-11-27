from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import unquote, urlsplit

from pydantic import SecretStr

from .generated import FileReference

_TEMPORARY_HOST = re.compile(r"t[1-9][0-9]*\.pawchive\.pw", re.ASCII | re.IGNORECASE)
_DOWNLOAD_ROUTES = ("/d/", "/f/")


def validated_temporary_url(value: str) -> str | None:
    """Validate the destination without rewriting the path or signed query."""
    if any(ord(char) <= 32 or ord(char) == 127 or char == "\\" for char in value):
        return None
    try:
        url = urlsplit(value)
    except ValueError:
        return None
    if url.scheme != "https" or not _TEMPORARY_HOST.fullmatch(url.netloc) or url.fragment:
        return None
    if not url.path.startswith(_DOWNLOAD_ROUTES) or not url.path[3:]:
        return None
    decoded_path = unquote(url.path)
    if "\\" in decoded_path or any(segment in {".", ".."} for segment in decoded_path.split("/")):
        return None
    return value


def protect_temporary_path(reference: FileReference) -> None:
    """Some responses put a temporary URL in the otherwise public path field."""
    if not reference.path:
        return
    try:
        url = urlsplit(reference.path)
    except ValueError:
        if reference.deferred:
            reference.path = None
        return
    if not (
        (url.hostname is not None and _TEMPORARY_HOST.fullmatch(url.hostname))
        or (reference.deferred and (url.netloc or url.scheme or url.path.startswith(_DOWNLOAD_ROUTES)))
    ):
        return
    if not reference.temp_download_url and (validated := validated_temporary_url(reference.path)):
        reference.temp_download_url = SecretStr(validated)
    reference.path = None
    reference.deferred = True


def active_temporary_url(reference: FileReference, now: datetime) -> str | None:
    if reference.preview_only or reference.temp_download_url is None:
        return None
    expires = reference.temp_expires
    if expires is not None and (expires if expires.tzinfo else expires.replace(tzinfo=timezone.utc)) <= now:
        return None
    return validated_temporary_url(reference.temp_download_url.get_secret_value())
