from datetime import datetime

from pydantic import BaseModel

__all__ = ["Creator"]


class Creator(BaseModel):
    # noinspection SpellCheckingInspection
    favorited: int
    # noinspection SpellCheckingInspection
    """The number of times this creator has been favorited"""
    id: str
    """The ID of the creator"""
    indexed: datetime
    """Timestamp when the creator was indexed, Unix time as integer"""
    name: str
    """The name of the creator"""
    service: str
    """The service for the creator"""
    updated: datetime
    """Timestamp when the creator was last updated, Unix time as integer"""
