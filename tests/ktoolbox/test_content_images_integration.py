"""
Integration test for content image extraction functionality
"""
import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from ktoolbox.action.job import create_job_from_post
from ktoolbox.api.model import Post
from ktoolbox.configuration import config


@pytest.mark.asyncio
async def test_create_job_from_post_with_content_images():
    """Test that create_job_from_post creates jobs for content images when enabled"""
    
    # Enable content image extraction
    original_extract_content_images = config.job.extract_content_images
    config.job.extract_content_images = True
    
    try:
        # Create a mock post with HTML content containing images
        mock_post = Post(
            id="test_post_123",
            user="test_user",
            service="patreon",
            title="Test Post",
            content='''
            <div>
                <p>Check out these images:</p>
                <img src="/data/66/83/image1.jpg" alt="Image 1">
                <img src="https://kemono.cr/data/12/34/image2.png" alt="Image 2">
                <a href="/data/78/90/linked_image.gif">Download Image</a>
            </div>
            ''',
            substring="Some content preview...",  # Indicates content exists
            attachments=[]  # No regular attachments
        )
        
        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            
            # Create jobs from the post
            jobs = await create_job_from_post(
                post=mock_post,
                post_path=post_path,
                post_dir=True,
                dump_post_data=True
            )
            
            # Check that content images directory was created
            content_images_path = post_path / config.job.post_structure.content_images
            assert content_images_path.exists()
            
            # Should have jobs for the content images
            content_image_jobs = [job for job in jobs if str(job.path).endswith("content_images")]
            assert len(content_image_jobs) == 3
            
            # Check the URLs in the jobs
            image_urls = {job.server_path for job in content_image_jobs}
            expected_urls = {
                "https://kemono.cr/patreon/data/66/83/image1.jpg",
                "https://kemono.cr/data/12/34/image2.png", 
                "https://kemono.cr/patreon/data/78/90/linked_image.gif"
            }
            assert image_urls == expected_urls
            
            # Check that filenames are generated properly
            filenames = {job.alt_filename for job in content_image_jobs}
            assert len(filenames) == 3  # Should have unique filenames
            
    finally:
        # Restore original configuration
        config.job.extract_content_images = original_extract_content_images


@pytest.mark.asyncio 
async def test_create_job_from_post_without_content_images():
    """Test that no content image jobs are created when feature is disabled"""
    
    # Ensure content image extraction is disabled
    original_extract_content_images = config.job.extract_content_images
    config.job.extract_content_images = False
    
    try:
        # Create a mock post with HTML content containing images
        mock_post = Post(
            id="test_post_456", 
            user="test_user",
            service="patreon",
            title="Test Post",
            content='''
            <div>
                <img src="/data/66/83/image1.jpg" alt="Image 1">
                <img src="/data/12/34/image2.png" alt="Image 2">
            </div>
            ''',
            substring="Some content preview...",
            attachments=[]
        )
        
        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            
            # Create jobs from the post
            jobs = await create_job_from_post(
                post=mock_post,
                post_path=post_path,
                post_dir=True,
                dump_post_data=True
            )
            
            # Should have no content image jobs
            content_image_jobs = [job for job in jobs if str(job.path).endswith("content_images")]
            assert len(content_image_jobs) == 0
            
            # Content images directory should not be created or should be empty
            content_images_path = post_path / config.job.post_structure.content_images
            if content_images_path.exists():
                assert len(list(content_images_path.iterdir())) == 0
                
    finally:
        # Restore original configuration
        config.job.extract_content_images = original_extract_content_images


@pytest.mark.asyncio
async def test_create_job_from_post_no_content():
    """Test that no content image jobs are created when post has no content"""
    
    # Enable content image extraction
    original_extract_content_images = config.job.extract_content_images
    config.job.extract_content_images = True
    
    try:
        # Create a mock post without content
        mock_post = Post(
            id="test_post_789",
            user="test_user", 
            service="patreon",
            title="Test Post",
            content=None,  # No content
            substring=None,  # No content preview either
            attachments=[]
        )
        
        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            post_path = Path(temp_dir) / "test_post"
            
            # Create jobs from the post
            jobs = await create_job_from_post(
                post=mock_post,
                post_path=post_path,
                post_dir=True,
                dump_post_data=True
            )
            
            # Should have no content image jobs since there's no content
            content_image_jobs = [job for job in jobs if str(job.path).endswith("content_images")]
            assert len(content_image_jobs) == 0
            
    finally:
        # Restore original configuration
        config.job.extract_content_images = original_extract_content_images