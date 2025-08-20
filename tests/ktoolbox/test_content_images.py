import pytest
from ktoolbox.utils import extract_content_images


class TestExtractContentImages:
    """Test cases for extract_content_images function"""

    def test_img_tags(self):
        """Test extraction from img tags"""
        content = '''
        <div>
            <img src="/data/66/83/example1.jpg" alt="Image 1">
            <img src="https://kemono.cr/data/12/34/example2.png" alt="Image 2">
            <img src="//kemono.cr/data/56/78/example3.gif" alt="Image 3">
        </div>
        '''
        
        images = extract_content_images(content, service="patreon")
        
        assert len(images) == 3
        assert "https://kemono.cr/patreon/data/66/83/example1.jpg" in images
        assert "https://kemono.cr/data/12/34/example2.png" in images  
        assert "https://kemono.cr/data/56/78/example3.gif" in images

    def test_link_to_images(self):
        """Test extraction from links to image files"""
        content = '''
        <div>
            <a href="https://example.com/image1.jpg">Image Link 1</a>
            <a href="/data/path/image2.png">Image Link 2</a>
            <a href="https://other.com/photo.jpeg?v=123">Image Link 3</a>
        </div>
        '''
        
        images = extract_content_images(content, service="fanbox")
        
        assert len(images) == 3
        assert "https://example.com/image1.jpg" in images
        assert "https://kemono.cr/fanbox/data/path/image2.png" in images
        assert "https://other.com/photo.jpeg?v=123" in images

    def test_picture_and_source_tags(self):
        """Test extraction from picture and source tags"""
        content = '''
        <picture>
            <source src="/data/mobile.webp" media="(max-width: 600px)">
            <source srcset="/data/desktop.jpg 1x, /data/desktop2x.jpg 2x">
            <img src="/data/fallback.png" alt="Picture">
        </picture>
        '''
        
        images = extract_content_images(content)
        
        # Should extract from source and img tags
        assert len(images) >= 3
        assert any("mobile.webp" in img for img in images)
        assert any("desktop.jpg" in img for img in images)
        assert any("fallback.png" in img for img in images)

    def test_background_images(self):
        """Test extraction from CSS background-image properties"""
        content = '''
        <div style="background-image: url('/data/bg1.jpg'); width: 100px;">
            <span style="background-image: url('https://example.com/bg2.png');">Content</span>
        </div>
        '''
        
        images = extract_content_images(content)
        
        assert len(images) == 2
        assert any("bg1.jpg" in img for img in images)
        assert "https://example.com/bg2.png" in images

    def test_empty_content(self):
        """Test handling of empty or None content"""
        assert extract_content_images("") == set()
        assert extract_content_images(None) == set()

    def test_no_images(self):
        """Test content with no images"""
        content = '''
        <div>
            <p>Some text content</p>
            <a href="https://example.com/document.pdf">PDF Link</a>
        </div>
        '''
        
        images = extract_content_images(content)
        assert images == set()

    def test_data_urls(self):
        """Test handling of data URLs"""
        content = '''
        <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==">
        <img src="data:text/plain;base64,SGVsbG8gV29ybGQ=">
        <img src="/data/real_image.jpg">
        '''
        
        images = extract_content_images(content)
        
        # Should include data:image URLs but not other data URLs
        assert len(images) >= 1
        assert any("real_image.jpg" in img for img in images)

    def test_html_entities(self):
        """Test handling of HTML entities in URLs"""
        content = '''
        <img src="/data/image.jpg?param1=value&amp;param2=value">
        <a href="https://example.com/photo.png?a=1&amp;b=2">Link</a>
        '''
        
        images = extract_content_images(content)
        
        # URLs should be properly decoded
        assert len(images) == 2
        for img in images:
            assert "&amp;" not in img
            assert "&" in img

    def test_relative_url_resolution(self):
        """Test proper resolution of relative URLs"""
        content = '''
        <img src="/absolute/path/image.jpg">
        <img src="//cdn.example.com/image.png">
        <img src="relative/image.gif">
        '''
        
        images = extract_content_images(content, service="patreon", base_url="https://kemono.cr/patreon")
        
        assert len(images) == 3
        
        # Check URL resolution
        absolute_urls = [url for url in images if url.startswith("https://kemono.cr/patreon/absolute/")]
        protocol_relative = [url for url in images if url.startswith("https://cdn.example.com/")]
        relative_urls = [url for url in images if "relative/image.gif" in url]
        
        assert len(absolute_urls) == 1
        assert len(protocol_relative) == 1  
        assert len(relative_urls) == 1

    def test_srcset_attribute(self):
        """Test extraction from srcset attributes with multiple resolutions"""
        content = '''
        <source srcset="/data/small.jpg 480w, /data/medium.jpg 800w, /data/large.jpg 1200w">
        '''
        
        images = extract_content_images(content)
        
        # Should extract the first URL from srcset
        assert len(images) >= 1
        assert any("small.jpg" in img for img in images)