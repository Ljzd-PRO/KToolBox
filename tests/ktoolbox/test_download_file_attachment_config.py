import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from ktoolbox._enum import PostFileTypeEnum
from ktoolbox.action.job import create_job_from_post
from ktoolbox.api.model import Post, Attachment, File
from ktoolbox.configuration import config, JobConfiguration


@pytest.fixture
def mock_post():
    """Create a mock post with both file and attachments."""
    return Post(
        id="test_post_123",
        user="test_user",
        service="patreon",
        title="Test Post",
        content="Test content",
        published=datetime(2024, 1, 1),
        added=datetime(2024, 1, 1),
        edited=datetime(2024, 1, 1),
        attachments=[
            Attachment(
                name="image1.jpg",
                path="/data/12/34/image1.jpg"
            ),
            Attachment(
                name="image2.png",
                path="/data/56/78/image2.png"
            )
        ],
        file=File(
            name="cover.jpg",
            path="/data/ab/cd/cover.jpg"
        )
    )


@pytest.mark.asyncio
async def test_download_file_enabled(mock_post):
    """Test that file is downloaded when download_file is True (default)."""
    # Save original config
    original_download_file = config.job.download_file
    original_download_attachments = config.job.download_attachments
    
    try:
        # Ensure both are enabled
        config.job.download_file = True
        config.job.download_attachments = True
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            jobs = await create_job_from_post(mock_post, temp_path)
            
            # Should have 3 jobs: 2 attachments + 1 file
            assert len(jobs) == 3
            
            # Check that we have both file and attachment jobs
            file_jobs = [job for job in jobs if job.type == PostFileTypeEnum.File]
            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            assert len(file_jobs) == 1
            assert len(attachment_jobs) == 2
            
            # Verify the file job properties
            file_job = file_jobs[0]
            assert "cover.jpg" in file_job.alt_filename
            assert file_job.server_path == "/data/ab/cd/cover.jpg"
    
    finally:
        # Restore original config
        config.job.download_file = original_download_file
        config.job.download_attachments = original_download_attachments


@pytest.mark.asyncio
async def test_download_file_disabled(mock_post):
    """Test that file is not downloaded when download_file is False."""
    # Save original config
    original_download_file = config.job.download_file
    original_download_attachments = config.job.download_attachments
    
    try:
        # Disable file download, keep attachments enabled
        config.job.download_file = False
        config.job.download_attachments = True
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            jobs = await create_job_from_post(mock_post, temp_path)
            
            # Should have 2 jobs: 2 attachments only
            assert len(jobs) == 2
            
            # Check that we have only attachment jobs
            file_jobs = [job for job in jobs if job.type == PostFileTypeEnum.File]
            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            assert len(file_jobs) == 0
            assert len(attachment_jobs) == 2
    
    finally:
        # Restore original config
        config.job.download_file = original_download_file
        config.job.download_attachments = original_download_attachments


@pytest.mark.asyncio
async def test_download_attachments_disabled(mock_post):
    """Test that attachments are not downloaded when download_attachments is False."""
    # Save original config
    original_download_file = config.job.download_file
    original_download_attachments = config.job.download_attachments
    
    try:
        # Enable file download, disable attachments
        config.job.download_file = True
        config.job.download_attachments = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            jobs = await create_job_from_post(mock_post, temp_path)
            
            # Should have 1 job: 1 file only
            assert len(jobs) == 1
            
            # Check that we have only file job
            file_jobs = [job for job in jobs if job.type == PostFileTypeEnum.File]
            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            assert len(file_jobs) == 1
            assert len(attachment_jobs) == 0
            
            # Verify the file job properties
            file_job = file_jobs[0]
            assert "cover.jpg" in file_job.alt_filename
            assert file_job.server_path == "/data/ab/cd/cover.jpg"
    
    finally:
        # Restore original config
        config.job.download_file = original_download_file
        config.job.download_attachments = original_download_attachments


@pytest.mark.asyncio
async def test_both_disabled(mock_post):
    """Test that no downloads occur when both options are disabled."""
    # Save original config
    original_download_file = config.job.download_file
    original_download_attachments = config.job.download_attachments
    
    try:
        # Disable both
        config.job.download_file = False
        config.job.download_attachments = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            jobs = await create_job_from_post(mock_post, temp_path)
            
            # Should have 0 download jobs
            download_jobs = [job for job in jobs if job.type in [PostFileTypeEnum.File, PostFileTypeEnum.Attachment]]
            assert len(download_jobs) == 0
    
    finally:
        # Restore original config
        config.job.download_file = original_download_file
        config.job.download_attachments = original_download_attachments