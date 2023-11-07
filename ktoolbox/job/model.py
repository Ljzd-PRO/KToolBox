from collections import UserList
from pathlib import Path
from typing import List, Generator, Optional, Literal

from pydantic import BaseModel, Field

__all__ = ["Job"]

from ktoolbox.enum import PostFileTypeEnum


class Job(BaseModel):
    """
    Download job model
    """
    path: Path
    """Directory path to save the file"""
    alt_filename: Optional[str] = None
    """Use this name if no filename given by the server"""
    server_path: str
    """The `path` part of download URL"""
    type: Optional[Literal[PostFileTypeEnum.Attachment, PostFileTypeEnum.File]] = None
    """Target file type"""


class JobList(Job, UserList[Job]):
    """
    (Alternative) Download job list model

    Different from builtin list, it has a `path` attribute for root path of the jobs.
    """
    server_path: str = Field(exclude=True, default=None)
    data: List[Job] = []

    def __iter__(self) -> Generator[Job, None, None]:
        """Generator for iterating over jobs"""
        yield from self.data
