from urllib.parse import urlunparse

from k_tool_box.configuration import config

__all__ = ["get_creator_icon", "get_creator_banner"]


def get_creator_icon(creator_id: str, service: str) -> str:
    """
    Get the creator icon for a given creator ID and service.

    :return: The icon URL.
    """
    url_parts = [config.api_scheme, config.statics_host, f"/icons/{service}/{creator_id}", '', '', '']
    return urlunparse(url_parts)


def get_creator_banner(creator_id: str, service: str) -> str:
    """
    Get the creator banner for a given creator ID and service.

    :return: The banner URL.
    """
    url_parts = [config.api_scheme, config.statics_host, f"/banners/{service}/{creator_id}", '', '', '']
    return urlunparse(url_parts)
