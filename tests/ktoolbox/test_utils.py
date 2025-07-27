import pytest
from ktoolbox.utils import parse_search_url


def test_parse_search_url():
    """Test parsing of search URLs"""
    # Valid search URLs
    assert parse_search_url("https://kemono.su/posts?q=mai+sakurajima") == "mai sakurajima"
    assert parse_search_url("https://kemono.su/posts?q=test") == "test"
    assert parse_search_url("https://kemono.su/posts?q=hello%20world") == "hello world"
    
    # Invalid URLs (not search URLs)
    assert parse_search_url("https://kemono.su/fanbox/user/123") is None
    assert parse_search_url("https://kemono.su/fanbox/user/123/post/456") is None
    assert parse_search_url("https://example.com/other") is None
    
    # Edge cases
    assert parse_search_url("https://kemono.su/posts") is None  # No query parameter
    assert parse_search_url("https://kemono.su/posts?other=value") is None  # No 'q' parameter
    
    # Test with multiple parameters
    assert parse_search_url("https://kemono.su/posts?q=test&o=50") == "test"