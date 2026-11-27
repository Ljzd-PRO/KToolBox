from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

from ktoolbox._enum import PostFileTypeEnum
from ktoolbox.api.generated import Post
from ktoolbox.job.temporary import TemporaryFile
from ktoolbox.model import BaseKToolBoxData

__all__ = ["Job", "JobListData", "CreatorIndices"]


class Job(BaseModel):
    """
    Download job model
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: Path
    """Directory path to save the file"""
    alt_filename: str | None = None
    """Use this name if no filename given by the server"""
    server_path: str
    """The `path` part of download URL"""
    type: Literal[PostFileTypeEnum.Attachment, PostFileTypeEnum.File] | None = None
    """Target file type"""
    post: Post | None = None
    """Post object"""
    temporary: SkipJsonSchema[TemporaryFile | None] = Field(default=None, exclude=True, repr=False)


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

    jobs: list[Job] = []
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
    posts: dict[str, Post] = {}
    """All posts, ``id`` -> ``Post``"""
    posts_path: dict[str, Path] = {}
    """Posts and their path, ``id`` -> ``Path``"""
