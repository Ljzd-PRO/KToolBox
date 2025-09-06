import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from typing import Optional

import pytest
import httpx

from ktoolbox._enum import PostFileTypeEnum
from ktoolbox.action.job import create_job_from_post, _should_filter_by_size
from ktoolbox.api.model import Post, Attachment, File
from ktoolbox.configuration import config, JobConfiguration
from ktoolbox.utils import get_file_size


@pytest.fixture
def mock_post():
    """Create a mock post with various attachment types."""
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
                name="small_image.jpg",
                path="/data/12/34/small_image.jpg"  # Will mock as 100KB
            ),
            Attachment(
                name="large_video.mp4",
                path="/data/56/78/large_video.mp4"  # Will mock as 100MB
            ),
            Attachment(
                name="medium_document.pdf",
                path="/data/90/ab/medium_document.pdf"  # Will mock as 10MB
            )
        ],
        file=File(
            name="cover.jpg",
            path="/data/kl/mn/cover.jpg"  # Will mock as 500KB
        )
    )


@pytest.fixture
def mock_client():
    """Create a mock HTTP client."""
    return Mock(spec=httpx.AsyncClient)


class TestFileSizeFilter:
    """Test file size filtering functionality."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Save original config
        original_config = JobConfiguration.model_validate(config.job.model_dump())
        
        # Reset to defaults before each test
        config.job.min_file_size = None
        config.job.max_file_size = None
        config.job.sequential_filename = False
        config.job.allow_list = set()
        config.job.block_list = set()
        config.job.download_attachments = True
        config.job.download_file = True
        
        yield
        
        # Restore original config
        for field, value in original_config.model_dump().items():
            setattr(config.job, field, value)

    @pytest.mark.asyncio
    async def test_get_file_size_success(self):
        """Test successful file size retrieval via Content-Length header."""
        mock_client = Mock(spec=httpx.AsyncClient)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Length": "1048576"}  # 1MB
        mock_client.head = AsyncMock(return_value=mock_response)
        
        size = await get_file_size("https://example.com/file.jpg", mock_client)
        assert size == 1048576

    @pytest.mark.asyncio
    async def test_get_file_size_content_range_fallback(self):
        """Test file size retrieval via Content-Range when HEAD fails."""
        mock_client = Mock(spec=httpx.AsyncClient)
        
        # HEAD request returns no Content-Length
        head_response = Mock()
        head_response.status_code = 200
        head_response.headers = {}
        mock_client.head = AsyncMock(return_value=head_response)
        
        # GET request with Range returns Content-Range
        get_response = Mock()
        get_response.status_code = 206
        get_response.headers = {"Content-Range": "bytes 0-0/2097152"}  # 2MB total
        mock_client.get = AsyncMock(return_value=get_response)
        
        size = await get_file_size("https://example.com/file.jpg", mock_client)
        assert size == 2097152

    @pytest.mark.asyncio
    async def test_get_file_size_failure(self):
        """Test file size retrieval failure."""
        mock_client = Mock(spec=httpx.AsyncClient)
        mock_client.head = AsyncMock(side_effect=Exception("Network error"))
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))
        
        size = await get_file_size("https://example.com/file.jpg", mock_client)
        assert size is None

    @pytest.mark.asyncio
    async def test_should_filter_by_size_no_limits(self, mock_client):
        """Test that no filtering occurs when no size limits are configured."""
        # No size limits configured
        result = await _should_filter_by_size("/data/test/file.jpg", mock_client)
        assert result is False

    @pytest.mark.asyncio
    async def test_should_filter_by_size_no_client(self):
        """Test that no filtering occurs when no client is provided."""
        config.job.max_file_size = 1000000  # 1MB
        
        result = await _should_filter_by_size("/data/test/file.jpg", None)
        assert result is False

    @pytest.mark.asyncio
    async def test_should_filter_by_size_below_minimum(self, mock_client):
        """Test filtering out files below minimum size."""
        config.job.min_file_size = 1000000  # 1MB minimum
        
        # Mock get_file_size to return 500KB
        with pytest.MonkeyPatch.context() as m:
            m.setattr("ktoolbox.action.job.get_file_size", AsyncMock(return_value=500000))
            
            result = await _should_filter_by_size("/data/test/small_file.jpg", mock_client)
            assert result is True

    @pytest.mark.asyncio
    async def test_should_filter_by_size_above_maximum(self, mock_client):
        """Test filtering out files above maximum size."""
        config.job.max_file_size = 10000000  # 10MB maximum
        
        # Mock get_file_size to return 50MB
        with pytest.MonkeyPatch.context() as m:
            m.setattr("ktoolbox.action.job.get_file_size", AsyncMock(return_value=50000000))
            
            result = await _should_filter_by_size("/data/test/large_file.mp4", mock_client)
            assert result is True

    @pytest.mark.asyncio
    async def test_should_filter_by_size_within_range(self, mock_client):
        """Test that files within size range are not filtered."""
        config.job.min_file_size = 1000000   # 1MB minimum
        config.job.max_file_size = 10000000  # 10MB maximum
        
        # Mock get_file_size to return 5MB (within range)
        with pytest.MonkeyPatch.context() as m:
            m.setattr("ktoolbox.action.job.get_file_size", AsyncMock(return_value=5000000))
            
            result = await _should_filter_by_size("/data/test/medium_file.jpg", mock_client)
            assert result is False

    @pytest.mark.asyncio
    async def test_should_filter_by_size_unknown_size(self, mock_client):
        """Test that files with unknown size are not filtered."""
        config.job.max_file_size = 10000000  # 10MB maximum
        
        # Mock get_file_size to return None (unknown size)
        with pytest.MonkeyPatch.context() as m:
            m.setattr("ktoolbox.action.job.get_file_size", AsyncMock(return_value=None))
            
            result = await _should_filter_by_size("/data/test/unknown_file.jpg", mock_client)
            assert result is False

    @pytest.mark.asyncio
    async def test_create_job_with_size_filtering(self, mock_post, mock_client):
        """Test job creation with file size filtering enabled."""
        config.job.max_file_size = 5000000  # 5MB maximum
        
        # Mock file sizes: small_image=100KB, large_video=100MB, medium_document=10MB, cover=500KB
        def mock_get_file_size(url, client):
            if "small_image.jpg" in url:
                return AsyncMock(return_value=100000)()  # 100KB - should pass
            elif "large_video.mp4" in url:
                return AsyncMock(return_value=100000000)()  # 100MB - should be filtered
            elif "medium_document.pdf" in url:
                return AsyncMock(return_value=10000000)()  # 10MB - should be filtered
            elif "cover.jpg" in url:
                return AsyncMock(return_value=500000)()  # 500KB - should pass
            return AsyncMock(return_value=None)()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            
            with pytest.MonkeyPatch.context() as m:
                m.setattr("ktoolbox.action.job.get_file_size", mock_get_file_size)
                
                jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False, client=mock_client)
                
                # Should have 2 jobs: small_image.jpg (attachment) and cover.jpg (file)
                assert len(jobs) == 2
                
                # Check which files made it through
                job_filenames = {job.alt_filename for job in jobs}
                assert "small_image.jpg" in job_filenames
                assert "cover.jpg" in job_filenames
                
                # Verify filtered files are not present
                assert not any("large_video.mp4" in job.alt_filename for job in jobs)
                assert not any("medium_document.pdf" in job.alt_filename for job in jobs)

    @pytest.mark.asyncio
    async def test_create_job_without_size_filtering(self, mock_post):
        """Test job creation without size filtering (should include all files)."""
        # No size limits configured
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False, client=None)
            
            # Should have 4 jobs: 3 attachments + 1 file
            assert len(jobs) == 4
            
            # Check all files are included
            job_filenames = {job.alt_filename for job in jobs}
            assert "small_image.jpg" in job_filenames
            assert "large_video.mp4" in job_filenames
            assert "medium_document.pdf" in job_filenames
            assert "cover.jpg" in job_filenames

    @pytest.mark.asyncio 
    async def test_minimum_size_filtering(self, mock_post, mock_client):
        """Test filtering files below minimum size."""
        config.job.min_file_size = 1000000  # 1MB minimum
        
        # Mock file sizes: only medium_document (10MB) and large_video (100MB) should pass
        def mock_get_file_size(url, client):
            if "small_image.jpg" in url:
                return AsyncMock(return_value=100000)()  # 100KB - should be filtered
            elif "large_video.mp4" in url:
                return AsyncMock(return_value=100000000)()  # 100MB - should pass
            elif "medium_document.pdf" in url:
                return AsyncMock(return_value=10000000)()  # 10MB - should pass
            elif "cover.jpg" in url:
                return AsyncMock(return_value=500000)()  # 500KB - should be filtered
            return AsyncMock(return_value=None)()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            
            with pytest.MonkeyPatch.context() as m:
                m.setattr("ktoolbox.action.job.get_file_size", mock_get_file_size)
                
                jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False, client=mock_client)
                
                # Should have 2 jobs: large_video.mp4 and medium_document.pdf
                assert len(jobs) == 2
                
                job_filenames = {job.alt_filename for job in jobs}
                assert "large_video.mp4" in job_filenames
                assert "medium_document.pdf" in job_filenames
                
                # Verify small files are filtered
                assert not any("small_image.jpg" in job.alt_filename for job in jobs)
                assert not any("cover.jpg" in job.alt_filename for job in jobs)