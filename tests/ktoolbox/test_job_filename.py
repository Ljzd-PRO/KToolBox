import tempfile
from pathlib import Path
from unittest.mock import Mock
from datetime import datetime

import pytest

from ktoolbox.action.job import create_job_from_post
from ktoolbox.api.model import Post, Attachment, File
from ktoolbox.configuration import config


@pytest.fixture
def sample_post():
    """Create a sample post with multiple attachments having the same filename"""
    return Post(
        id="test123",
        user="testuser",
        service="fanbox",
        title="Test Post",
        content="Test content",
        added=datetime(2024, 1, 1),
        published=datetime(2024, 1, 1),
        edited=datetime(2024, 1, 1),
        attachments=[
            Attachment(name="image.png", path="/data/1/image.png"),
            Attachment(name="image.png", path="/data/2/image.png"),
            Attachment(name="image.png", path="/data/3/image.png"),
            Attachment(name="document.pdf", path="/data/4/document.pdf"),
            Attachment(name="document.pdf", path="/data/5/document.pdf"),
        ],
        file=File(name="cover.jpg", path="/data/cover.jpg")
    )


@pytest.mark.asyncio
async def test_prefix_sequence_to_filename_enabled(sample_post):
    """Test that prefix_sequence_to_filename generates correct filenames"""
    # Store original config values
    original_sequential = config.job.sequential_filename
    original_prefix = config.job.prefix_sequence_to_filename
    original_format = config.job.filename_format
    
    try:
        # Set configuration for prefix sequence
        config.job.sequential_filename = False
        config.job.prefix_sequence_to_filename = True
        config.job.filename_format = "{}"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir)
            jobs = await create_job_from_post(sample_post, post_path)
            
            # Should have 5 attachment jobs + 1 file job
            assert len(jobs) == 6
            
            # Check attachment filenames
            attachment_jobs = [job for job in jobs if "cover.jpg" not in job.alt_filename]
            expected_filenames = [
                "1_image.png",
                "2_image.png", 
                "3_image.png",
                "4_document.pdf",
                "5_document.pdf"
            ]
            
            actual_filenames = [job.alt_filename for job in attachment_jobs]
            assert actual_filenames == expected_filenames
            
    finally:
        # Restore original config values
        config.job.sequential_filename = original_sequential
        config.job.prefix_sequence_to_filename = original_prefix
        config.job.filename_format = original_format


@pytest.mark.asyncio
async def test_sequential_filename_takes_precedence(sample_post):
    """Test that sequential_filename takes precedence over prefix_sequence_to_filename"""
    # Store original config values
    original_sequential = config.job.sequential_filename
    original_prefix = config.job.prefix_sequence_to_filename
    original_format = config.job.filename_format
    
    try:
        # Set both options to True
        config.job.sequential_filename = True
        config.job.prefix_sequence_to_filename = True
        config.job.filename_format = "{}"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir)
            jobs = await create_job_from_post(sample_post, post_path)
            
            # Check attachment filenames - should follow sequential pattern
            attachment_jobs = [job for job in jobs if "cover.jpg" not in job.alt_filename]
            expected_filenames = [
                "1.png",
                "2.png", 
                "3.png",
                "4.pdf",
                "5.pdf"
            ]
            
            actual_filenames = [job.alt_filename for job in attachment_jobs]
            assert actual_filenames == expected_filenames
            
    finally:
        # Restore original config values
        config.job.sequential_filename = original_sequential
        config.job.prefix_sequence_to_filename = original_prefix
        config.job.filename_format = original_format


@pytest.mark.asyncio
async def test_prefix_sequence_with_filename_format(sample_post):
    """Test prefix_sequence_to_filename works with filename_format"""
    # Store original config values
    original_sequential = config.job.sequential_filename
    original_prefix = config.job.prefix_sequence_to_filename
    original_format = config.job.filename_format
    
    try:
        # Set configuration for prefix sequence with custom format
        config.job.sequential_filename = False
        config.job.prefix_sequence_to_filename = True
        config.job.filename_format = "[{published}]_{}"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir)
            jobs = await create_job_from_post(sample_post, post_path)
            
            # Check attachment filenames with custom format
            attachment_jobs = [job for job in jobs if "[2024-01-01]" in job.alt_filename]
            expected_filenames = [
                "[2024-01-01]_1_image.png",
                "[2024-01-01]_2_image.png", 
                "[2024-01-01]_3_image.png",
                "[2024-01-01]_4_document.pdf",
                "[2024-01-01]_5_document.pdf"
            ]
            
            actual_filenames = [job.alt_filename for job in attachment_jobs]
            assert actual_filenames == expected_filenames
            
    finally:
        # Restore original config values
        config.job.sequential_filename = original_sequential
        config.job.prefix_sequence_to_filename = original_prefix
        config.job.filename_format = original_format


@pytest.mark.asyncio
async def test_default_behavior_unchanged(sample_post):
    """Test that default behavior is unchanged when new option is disabled"""
    # Store original config values
    original_sequential = config.job.sequential_filename
    original_prefix = config.job.prefix_sequence_to_filename
    original_format = config.job.filename_format
    
    try:
        # Set default configuration
        config.job.sequential_filename = False
        config.job.prefix_sequence_to_filename = False
        config.job.filename_format = "{}"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir)
            jobs = await create_job_from_post(sample_post, post_path)
            
            # Should preserve original filenames
            attachment_jobs = [job for job in jobs if "cover.jpg" not in job.alt_filename]
            expected_filenames = [
                "image.png",
                "image.png", 
                "image.png",
                "document.pdf",
                "document.pdf"
            ]
            
            actual_filenames = [job.alt_filename for job in attachment_jobs]
            assert actual_filenames == expected_filenames
            
    finally:
        # Restore original config values
        config.job.sequential_filename = original_sequential
        config.job.prefix_sequence_to_filename = original_prefix
        config.job.filename_format = original_format