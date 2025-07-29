import tempfile
from datetime import datetime
from pathlib import Path
from typing import Set

import pytest

from ktoolbox.action.job import create_job_from_post
from ktoolbox.api.model import Post, Attachment, File
from ktoolbox.configuration import config, JobConfiguration, PostStructureConfiguration
from ktoolbox._enum import PostFileTypeEnum


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
                name="image1.jpg",
                path="/data/12/34/image1.jpg"
            ),
            Attachment(
                name="document.psd", 
                path="/data/56/78/document.psd"
            ),
            Attachment(
                name="archive.zip",
                path="/data/90/ab/archive.zip"
            ),
            Attachment(
                name="video.mp4",
                path="/data/cd/ef/video.mp4"
            ),
            Attachment(
                name="image2.png",
                path="/data/gh/ij/image2.png"
            )
        ],
        file=File(
            name="cover.jpg",
            path="/data/kl/mn/cover.jpg"
        )
    )


class TestSequentialFilenameExcludes:
    """Test sequential filename with excludes functionality."""

    def setup_method(self):
        """Setup test environment."""
        # Reset config to defaults
        config.job = JobConfiguration()

    @pytest.mark.asyncio
    async def test_sequential_filename_disabled(self, mock_post):
        """Test that original names are preserved when sequential_filename is False."""
        config.job.sequential_filename = False
        config.job.sequential_filename_excludes = {".psd", ".zip"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)
            
            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            # All attachments should keep original names
            expected_names = ["image1.jpg", "document.psd", "archive.zip", "video.mp4", "image2.png"]
            actual_names = [job.alt_filename for job in attachment_jobs]
            assert sorted(actual_names) == sorted(expected_names)

    @pytest.mark.asyncio
    async def test_sequential_filename_enabled_no_excludes(self, mock_post):
        """Test that all attachments get sequential names when no excludes are set."""
        config.job.sequential_filename = True
        config.job.sequential_filename_excludes = set()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)
            
            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            # All attachments should get sequential names
            expected_names = ["1.jpg", "2.psd", "3.zip", "4.mp4", "5.png"]
            actual_names = [job.alt_filename for job in attachment_jobs]
            assert actual_names == expected_names

    @pytest.mark.asyncio
    async def test_sequential_filename_with_excludes(self, mock_post):
        """Test that excluded extensions preserve original names while others get sequential."""
        config.job.sequential_filename = True
        config.job.sequential_filename_excludes = {".psd", ".zip", ".mp4"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)
            
            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            # Expected: images get sequential names, excluded types keep original names
            expected_names = ["1.jpg", "document.psd", "archive.zip", "video.mp4", "2.png"]
            actual_names = [job.alt_filename for job in attachment_jobs]
            assert actual_names == expected_names

    @pytest.mark.asyncio 
    async def test_sequential_filename_case_insensitive_excludes(self, mock_post):
        """Test that excludes work with different case extensions."""
        # Modify post to have uppercase extensions
        mock_post.attachments[1].name = "document.PSD"
        mock_post.attachments[2].name = "archive.ZIP"
        
        config.job.sequential_filename = True
        config.job.sequential_filename_excludes = {".psd", ".zip"}  # lowercase excludes
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)
            
            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            # Expected: uppercase extensions should also be excluded (case insensitive)
            expected_names = ["1.jpg", "document.PSD", "archive.ZIP", "2.mp4", "3.png"]
            actual_names = [job.alt_filename for job in attachment_jobs]
            assert actual_names == expected_names

    @pytest.mark.asyncio
    async def test_sequential_filename_with_filename_format(self, mock_post):
        """Test that filename_format works correctly with sequential_filename_excludes."""
        config.job.sequential_filename = True
        config.job.sequential_filename_excludes = {".psd", ".zip"}
        config.job.filename_format = "[{published}]_{}"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)
            
            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            # Expected: formatted names with sequential for non-excluded, original for excluded
            expected_names = [
                "[2024-01-01]_1.jpg",
                "[2024-01-01]_document.psd", 
                "[2024-01-01]_archive.zip",
                "[2024-01-01]_2.mp4",
                "[2024-01-01]_3.png"
            ]
            actual_names = [job.alt_filename for job in attachment_jobs]
            assert actual_names == expected_names

    @pytest.mark.asyncio
    async def test_file_type_not_affected_by_excludes(self, mock_post):
        """Test that Post.file is not affected by sequential_filename_excludes."""
        config.job.sequential_filename = True
        config.job.sequential_filename_excludes = {".jpg"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)
            
            file_jobs = [job for job in jobs if job.type == PostFileTypeEnum.File]
            
            # File should always keep original name (with post ID prefix)
            assert len(file_jobs) == 1
            assert file_jobs[0].alt_filename == "test_post_123_cover.jpg"

    @pytest.mark.asyncio
    async def test_empty_excludes_set(self, mock_post):
        """Test behavior with explicitly empty excludes set."""
        config.job.sequential_filename = True
        config.job.sequential_filename_excludes = set()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)
            
            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            # All should get sequential names
            expected_names = ["1.jpg", "2.psd", "3.zip", "4.mp4", "5.png"]
            actual_names = [job.alt_filename for job in attachment_jobs]
            assert actual_names == expected_names

    @pytest.mark.asyncio
    async def test_all_extensions_excluded(self, mock_post):
        """Test behavior when all attachment extensions are excluded."""
        config.job.sequential_filename = True
        config.job.sequential_filename_excludes = {".jpg", ".psd", ".zip", ".mp4", ".png"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)
            
            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            # All should keep original names
            expected_names = ["image1.jpg", "document.psd", "archive.zip", "video.mp4", "image2.png"]
            actual_names = [job.alt_filename for job in attachment_jobs]
            assert sorted(actual_names) == sorted(expected_names)

    @pytest.mark.asyncio
    async def test_extensions_with_and_without_dot(self, mock_post):
        """Test that extensions work whether specified with or without leading dot."""
        # This tests the current implementation which expects dots in the config
        config.job.sequential_filename = True
        config.job.sequential_filename_excludes = {".psd", "zip"}  # mixed with/without dot
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)
            
            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            # Only .psd should be excluded, not .zip (because "zip" != ".zip")
            expected_names = ["1.jpg", "document.psd", "2.zip", "3.mp4", "4.png"]
            actual_names = [job.alt_filename for job in attachment_jobs]
            assert actual_names == expected_names