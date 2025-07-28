"""Test metadata preservation functionality"""
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from ktoolbox.api.model import Post, File, Attachment
from ktoolbox.action.job import create_job_from_post


class TestMetadataPreservation:
    """Test cases for metadata preservation functionality"""

    @pytest.mark.asyncio
    async def test_published_date_passed_to_job(self):
        """Test that published date is correctly passed from Post to Job"""
        published_date = datetime(2024, 4, 3, 12, 30, 45)
        
        post = Post(
            id="test123",
            title="Test Post",
            published=published_date,
            attachments=[
                Attachment(name="test.png", path="/test/path/test.png")
            ],
            file=File(name="main.jpg", path="/test/path/main.jpg")
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(post, post_path, dump_post_data=False)
            
            assert len(jobs) == 2  # One for attachment, one for file
            for job in jobs:
                assert job.published == published_date

    @pytest.mark.asyncio
    async def test_fallback_to_added_date(self):
        """Test that added date is used when published date is None"""
        added_date = datetime(2024, 5, 1, 10, 15, 30)
        
        post = Post(
            id="test456",
            title="Test Post",
            published=None,
            added=added_date,
            attachments=[],
            file=File(name="main.jpg", path="/test/path/main.jpg")
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(post, post_path, dump_post_data=False)
            
            assert len(jobs) == 1
            assert jobs[0].published == added_date

    @pytest.mark.asyncio
    async def test_none_date_handling(self):
        """Test behavior when both published and added dates are None"""
        post = Post(
            id="test789",
            title="Test Post",
            published=None,
            added=None,
            attachments=[],
            file=File(name="main.jpg", path="/test/path/main.jpg")
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(post, post_path, dump_post_data=False)
            
            assert len(jobs) == 1
            assert jobs[0].published is None