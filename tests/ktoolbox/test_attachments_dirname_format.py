import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from ktoolbox._enum import PostFileTypeEnum
from ktoolbox.action.job import create_job_from_post
from ktoolbox.api.model import Post, Attachment, File
from ktoolbox.configuration import config, JobConfiguration, PostStructureConfiguration


@pytest.fixture
def mock_post():
    """Create a mock post for testing."""
    return Post(
        id="test_post_123",
        user="test_user",
        service="patreon",
        title="Test Post Title",
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
            path="/data/kl/mn/cover.jpg"
        )
    )


class TestAttachmentsDirnameFormat:
    """Test attachments directory naming format functionality."""

    def setup_method(self):
        """Setup test environment."""
        # Reset configuration to defaults
        config.job = JobConfiguration()
        config.job.post_structure = PostStructureConfiguration()

    @pytest.mark.asyncio
    async def test_default_attachments_dirname(self, mock_post):
        """Test that default attachments directory name is used when format is default."""
        config.job.post_structure.attachments_dirname_format = "attachments"

        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)

            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            # Check that all attachment jobs use the default attachments directory
            for job in attachment_jobs:
                assert job.path.name == "attachments"

    @pytest.mark.asyncio
    async def test_custom_attachments_dirname_with_title(self, mock_post):
        """Test custom attachments directory naming using post title."""
        config.job.post_structure.attachments_dirname_format = "{title}"

        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)

            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            # Check that all attachment jobs use the custom directory name
            for job in attachment_jobs:
                assert job.path.name == "Test Post Title"

    @pytest.mark.asyncio
    async def test_custom_attachments_dirname_with_id(self, mock_post):
        """Test custom attachments directory naming using post id."""
        config.job.post_structure.attachments_dirname_format = "{id}"

        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)

            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            # Check that all attachment jobs use the custom directory name
            for job in attachment_jobs:
                assert job.path.name == "test_post_123"

    @pytest.mark.asyncio
    async def test_custom_attachments_dirname_with_combined_format(self, mock_post):
        """Test custom attachments directory naming using combined format."""
        config.job.post_structure.attachments_dirname_format = "{id}_{title}"

        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)

            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            # Check that all attachment jobs use the custom directory name
            for job in attachment_jobs:
                assert job.path.name == "test_post_123_Test Post Title"

    @pytest.mark.asyncio
    async def test_custom_attachments_dirname_with_date_format(self, mock_post):
        """Test custom attachments directory naming using date formatting."""
        config.job.post_structure.attachments_dirname_format = "{published}_{title}"

        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)

            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            # Check that all attachment jobs use the custom directory name with formatted date
            for job in attachment_jobs:
                assert job.path.name == "2024-01-01_Test Post Title"

    @pytest.mark.asyncio
    async def test_custom_attachments_dirname_with_format_specification(self, mock_post):
        """Test custom attachments directory naming using Python format specification."""
        config.job.post_structure.attachments_dirname_format = "{title:.6}"

        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)

            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            # Check that all attachment jobs use the truncated title
            for job in attachment_jobs:
                assert job.path.name == "Test P"  # First 6 characters of "Test Post Title"

    @pytest.mark.asyncio
    async def test_attachments_dirname_format_when_mix_posts_enabled(self, mock_post):
        """Test that attachments dirname format doesn't affect behavior when mix_posts is enabled."""
        config.job.mix_posts = True
        config.job.post_structure.attachments_dirname_format = "{title}"

        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, post_dir=False, dump_post_data=False)

            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]
            
            # When mix_posts is enabled and post_dir=False, attachments go directly to post_path
            for job in attachment_jobs:
                assert job.path == post_path

    @pytest.mark.asyncio
    async def test_attachments_path_creation(self, mock_post):
        """Test that the custom attachments directory is actually created."""
        config.job.post_structure.attachments_dirname_format = "{title}"

        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            await create_job_from_post(mock_post, post_path, dump_post_data=False)

            # Check that the custom directory was created
            expected_attachments_path = post_path / "Test Post Title"
            assert expected_attachments_path.exists()
            assert expected_attachments_path.is_dir()