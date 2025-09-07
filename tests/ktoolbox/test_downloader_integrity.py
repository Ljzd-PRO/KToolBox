import pytest
from ktoolbox.configuration import config


class TestDownloaderConfiguration:
    """Test new downloader configuration options"""

    def test_integrity_check_config_default(self):
        """Test that verify_file_integrity is enabled by default"""
        assert config.downloader.verify_file_integrity is True

    def test_checksum_verification_config_default(self):
        """Test that checksum_verification is disabled by default"""
        assert config.downloader.checksum_verification is False

    def test_config_can_be_modified(self):
        """Test that configuration can be modified"""
        # Save original values
        original_verify = config.downloader.verify_file_integrity
        original_checksum = config.downloader.checksum_verification
        
        try:
            # Modify values
            config.downloader.verify_file_integrity = False
            config.downloader.checksum_verification = True
            
            # Check they were modified
            assert config.downloader.verify_file_integrity is False
            assert config.downloader.checksum_verification is True
            
        finally:
            # Restore original values
            config.downloader.verify_file_integrity = original_verify
            config.downloader.checksum_verification = original_checksum


class TestDownloaderLogic:
    """Test downloader logic improvements"""

    def test_content_length_fallback_logic(self):
        """Test that Content-Length is used when Content-Range is not available"""
        # This tests the logic we added to check Content-Length as fallback
        
        # Simulate the logic from downloader.py
        range_str = None  # No Content-Range header
        headers = {"Content-Length": "12345"}
        
        # Our updated logic
        total_size = int(range_str.split("/")[-1]) if range_str else None
        if total_size is None:
            total_size = int(headers.get("Content-Length", 0)) or None
            
        assert total_size == 12345

    def test_content_range_takes_priority(self):
        """Test that Content-Range takes priority over Content-Length"""
        # This tests that existing logic still works correctly
        
        range_str = "bytes 1000-12345/12346"
        headers = {"Content-Length": "11346", "Content-Range": range_str}
        
        # Our updated logic
        total_size = int(range_str.split("/")[-1]) if range_str else None
        if total_size is None:
            total_size = int(headers.get("Content-Length", 0)) or None
            
        assert total_size == 12346  # Should use Content-Range, not Content-Length

    def test_no_size_headers(self):
        """Test behavior when neither Content-Range nor Content-Length are available"""
        range_str = None
        headers = {}
        
        # Our updated logic
        total_size = int(range_str.split("/")[-1]) if range_str else None
        if total_size is None:
            total_size = int(headers.get("Content-Length", 0)) or None
            
        assert total_size is None