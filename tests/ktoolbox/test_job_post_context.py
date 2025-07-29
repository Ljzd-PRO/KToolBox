"""
Test cases for post context in job error messages
"""
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from loguru import logger
from httpx import RemoteProtocolError

from ktoolbox.api.model import Post, Attachment, File
from ktoolbox.action.job import create_job_from_post
from ktoolbox.job import Job
from ktoolbox.job.runner import JobRunner
from ktoolbox._enum import PostFileTypeEnum


@pytest.mark.asyncio
async def test_create_job_from_post_includes_context():
    """Test that jobs created from post include post context information"""
    # Create a test post
    post = Post(
        id="test_post_123",
        title="Test Post Title",
        service="patreon",
        user="test_user",
        attachments=[
            Attachment(name="test_file.jpg", path="/files/test_file.jpg")
        ],
        file=File(name="main_file.mp4", path="/files/main_file.mp4")
    )
    
    # Create a temporary directory for the test
    test_path = Path("/tmp/test_post")
    test_path.mkdir(exist_ok=True)
    
    # Create jobs from the post
    jobs = await create_job_from_post(post, test_path, dump_post_data=False)
    
    # Verify that we have jobs created
    assert len(jobs) == 2  # One attachment and one file
    
    # Check attachment job
    attachment_job = next(job for job in jobs if job.type == PostFileTypeEnum.Attachment)
    assert attachment_job.post_id == "test_post_123"
    assert attachment_job.post_title == "Test Post Title"
    assert attachment_job.post_service == "patreon"
    assert attachment_job.post_user == "test_user"
    
    # Check file job
    file_job = next(job for job in jobs if job.type == PostFileTypeEnum.File)
    assert file_job.post_id == "test_post_123"
    assert file_job.post_title == "Test Post Title"
    assert file_job.post_service == "patreon"
    assert file_job.post_user == "test_user"
    
    # Clean up
    import shutil
    shutil.rmtree(test_path, ignore_errors=True)


def test_job_model_with_post_context():
    """Test that Job model can store post context information"""
    job = Job(
        path=Path("/tmp/test"),
        alt_filename="test.jpg",
        server_path="/files/test.jpg",
        type=PostFileTypeEnum.Attachment,
        post_id="123",
        post_title="Test Title",
        post_service="patreon",
        post_user="testuser"
    )
    
    assert job.post_id == "123"
    assert job.post_title == "Test Title"
    assert job.post_service == "patreon"
    assert job.post_user == "testuser"


def test_job_model_without_post_context():
    """Test that Job model works without post context (backward compatibility)"""
    job = Job(
        path=Path("/tmp/test"),
        alt_filename="test.jpg",
        server_path="/files/test.jpg",
        type=PostFileTypeEnum.Attachment
    )
    
    assert job.post_id is None
    assert job.post_title is None
    assert job.post_service is None
    assert job.post_user is None