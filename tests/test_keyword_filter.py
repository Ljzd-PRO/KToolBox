import pytest
from datetime import datetime
from typing import Set

from ktoolbox.api.model.post import Post
from ktoolbox.action.utils import filter_posts_by_keywords, _match_post_keywords


class TestKeywordFiltering:
    
    def test_match_post_keywords_empty_keywords(self):
        """Test that empty keywords set returns True (no filtering)"""
        post = Post(title="Test Post", content="Test content")
        result = _match_post_keywords(post, set())
        assert result is True
        
        result = _match_post_keywords(post, None)
        assert result is True

    def test_match_post_keywords_title_match(self):
        """Test keyword matching in post title"""
        post = Post(title="Amazing Artwork", content="Some description")
        keywords = {"amazing", "artwork"}
        
        result = _match_post_keywords(post, keywords)
        assert result is True
        
        # Case insensitive test
        keywords = {"AMAZING", "ArtWork"}
        result = _match_post_keywords(post, keywords)
        assert result is True

    def test_match_post_keywords_title_only(self):
        """Test keyword matching only applies to post title, not content"""
        post = Post(title="Amazing Artwork", content="This contains python programming tutorial")
        
        # Keywords in title should match
        keywords = {"amazing", "artwork"}
        result = _match_post_keywords(post, keywords)
        assert result is True
        
        # Keywords only in content should NOT match
        keywords = {"python", "programming", "tutorial"}
        result = _match_post_keywords(post, keywords)
        assert result is False

    def test_match_post_keywords_no_match(self):
        """Test when no keywords match"""
        post = Post(title="Art Gallery", content="Beautiful paintings and sculptures")
        keywords = {"python", "programming"}
        
        result = _match_post_keywords(post, keywords)
        assert result is False

    def test_match_post_keywords_partial_match(self):
        """Test partial keyword matching (substring)"""
        post = Post(title="Programming Tutorial", content="Learn to code")
        keywords = {"program"}  # Should match "Programming"
        
        result = _match_post_keywords(post, keywords)
        assert result is True

    def test_match_post_keywords_empty_post_fields(self):
        """Test handling of posts with empty title/content"""
        post = Post(title=None, content=None)
        keywords = {"test"}
        
        result = _match_post_keywords(post, keywords)
        assert result is False
        
        post = Post(title="", content="")
        result = _match_post_keywords(post, keywords)
        assert result is False

    def test_filter_posts_by_keywords_empty_list(self):
        """Test filtering empty post list"""
        posts = []
        keywords = {"test"}
        
        result = list(filter_posts_by_keywords(posts, keywords))
        assert result == []

    def test_filter_posts_by_keywords_no_keywords(self):
        """Test filtering with no keywords (should return all posts)"""
        posts = [
            Post(id="1", title="Post 1", content="Content 1"),
            Post(id="2", title="Post 2", content="Content 2")
        ]
        
        result = list(filter_posts_by_keywords(posts, None))
        assert len(result) == 2
        
        result = list(filter_posts_by_keywords(posts, set()))
        assert len(result) == 2

    def test_filter_posts_by_keywords_with_filtering(self):
        """Test actual filtering with keywords (title only)"""
        posts = [
            Post(id="1", title="Python Tutorial", content="Learn programming"),
            Post(id="2", title="Art Gallery", content="Beautiful paintings"),
            Post(id="3", title="Java Guide", content="Programming in Java"),
            Post(id="4", title="Cooking Tips", content="Python recipes for cooking")
        ]
        
        keywords = {"python"}
        result = list(filter_posts_by_keywords(posts, keywords))
        
        # Should match only post 1 (title contains "python")
        # Post 4 should NOT match since "python" is only in content
        assert len(result) == 1
        assert result[0].id == "1"
        
        keywords = {"java"}
        result = list(filter_posts_by_keywords(posts, keywords))
        
        # Should match only post 3 (title contains "Java")
        assert len(result) == 1
        assert result[0].id == "3"

    def test_filter_posts_by_keywords_multiple_keywords(self):
        """Test filtering with multiple keywords (OR logic)"""
        posts = [
            Post(id="1", title="Python Tutorial", content="Learn coding"),
            Post(id="2", title="Art Gallery", content="Beautiful paintings"),
            Post(id="3", title="Music Review", content="Amazing soundtrack")
        ]
        
        keywords = {"python", "art"}
        result = list(filter_posts_by_keywords(posts, keywords))
        
        # Should match posts 1 and 2
        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].id == "2"