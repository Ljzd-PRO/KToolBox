from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

__all__ = ["File", "Attachment", "Post", "Revision"]


class File(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None


class Attachment(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None


class Post(BaseModel):
    id: Optional[str] = None
    user: Optional[str] = None
    service: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    embed: Optional[Dict[str, Any]] = None
    shared_file: Optional[bool] = None
    added: Optional[datetime] = None
    published: Optional[datetime] = None
    edited: Optional[datetime] = None
    file: Optional[File] = None
    attachments: Optional[List[Attachment]] = None


class Revision(Post):
    """Revision model that extends Post with revision_id field"""
    revision_id: Optional[int] = None
