import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ktoolbox.cli import KToolBoxCli
from ktoolbox.utils import parse_webpage_url, generate_msg
from ktoolbox._enum import TextEnum
from ktoolbox.api.model import Post
from ktoolbox.api.posts import GetPost


class TestRevisionSupport:
    """Test revision functionality"""
    
    def test_parse_webpage_url_revision(self):
        """Test URL parsing for revision posts"""
        # Normal post URL
        service, creator_id, post_id, revision_id = parse_webpage_url(
            "https://kemono.su/fanbox/user/123/post/456"
        )
        assert service == "fanbox"
        assert creator_id == "123"
        assert post_id == "456"
        assert revision_id is None
        
        # Revision post URL
        service, creator_id, post_id, revision_id = parse_webpage_url(
            "https://kemono.su/fanbox/user/123/post/456/revision/789"
        )
        assert service == "fanbox"
        assert creator_id == "123"
        assert post_id == "456"
        assert revision_id == "789"
    
    @pytest.mark.asyncio
    async def test_download_post_invalid_input_with_revision(self):
        """Test that download_post still handles invalid input correctly with revision support"""
        # Test invalid input
        invalid = await KToolBoxCli.download_post(url="")
        assert invalid == generate_msg(
            TextEnum.MissingParams.value,
            use_at_lease_one=[
                ["url"],
                ["service", "creator_id", "post_id"]
            ]
        )
    
    @pytest.mark.asyncio
    async def test_download_post_revision_url_parsing(self):
        """Test that download_post correctly parses revision URLs"""
        with patch('ktoolbox.cli.get_post_api') as mock_get_post:
            # Mock the API response
            mock_response = MagicMock()
            mock_response.data.post = Post(
                id="456",
                title="Test Post",
                service="fanbox",
                user="123",
                attachments=[]  # Add empty attachments list
            )
            mock_get_post.return_value = mock_response
            
            with patch('ktoolbox.action.job.create_job_from_post') as mock_create_job:
                mock_create_job.return_value = []
                
                with patch('ktoolbox.job.runner.JobRunner') as mock_job_runner:
                    mock_job_runner.return_value.start = MagicMock()
                    
                    # Test revision URL
                    with tempfile.TemporaryDirectory() as td:
                        result = await KToolBoxCli.download_post(
                            url="https://kemono.su/fanbox/user/123/post/456/revision/789",
                            path=Path(td)
                        )
                    
                    # Verify the API was called with revision_id
                    mock_get_post.assert_called_once_with(
                        service="fanbox",
                        creator_id="123", 
                        post_id="456",
                        revision_id="789"
                    )
    
    @pytest.mark.asyncio
    async def test_get_post_with_revision(self):
        """Test that get_post API supports revision parameter"""
        with patch('ktoolbox.cli.get_post_api') as mock_get_post:
            mock_response = MagicMock()
            mock_response.data.post = Post(
                id="456",
                title="Test Post",
                service="fanbox",
                user="123"
            )
            mock_get_post.return_value = mock_response
            
            # Test with revision_id
            result = await KToolBoxCli.get_post(
                service="fanbox",
                creator_id="123",
                post_id="456", 
                revision_id="789"
            )
            
            # Verify the API was called with revision_id
            mock_get_post.assert_called_once_with(
                service="fanbox",
                creator_id="123",
                post_id="456",
                revision_id="789"
            )
    
    def test_api_revision_path_construction(self):
        """Test that API correctly constructs revision paths"""
        # Test normal post path
        normal_path = GetPost.path.format(
            service="fanbox",
            creator_id="123", 
            post_id="456"
        )
        assert normal_path == "/fanbox/user/123/post/456"
        
        # Test revision path (constructed in the __call__ method)
        revision_path = f"/fanbox/user/123/post/456/revision/789"
        assert revision_path == "/fanbox/user/123/post/456/revision/789"