import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from ktoolbox.action.utils import generate_year_dirname, generate_month_dirname, generate_grouped_post_path
from ktoolbox.api.model import Post
from ktoolbox.configuration import config


@pytest.fixture
def sample_post():
    """Create a sample post for testing"""
    return Post(
        id="test123",
        user="testuser",
        service="fanbox", 
        title="Test Post",
        content="Test content",
        published=datetime(2024, 3, 15),
        added=datetime(2024, 3, 10),
        edited=datetime(2024, 3, 20),
        attachments=[],
        file=None
    )


@pytest.fixture
def sample_post_no_published():
    """Create a sample post without published date"""
    return Post(
        id="test456",
        user="testuser",
        service="fanbox",
        title="Test Post No Published",
        content="Test content",
        published=None,
        added=datetime(2023, 12, 25),
        edited=datetime(2023, 12, 26),
        attachments=[],
        file=None
    )


@pytest.fixture
def sample_post_no_dates():
    """Create a sample post without any dates"""
    return Post(
        id="test789",
        user="testuser", 
        service="fanbox",
        title="Test Post No Dates",
        content="Test content",
        published=None,
        added=None,
        edited=None,
        attachments=[],
        file=None
    )


def test_generate_year_dirname_default_format(sample_post):
    """Test year directory generation with default format"""
    result = generate_year_dirname(sample_post)
    assert result == "2024"


def test_generate_year_dirname_custom_format(sample_post):
    """Test year directory generation with custom format"""
    with patch.object(config.job, 'year_dirname_format', 'Year_{year}'):
        result = generate_year_dirname(sample_post)
        assert result == "Year_2024"


def test_generate_year_dirname_fallback_to_added(sample_post_no_published):
    """Test year directory generation falls back to added date"""
    result = generate_year_dirname(sample_post_no_published)
    assert result == "2023"


def test_generate_year_dirname_no_dates(sample_post_no_dates):
    """Test year directory generation with no dates"""
    result = generate_year_dirname(sample_post_no_dates)
    assert result == "unknown"


def test_generate_month_dirname_default_format(sample_post):
    """Test month directory generation with default format"""
    result = generate_month_dirname(sample_post)
    assert result == "2024-03"


def test_generate_month_dirname_custom_format(sample_post):
    """Test month directory generation with custom format"""
    with patch.object(config.job, 'month_dirname_format', '{year}_{month:02d}'):
        result = generate_month_dirname(sample_post)
        assert result == "2024_03"


def test_generate_month_dirname_fallback_to_added(sample_post_no_published):
    """Test month directory generation falls back to added date"""
    result = generate_month_dirname(sample_post_no_published)
    assert result == "2023-12"


def test_generate_month_dirname_no_dates(sample_post_no_dates):
    """Test month directory generation with no dates"""
    result = generate_month_dirname(sample_post_no_dates)
    assert result == "unknown"


def test_generate_grouped_post_path_no_grouping(sample_post):
    """Test path generation with no grouping enabled"""
    base_path = Path("/test/creator")
    with patch.object(config.job, 'group_by_year', False):
        with patch.object(config.job, 'group_by_month', False):
            result = generate_grouped_post_path(sample_post, base_path)
            assert result == base_path


def test_generate_grouped_post_path_year_only(sample_post):
    """Test path generation with year grouping only"""
    base_path = Path("/test/creator")
    with patch.object(config.job, 'group_by_year', True):
        with patch.object(config.job, 'group_by_month', False):
            result = generate_grouped_post_path(sample_post, base_path)
            assert result == base_path / "2024"


def test_generate_grouped_post_path_year_and_month(sample_post):
    """Test path generation with both year and month grouping"""
    base_path = Path("/test/creator")
    with patch.object(config.job, 'group_by_year', True):
        with patch.object(config.job, 'group_by_month', True):
            result = generate_grouped_post_path(sample_post, base_path)
            assert result == base_path / "2024" / "2024-03"


def test_generate_grouped_post_path_month_without_year(sample_post):
    """Test path generation with month grouping but no year grouping"""
    base_path = Path("/test/creator")
    with patch.object(config.job, 'group_by_year', False):
        with patch.object(config.job, 'group_by_month', True):
            result = generate_grouped_post_path(sample_post, base_path)
            # Month grouping should not work without year grouping
            assert result == base_path


def test_invalid_year_format_key():
    """Test error handling for invalid year format key"""
    sample_post = Post(
        id="test123",
        user="testuser",
        service="fanbox",
        title="Test Post",
        content="Test content",
        published=datetime(2024, 3, 15),
        added=datetime(2024, 3, 10),
        edited=datetime(2024, 3, 20),
        attachments=[],
        file=None
    )
    
    with patch.object(config.job, 'year_dirname_format', '{invalid_key}'):
        with pytest.raises(SystemExit):
            generate_year_dirname(sample_post)


def test_invalid_month_format_key():
    """Test error handling for invalid month format key"""
    sample_post = Post(
        id="test123",
        user="testuser",
        service="fanbox",
        title="Test Post",
        content="Test content",
        published=datetime(2024, 3, 15),
        added=datetime(2024, 3, 10),
        edited=datetime(2024, 3, 20),
        attachments=[],
        file=None
    )
    
    with patch.object(config.job, 'month_dirname_format', '{invalid_key}'):
        with pytest.raises(SystemExit):
            generate_month_dirname(sample_post)