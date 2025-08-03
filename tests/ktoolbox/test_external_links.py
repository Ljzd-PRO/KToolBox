import pytest
from ktoolbox.utils import extract_external_links


class TestExtractExternalLinks:
    """Test cases for extract_external_links function"""

    def test_plain_text_links(self):
        """Test extraction from plain text content"""
        content = "Check out this file: https://www.dropbox.com/scl/fo/fpce4g4q4huztj71vo8uh/AB6Z1ukDsiKu0WONcWFxvq4?rlkey=wetgmx8xs41fl0o3ac81gm8kd&st=x3ejm0rh&dl=0"
        patterns = [r'https?://(?:www\.)?dropbox\.com/[^\s]+']
        
        links = extract_external_links(content, patterns)
        
        expected_link = "https://www.dropbox.com/scl/fo/fpce4g4q4huztj71vo8uh/AB6Z1ukDsiKu0WONcWFxvq4?rlkey=wetgmx8xs41fl0o3ac81gm8kd&st=x3ejm0rh&dl=0"
        assert expected_link in links

    def test_html_entities_and_markup(self):
        """Test that HTML entities are decoded and markup is removed"""
        content = '''
        <p>Here is the link:</p>
        <a href="https://www.dropbox.com/scl/fo/fpce4g4q4huztj71vo8uh/AB6Z1ukDsiKu0WONcWFxvq4?rlkey=wetgmx8xs41fl0o3ac81gm8kd&amp;st=x3ejm0rh&amp;dl=0">Download</a>
        <p>video</p>
        '''
        patterns = [r'https?://(?:www\.)?dropbox\.com/[^\s]+']
        
        links = extract_external_links(content, patterns)
        
        # Should decode &amp; to & and remove HTML markup
        expected_link = "https://www.dropbox.com/scl/fo/fpce4g4q4huztj71vo8uh/AB6Z1ukDsiKu0WONcWFxvq4?rlkey=wetgmx8xs41fl0o3ac81gm8kd&st=x3ejm0rh&dl=0"
        assert expected_link in links
        
        # Check that we don't have links with HTML entities or tags
        for link in links:
            assert "&amp;" not in link, f"Found HTML entity &amp; in link: {link}"
            assert "<" not in link, f"Found HTML tag in link: {link}"
            assert ">" not in link, f"Found HTML tag in link: {link}"

    def test_multiple_link_types(self):
        """Test extraction of multiple different link types"""
        content = '''
        <div>
            <a href="https://www.dropbox.com/s/abc123/file.zip?dl=0&amp;raw=1">Dropbox</a>
            <p>MEGA: https://mega.nz/file/xyz789?key=test&amp;action=download</p>
            <span onclick="window.open('https://drive.google.com/file/d/456/view?usp=sharing&amp;t=123')">Google Drive</span>
        </div>
        '''
        patterns = [
            r'https?://(?:www\.)?dropbox\.com/[^\s]+',
            r'https?://mega\.nz/[^\s]+',
            r'https?://drive\.google\.com/[^\s]+',
        ]
        
        links = extract_external_links(content, patterns)
        
        # Check that HTML entities are properly decoded
        for link in links:
            assert "&amp;" not in link, f"Found HTML entity in: {link}"
            assert "<" not in link, f"Found HTML tag in: {link}"
            assert ">" not in link, f"Found HTML tag in: {link}"
        
        # Should find all three types of links
        assert len(links) == 3

    def test_trailing_punctuation_removal(self):
        """Test removal of trailing punctuation"""
        content = '''
        Links with punctuation:
        - https://dropbox.com/s/test123/file.zip.
        - Check this: https://mega.nz/file/test456!
        - (See https://drive.google.com/file/d/789)
        - "Download from https://mediafire.com/file/abc"
        '''
        patterns = [
            r'https?://(?:www\.)?dropbox\.com/[^\s]+',
            r'https?://mega\.nz/[^\s]+',
            r'https?://drive\.google\.com/[^\s]+',
            r'https?://(?:www\.)?mediafire\.com/[^\s]+',
        ]
        
        links = extract_external_links(content, patterns)
        
        # Verify clean URLs without trailing punctuation
        for link in links:
            assert not link.endswith(('.', '!', ')', '"')), f"Link has trailing punctuation: {link}"

    def test_empty_content(self):
        """Test handling of empty or None content"""
        patterns = [r'https?://(?:www\.)?dropbox\.com/[^\s]+']
        
        assert extract_external_links("", patterns) == set()
        assert extract_external_links(None, patterns) == set()

    def test_no_patterns(self):
        """Test with no custom patterns provided"""
        content = "https://www.dropbox.com/file/123"
        
        # Should return empty set when no patterns provided
        links = extract_external_links(content, [])
        assert links == set()