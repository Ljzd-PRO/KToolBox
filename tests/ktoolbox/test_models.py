from __future__ import annotations

from pathlib import Path

from ktoolbox._enum import PostFileTypeEnum, RetCodeEnum
from ktoolbox.api.generated import Post
from ktoolbox.job import CreatorIndices, Job, JobListData
from ktoolbox.model import SearchResult
from ktoolbox.utils import BaseRet


def test_return_and_storage_models_serialize_type_information() -> None:
    assert BaseRet(code=RetCodeEnum.Success)
    assert not BaseRet(code=RetCodeEnum.GeneralFailure)

    post = Post(id="post", user="creator", service="fanbox")
    job = Job(
        path=Path("downloads"),
        alt_filename="file.jpg",
        server_path="/hash/file.jpg",
        type=PostFileTypeEnum.File,
        post=post,
    )
    job_data = JobListData(jobs=[job])
    indices = CreatorIndices(
        creator_id="creator",
        service="fanbox",
        posts={post.id: post},
        posts_path={post.id: Path("downloads/post")},
    )
    search = SearchResult(result=[post])

    assert "JobListData" in job_data.model_dump()["type"]
    assert indices.posts_path["post"] == Path("downloads/post")
    assert search.result == [post]
