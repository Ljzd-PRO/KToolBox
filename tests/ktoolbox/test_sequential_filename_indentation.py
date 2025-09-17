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
                name="OriginalImage1.jpg",
                path="/data/12/34/OriginalImage1.jpg"
            ),
            Attachment(
                name="SomeDocument.pdf",
                path="/data/56/78/SomeDocument.pdf"
            ),
            Attachment(
                name="AnotherImage.png",
                path="/data/90/ab/AnotherImage.png"
            ),
            Attachment(
                name="VideoFile.mp4",
                path="/data/cd/ef/VideoFile.mp4"
            )
        ],
        file=File(
            name="cover.jpg",
            path="/data/kl/mn/cover.jpg"
        )
    )


class TestSequentialFilenameIndentation:
    """Test sequential filename indentation functionality."""

    def setup_method(self):
        """Setup test environment."""
        # Reset configuration to defaults
        config.job = JobConfiguration()

    @pytest.mark.asyncio
    async def test_sequential_filename_indentation_disabled_by_default(self, mock_post):
        """Test that sequential filename indentation is disabled by default."""
        config.job.sequential_filename = True
        config.job.sequential_filename_indentation = False

        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)

            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]

            # Expected: traditional sequential names without original filenames
            expected_names = ["1.jpg", "2.pdf", "3.png", "4.mp4"]
            actual_names = [job.alt_filename for job in attachment_jobs]
            assert actual_names == expected_names

    @pytest.mark.asyncio
    async def test_sequential_filename_indentation_enabled(self, mock_post):
        """Test that sequential filename indentation works when enabled."""
        config.job.sequential_filename = True
        config.job.sequential_filename_indentation = True

        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)

            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]

            # Expected: sequential numbers with original filenames
            expected_names = [
                "1_OriginalImage1.jpg",
                "2_SomeDocument.pdf", 
                "3_AnotherImage.png",
                "4_VideoFile.mp4"
            ]
            actual_names = [job.alt_filename for job in attachment_jobs]
            assert actual_names == expected_names

    @pytest.mark.asyncio
    async def test_sequential_filename_indentation_without_sequential_filename(self, mock_post):
        """Test that indentation setting has no effect when sequential_filename is disabled."""
        config.job.sequential_filename = False
        config.job.sequential_filename_indentation = True

        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)

            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]

            # Expected: original filenames unchanged
            expected_names = [
                "OriginalImage1.jpg",
                "SomeDocument.pdf",
                "AnotherImage.png", 
                "VideoFile.mp4"
            ]
            actual_names = [job.alt_filename for job in attachment_jobs]
            assert actual_names == expected_names

    @pytest.mark.asyncio
    async def test_sequential_filename_indentation_with_excludes(self, mock_post):
        """Test sequential filename indentation with excludes."""
        config.job.sequential_filename = True
        config.job.sequential_filename_indentation = True
        config.job.sequential_filename_excludes = {".pdf", ".mp4"}

        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)

            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]

            # Expected: sequential with indentation for non-excluded, original for excluded
            expected_names = [
                "1_OriginalImage1.jpg",
                "SomeDocument.pdf",  # excluded from sequential
                "2_AnotherImage.png",
                "VideoFile.mp4"  # excluded from sequential
            ]
            actual_names = [job.alt_filename for job in attachment_jobs]
            assert actual_names == expected_names

    @pytest.mark.asyncio
    async def test_sequential_filename_indentation_with_filename_format(self, mock_post):
        """Test sequential filename indentation with custom filename format."""
        config.job.sequential_filename = True
        config.job.sequential_filename_indentation = True
        config.job.filename_format = "[{published}]_{}"

        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(mock_post, post_path, dump_post_data=False)

            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]

            # Expected: custom format applied to sequential indented filenames
            expected_names = [
                "[2024-01-01]_1_OriginalImage1.jpg",
                "[2024-01-01]_2_SomeDocument.pdf",
                "[2024-01-01]_3_AnotherImage.png",
                "[2024-01-01]_4_VideoFile.mp4"
            ]
            actual_names = [job.alt_filename for job in attachment_jobs]
            assert actual_names == expected_names

    @pytest.mark.asyncio
    async def test_sequential_filename_indentation_with_complex_original_names(self, mock_post):
        """Test sequential filename indentation with complex original filenames."""
        # Create a post with complex filenames
        complex_post = Post(
            id="test_post_456",
            user="test_user",
            service="patreon",
            title="Test Post",
            content="Test content",
            published=datetime(2024, 1, 1),
            added=datetime(2024, 1, 1),
            edited=datetime(2024, 1, 1),
            attachments=[
                Attachment(
                    name="File With Spaces.jpg",
                    path="/data/12/34/File With Spaces.jpg"
                ),
                Attachment(
                    name="File-With-Dashes.png",
                    path="/data/56/78/File-With-Dashes.png"
                ),
                Attachment(
                    name="File_With_Underscores.gif",
                    path="/data/90/ab/File_With_Underscores.gif"
                )
            ],
            file=None
        )

        config.job.sequential_filename = True
        config.job.sequential_filename_indentation = True

        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(complex_post, post_path, dump_post_data=False)

            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]

            # Expected: sequential numbers with original complex filenames preserved
            expected_names = [
                "1_File With Spaces.jpg",
                "2_File-With-Dashes.png",
                "3_File_With_Underscores.gif"
            ]
            actual_names = [job.alt_filename for job in attachment_jobs]
            assert actual_names == expected_names

    @pytest.mark.asyncio
    async def test_sequential_filename_indentation_with_no_extension_files(self, mock_post):
        """Test sequential filename indentation with files that have no extension."""
        # Create a post with files without extensions
        no_ext_post = Post(
            id="test_post_789",
            user="test_user",
            service="patreon",
            title="Test Post",
            content="Test content",
            published=datetime(2024, 1, 1),
            added=datetime(2024, 1, 1),
            edited=datetime(2024, 1, 1),
            attachments=[
                Attachment(
                    name="README",
                    path="/data/12/34/README"
                ),
                Attachment(
                    name="Makefile",
                    path="/data/56/78/Makefile"
                )
            ],
            file=None
        )

        config.job.sequential_filename = True
        config.job.sequential_filename_indentation = True

        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            jobs = await create_job_from_post(no_ext_post, post_path, dump_post_data=False)

            attachment_jobs = [job for job in jobs if job.type == PostFileTypeEnum.Attachment]

            # Expected: sequential numbers with original filenames (no extension)
            expected_names = [
                "1_README",
                "2_Makefile"
            ]
            actual_names = [job.alt_filename for job in attachment_jobs]
            assert actual_names == expected_names