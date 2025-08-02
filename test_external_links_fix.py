#!/usr/bin/env python3
"""
Test case to reproduce the external links issue
"""

from ktoolbox.utils import extract_external_links
from ktoolbox.configuration import config

def test_external_links_with_html_entities():
    """Test that external links are extracted correctly without HTML entities and tags"""
    
    # Sample content that reproduces the issue from the GitHub issue
    content_with_html_entities = '''
    <p>Here is the link:</p>
    <a href="https://www.dropbox.com/scl/fo/fpce4g4q4huztj71vo8uh/AB6Z1ukDsiKu0WONcWFxvq4?rlkey=wetgmx8xs41fl0o3ac81gm8kd&amp;st=x3ejm0rh&amp;dl=0">Download</a>
    <p>video</p>
    '''
    
    # Extract links using the current function
    links = extract_external_links(content_with_html_entities, config.job.external_link_patterns)
    
    print("Extracted links:")
    for link in sorted(links):
        print(f"  {link}")
    
    # Expected clean link
    expected_link = "https://www.dropbox.com/scl/fo/fpce4g4q4huztj71vo8uh/AB6Z1ukDsiKu0WONcWFxvq4?rlkey=wetgmx8xs41fl0o3ac81gm8kd&st=x3ejm0rh&dl=0"
    
    print(f"\nExpected link: {expected_link}")
    
    # Check if we get the expected clean link
    assert expected_link in links, f"Expected clean link not found. Got: {links}"
    
    # Check that we don't have links with HTML entities or tags
    for link in links:
        assert "&amp;" not in link, f"Found HTML entity &amp; in link: {link}"
        assert "<" not in link, f"Found HTML tag in link: {link}"
        assert ">" not in link, f"Found HTML tag in link: {link}"

def test_external_links_plain_text():
    """Test extraction from plain text content"""
    content = "Check out this file: https://www.dropbox.com/scl/fo/fpce4g4q4huztj71vo8uh/AB6Z1ukDsiKu0WONcWFxvq4?rlkey=wetgmx8xs41fl0o3ac81gm8kd&st=x3ejm0rh&dl=0"
    
    links = extract_external_links(content, config.job.external_link_patterns)
    
    print("Links from plain text:")
    for link in sorted(links):
        print(f"  {link}")
    
    expected_link = "https://www.dropbox.com/scl/fo/fpce4g4q4huztj71vo8uh/AB6Z1ukDsiKu0WONcWFxvq4?rlkey=wetgmx8xs41fl0o3ac81gm8kd&st=x3ejm0rh&dl=0"
    assert expected_link in links

if __name__ == "__main__":
    print("Testing external links extraction...")
    try:
        test_external_links_plain_text()
        print("✓ Plain text test passed")
    except Exception as e:
        print(f"✗ Plain text test failed: {e}")
    
    try:
        test_external_links_with_html_entities()
        print("✓ HTML entities test passed")
    except Exception as e:
        print(f"✗ HTML entities test failed: {e}")