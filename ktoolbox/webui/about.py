from __future__ import annotations

import platform
from importlib.metadata import PackageNotFoundError, metadata

from ktoolbox import __version__
from ktoolbox.webui.models import AboutResponse

_DESCRIPTION = "An asynchronous CLI and typed Python client for downloading public Pawchive posts"
_AUTHOR = "Ljzd-PRO"
_LICENSE = "BSD-3-Clause"
_URLS = {
    "documentation": "https://ktoolbox.readthedocs.io/",
    "repository": "https://github.com/Ljzd-PRO/KToolBox",
    "issues": "https://github.com/Ljzd-PRO/KToolBox/issues",
}


def build_about_response() -> AboutResponse:
    try:
        package = metadata("ktoolbox")
    except PackageNotFoundError:
        return _fallback_response()

    project_urls = _project_urls(package.get_all("Project-URL") or [])
    authors = _author_names(
        [
            *(package.get_all("Author") or []),
            *(package.get_all("Author-email") or []),
        ]
    )
    return AboutResponse(
        name=package["Name"] or "KToolBox",
        version=package["Version"] or __version__,
        description=package["Summary"] or _DESCRIPTION,
        license=package["License-Expression"] or package["License"] or _LICENSE,
        authors=authors or [_AUTHOR],
        python_version=platform.python_version(),
        urls={**_URLS, **project_urls},
    )


def _fallback_response() -> AboutResponse:
    return AboutResponse(
        name="KToolBox",
        version=__version__,
        description=_DESCRIPTION,
        license=_LICENSE,
        authors=[_AUTHOR],
        python_version=platform.python_version(),
        urls=dict(_URLS),
    )


def _project_urls(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    aliases = {
        "homepage": "documentation",
        "documentation": "documentation",
        "repository": "repository",
        "bug tracker": "issues",
        "issues": "issues",
    }
    for value in values:
        label, separator, url = value.partition(",")
        key = aliases.get(label.strip().casefold())
        if separator and key and url.strip():
            result[key] = url.strip()
    return result


def _author_names(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        name = value.partition("<")[0].strip()
        if not name or "@" in name or name in result:
            continue
        result.append(name)
    return result
