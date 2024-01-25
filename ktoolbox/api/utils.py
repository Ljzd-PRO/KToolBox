from urllib.parse import urlunparse

from ktoolbox.configuration import config

__all__ = ["SEARCH_STEP", "get_creator_icon", "get_creator_banner"]

SEARCH_STEP = 50
"""Searching APIs result steps"""


def get_creator_icon(creator_id: str, service: str) -> str:
    """
    Get the creator icon for a given creator ID and service.

    :return: The icon URL.
    """
    url_parts = [config.api.scheme, config.api.statics_netloc, f"/icons/{service}/{creator_id}", '', '', '']
    return str(urlunparse(url_parts))


def get_creator_banner(creator_id: str, service: str) -> str:
    """
    Get the creator banner for a given creator ID and service.

    :return: The banner URL.
    """
    url_parts = [config.api.scheme, config.api.statics_netloc, f"/banners/{service}/{creator_id}", '', '', '']
    return str(urlunparse(url_parts))
