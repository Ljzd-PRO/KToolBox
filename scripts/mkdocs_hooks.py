from __future__ import annotations

import re
from typing import Any

from mkdocs.structure.pages import Page

_SHARED_ASSET_LINK = re.compile(r"(?<=\()(?:(?:\.\./)+)assets/")


def on_page_markdown(markdown: str, page: Page, **_: Any) -> str:
    """Resolve shared docs assets from the final localized page depth."""
    page_depth = len([part for part in page.url.split("/") if part])
    asset_prefix = "../" * page_depth
    return _SHARED_ASSET_LINK.sub(f"{asset_prefix}assets/", markdown)
