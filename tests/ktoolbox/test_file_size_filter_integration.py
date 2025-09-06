import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from ktoolbox.action.job import create_job_from_post
from ktoolbox.api.model import Post, Attachment, File
from ktoolbox.configuration import config


@pytest.fixture
def mock_post():
    """Create a simple mock post."""
    return Post(
        id="test_post_123",
        user="test_user",
        service="patreon",
        title="Test Post",
        published=datetime(2024, 1, 1),
        attachments=[
            Attachment(name="image.jpg", path="/data/12/34/image.jpg"),
            Attachment(name="video.mp4", path="/data/56/78/video.mp4")
        ],
        file=File(name="cover.jpg", path="/data/kl/mn/cover.jpg")
    )


class TestFileSizeFilterIntegration:
    """Test that file size filtering is deferred to download time."""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset config before each test."""
        config.job.min_file_size = None
        config.job.max_file_size = None
        config.job.download_attachments = True
        config.job.download_file = True
        yield

    @pytest.mark.asyncio
    async def test_jobs_created_regardless_of_size_limits(self, mock_post):
        """Test that jobs are created regardless of configured size limits."""
        # Set aggressive size limits
        config.job.min_file_size = 999999999  # 999MB minimum
        config.job.max_file_size = 1000       # 1KB maximum (impossible)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)
            
            # Should still create all 3 jobs (filtering happens at download time)
            assert len(jobs) == 3
            job_filenames = {job.alt_filename for job in jobs}
            assert "image.jpg" in job_filenames
            assert "video.mp4" in job_filenames
            assert "test_post_123_cover.jpg" in job_filenames  # Post file gets prefixed with ID

    @pytest.mark.asyncio
    async def test_jobs_created_without_size_limits(self, mock_post):
        """Test that jobs are created when no size limits are configured."""
        # No size limits configured
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)
            
            # Should create all 3 jobs
            assert len(jobs) == 3
            job_filenames = {job.alt_filename for job in jobs}
            assert "image.jpg" in job_filenames
            assert "video.mp4" in job_filenames
            assert "test_post_123_cover.jpg" in job_filenames