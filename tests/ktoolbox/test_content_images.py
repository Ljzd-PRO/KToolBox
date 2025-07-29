"""
Tests for content image parsing functionality
"""
import pytest
from pathlib import Path
from ktoolbox.action.job import create_job_from_post
from ktoolbox.api.model import Post, Attachment
from ktoolbox.action.utils import extract_content_images
from ktoolbox.configuration import config


class TestContentImageParsing:
    """Test content image parsing functionality"""
    
    def test_extract_content_images_basic(self):
        """Test basic HTML content image extraction"""
        html_content = '<p><img src="/e9/a1/test.png"></p><p>Some text</p><p><img src="/another/image.jpg"></p>'
        
        image_sources = extract_content_images(html_content)
        
        assert len(image_sources) == 2
        assert "/e9/a1/test.png" in image_sources
        assert "/another/image.jpg" in image_sources
    
    def test_extract_content_images_empty(self):
        """Test extraction with empty or None content"""
        assert extract_content_images("") == []
        assert extract_content_images(None) == []
    
    def test_extract_content_images_no_images(self):
        """Test extraction with content that has no images"""
        html_content = '<p>Just some text</p><div>No images here</div>'
        
        image_sources = extract_content_images(html_content)
        
        assert len(image_sources) == 0
    
    def test_extract_content_images_various_formats(self):
        """Test extraction with various image formats and attributes"""
        html_content = '''
        <img src="/path/to/image.png" alt="Test">
        <img src="/another/file.jpg" class="image">
        <img alt="No src">
        <img src="">
        <IMG SRC="/uppercase.gif">
        '''
        
        image_sources = extract_content_images(html_content)
        
        assert len(image_sources) == 3
        assert "/path/to/image.png" in image_sources
        assert "/another/file.jpg" in image_sources
        assert "/uppercase.gif" in image_sources
    
    @pytest.mark.asyncio
    async def test_create_job_from_post_with_content_images(self, tmp_path):
        """Test job creation from post with content images"""
        # Enable sequential filename for testing
        original_sequential = config.job.sequential_filename
        config.job.sequential_filename = True
        
        try:
            test_post = Post(
                id="test_123",
                user="test_user",
                service="patreon",
                title="Test Post",
                content='<p><img src="/e9/a1/test.png"></p><p><img src="/another/image.jpg"></p>',
                attachments=[],
                file=None
            )
            
            jobs = await create_job_from_post(test_post, tmp_path)
            
            # Should have 2 content image jobs
            assert len(jobs) == 2
            
            # All jobs should be content image jobs
            assert len(jobs) == 2
            
            # Check filenames and paths (unified counter, no content_ prefix)
            assert jobs[0].alt_filename == "1.png"
            assert jobs[0].server_path == "/e9/a1/test.png"
            assert jobs[1].alt_filename == "2.jpg"
            assert jobs[1].server_path == "/another/image.jpg"
            
        finally:
            config.job.sequential_filename = original_sequential
    
    @pytest.mark.asyncio
    async def test_create_job_with_attachments_and_content_images(self, tmp_path):
        """Test job creation with both attachments and content images"""
        # Enable sequential filename for testing
        original_sequential = config.job.sequential_filename
        config.job.sequential_filename = True
        
        try:
            test_post = Post(
                id="test_123",
                user="test_user",
                service="patreon",
                title="Test Post",
                content='<p><img src="/content/image1.png"></p>',
                attachments=[
                    Attachment(name="attachment1.jpg", path="/attachments/file1.jpg")
                ],
                file=None
            )
            
            jobs = await create_job_from_post(test_post, tmp_path)
            
            # Should have 1 attachment + 1 content image = 2 jobs
            assert len(jobs) == 2
            
            # Sort jobs by filename to ensure consistent ordering for testing
            jobs_sorted = sorted(jobs, key=lambda x: x.alt_filename)
            
            # Check attachment job (should be numbered 1)
            assert jobs_sorted[0].alt_filename == "1.jpg"
            assert jobs_sorted[0].server_path == "/attachments/file1.jpg"
            
            # Check content image job (should be numbered 2, following attachment)
            assert jobs_sorted[1].alt_filename == "2.png"
            assert jobs_sorted[1].server_path == "/content/image1.png"
            
        finally:
            config.job.sequential_filename = original_sequential
    
    @pytest.mark.asyncio
    async def test_create_job_non_sequential_filenames(self, tmp_path):
        """Test job creation with non-sequential filenames"""
        # Disable sequential filename
        original_sequential = config.job.sequential_filename
        config.job.sequential_filename = False
        
        try:
            test_post = Post(
                id="test_123",
                user="test_user",
                service="patreon",
                title="Test Post",
                content='<p><img src="/path/to/myimage.png"></p>',
                attachments=[],
                file=None
            )
            
            jobs = await create_job_from_post(test_post, tmp_path)
            
            assert len(jobs) == 1
            assert jobs[0].alt_filename == "myimage.png"
            assert jobs[0].server_path == "/path/to/myimage.png"
            
        finally:
            config.job.sequential_filename = original_sequential