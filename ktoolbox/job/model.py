from pathlib import Path
from typing import List, Optional, Literal, Dict

from pydantic import BaseModel

from ktoolbox._enum import PostFileTypeEnum
from ktoolbox.api.model import Post
from ktoolbox.model import BaseKToolBoxData

__all__ = ["Job", "JobListData", "CreatorIndices"]


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


# class JobList(Job, UserList[Job]):
#     """
#     (Alternative) Download job list model
#
#     Different from builtin list, it has a ``path`` attribute for root path of the jobs.
#     """
#     server_path: str = Field(exclude=True, default=None)
#     data: List[Job] = []
#
#     def __iter__(self) -> Generator[Job, None, None]:
#         """Generator for iterating over jobs"""
#         yield from self.data


class JobListData(BaseKToolBoxData):
    """
    Download job list data model

    For saving the list of jobs to disk.
    """
    jobs: List[Job] = []
    """All jobs"""


class CreatorIndices(BaseKToolBoxData):
    """
    Creator directory indices model

    Record the path of each downloaded post.
    """
    creator_id: str
    """Creator ID"""
    service: str
    """Creator service"""
    posts: Dict[str, Post] = {}
    """All posts, ``id`` -> ``Post``"""
    posts_path: Dict[str, Path] = {}
    """Posts and their path, ``id`` -> ``Path``"""
