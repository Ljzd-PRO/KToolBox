import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock
from typing import Optional

import pytest

from ktoolbox.action.job import create_job_from_post, _should_filter_by_size
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


class TestBasicFileSizeFilter:
    """Basic file size filtering tests."""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset config before each test."""
        config.job.min_file_size = None
        config.job.max_file_size = None
        config.job.download_attachments = True
        config.job.download_file = True
        yield

    @pytest.mark.asyncio
    async def test_no_size_filtering_without_client(self, mock_post):
        """Test that without client, no size filtering occurs."""
        config.job.max_file_size = 1000000  # 1MB
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False, client=None)
            
            # Should have all 3 jobs regardless of size limits (no client = no filtering)
            assert len(jobs) == 3
            job_filenames = {job.alt_filename for job in jobs}
            assert "image.jpg" in job_filenames
            assert "video.mp4" in job_filenames
            assert "test_post_123_cover.jpg" in job_filenames  # Post file gets prefixed with ID

    @pytest.mark.asyncio
    async def test_no_size_filtering_without_limits(self, mock_post):
        """Test that without size limits, no filtering occurs."""
        # No size limits configured
        mock_client = AsyncMock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False, client=mock_client)
            
            # Should have all 3 jobs
            assert len(jobs) == 3

    @pytest.mark.asyncio
    async def test_should_filter_by_size_no_limits(self):
        """Test filtering function with no size limits."""
        mock_client = AsyncMock()
        result = await _should_filter_by_size("/test/file.jpg", mock_client)
        assert result is False

    @pytest.mark.asyncio
    async def test_should_filter_by_size_no_client(self):
        """Test filtering function with no client."""
        config.job.max_file_size = 1000000
        result = await _should_filter_by_size("/test/file.jpg", None)
        assert result is False