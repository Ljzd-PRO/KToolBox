from datetime import datetime
from typing import Optional

from pydantic import BaseModel

__all__ = ["Announcement"]


class Announcement(BaseModel):
    service: Optional[str] = None
    user_id: Optional[str] = None
    hash: Optional[str] = None
    """sha256"""
    content: Optional[str] = None
    added: Optional[datetime] = None
    # noinspection SpellCheckingInspection
    """isoformat UTC"""
