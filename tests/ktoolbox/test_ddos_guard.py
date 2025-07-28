import pytest
import httpx
from unittest.mock import Mock

from ktoolbox.ddos_guard import (
    DDoSGuardCookieManager, 
    generate_ddg_cookie_value, 
    merge_cookies,
    update_cookies_from_response
)


class TestDDoSGuardCookieManager:
    """Test DDoS Guard cookie manager functionality"""
    
    def test_init_auto_generates_cookies(self):
        """Test initialization auto-generates cookies"""
        manager = DDoSGuardCookieManager()
        cookies = manager.cookies
        
        # Check that required cookies are auto-generated
        assert "ddg1" in cookies
        assert "ddg8" in cookies
        assert "ddg9" in cookies
        assert "ddg10" in cookies
        
        # Check default IP is used
        assert cookies["ddg9"] == "127.0.0.1"
    
    def test_init_with_custom_ip(self):
        """Test initialization with custom IP"""
        manager = DDoSGuardCookieManager("192.168.1.100")
        cookies = manager.cookies
        
        # Check that required cookies are auto-generated
        assert "ddg1" in cookies
        assert "ddg8" in cookies
        assert "ddg9" in cookies
        assert "ddg10" in cookies
        
        # Check custom IP is used
        assert cookies["ddg9"] == "192.168.1.100"
    
    def test_generate_default_cookies(self):
        """Test generation of default DDoS Guard cookies"""
        manager = DDoSGuardCookieManager()
        cookies = manager.generate_default_cookies("192.168.1.1")
        
        # Check that required cookies are generated
        assert "ddg1" in cookies
        assert "ddg8" in cookies
        assert "ddg9" in cookies
        assert "ddg10" in cookies
        
        # Check ddg9 contains the IP
        assert cookies["ddg9"] == "192.168.1.1"
        
        # Check cookies are stored in manager
        assert manager.cookies["ddg9"] == "192.168.1.1"
    
    def test_generate_default_cookies_no_ip(self):
        """Test generation of default cookies without IP"""
        manager = DDoSGuardCookieManager()
        cookies = manager.generate_default_cookies()
        
        assert cookies["ddg9"] == "127.0.0.1"  # Default IP
    
    def test_update_from_response(self):
        """Test updating cookies from HTTP response"""
        manager = DDoSGuardCookieManager()
        
        # Mock response with DDoS Guard cookies
        response = Mock(spec=httpx.Response)
        response.headers = Mock()
        response.headers.get_list.return_value = [
            "ddg8=newvalue8; Path=/; HttpOnly",
            "ddg10=987654321; Path=/; HttpOnly",
            "normal_cookie=value; Path=/"
        ]
        
        updated = manager.update_from_response(response)
        
        assert updated is True
        assert manager.cookies["ddg8"] == "newvalue8"
        assert manager.cookies["ddg10"] == "987654321"
        # Normal cookie should not be added
        assert "normal_cookie" not in manager.cookies
    
    def test_update_from_response_no_ddg_cookies(self):
        """Test updating from response with no DDoS Guard cookies"""
        manager = DDoSGuardCookieManager()
        initial_cookies = manager.cookies.copy()  # Store initial auto-generated cookies
        
        response = Mock(spec=httpx.Response)
        response.headers = Mock()
        response.headers.get_list.return_value = [
            "session=sessionvalue; Path=/",
            "other=value; Path=/"
        ]
        
        updated = manager.update_from_response(response)
        
        assert updated is False
        assert manager.cookies == initial_cookies  # Should remain unchanged
    
    def test_refresh_time_dependent_cookies(self):
        """Test refreshing time-dependent cookies"""
        manager = DDoSGuardCookieManager()
        old_value = manager.cookies["ddg10"]
        
        # Wait a tiny bit to ensure timestamp changes
        import time
        time.sleep(0.01)
        
        manager.refresh_time_dependent_cookies()
        
        new_value = manager.cookies["ddg10"]
        assert new_value != old_value
        assert new_value.isdigit()  # Should be a timestamp
    
    def test_refresh_without_ddg10(self):
        """Test refreshing when ddg10 is manually removed"""
        manager = DDoSGuardCookieManager()
        original_cookies = manager.cookies.copy()
        
        # Remove ddg10 manually
        del manager._cookies["ddg10"]
        
        # Should not raise an error
        manager.refresh_time_dependent_cookies()
        
        # ddg10 should not be restored (only refreshes existing ddg10)
        assert "ddg10" not in manager.cookies


class TestGenerateDdgCookieValue:
    """Test DDoS Guard cookie value generation"""
    
    def test_generate_ddg1(self):
        """Test ddg1 cookie generation"""
        value = generate_ddg_cookie_value("ddg1")
        assert len(value) == 16
        assert value.isalnum()
    
    def test_generate_ddg5(self):
        """Test ddg5 cookie generation"""
        value = generate_ddg_cookie_value("ddg5")
        assert len(value) == 24
        assert value.isalnum()
    
    def test_generate_ddg8(self):
        """Test ddg8 cookie generation"""
        value = generate_ddg_cookie_value("ddg8")
        assert len(value) == 16
        assert value.isalnum()
    
    def test_generate_ddg9_with_ip(self):
        """Test ddg9 cookie generation with IP"""
        value = generate_ddg_cookie_value("ddg9", "10.0.0.1")
        assert value == "10.0.0.1"
    
    def test_generate_ddg9_without_ip(self):
        """Test ddg9 cookie generation without IP"""
        value = generate_ddg_cookie_value("ddg9")
        assert value == "127.0.0.1"
    
    def test_generate_ddg10(self):
        """Test ddg10 cookie generation"""
        value = generate_ddg_cookie_value("ddg10")
        assert value.isdigit()
        assert len(value) >= 10  # Should be a timestamp
    
    def test_generate_unknown_ddg(self):
        """Test generation for unknown ddg cookie"""
        value = generate_ddg_cookie_value("ddg99")
        assert len(value) == 16
        assert value.isalnum()


class TestMergeCookies:
    """Test cookie merging functionality"""
    
    def test_merge_both_none(self):
        """Test merging when both are None"""
        result = merge_cookies(None, None)
        assert result is None
    
    def test_merge_session_only(self):
        """Test merging with only session cookies"""
        session = {"session": "value"}
        result = merge_cookies(session, None)
        assert result == session
    
    def test_merge_ddos_only(self):
        """Test merging with only DDoS cookies"""
        ddos = {"ddg1": "value"}
        result = merge_cookies(None, ddos)
        assert result == ddos
    
    def test_merge_both(self):
        """Test merging both types of cookies"""
        session = {"session": "sessionvalue"}
        ddos = {"ddg1": "ddgvalue"}
        result = merge_cookies(session, ddos)
        
        expected = {"session": "sessionvalue", "ddg1": "ddgvalue"}
        assert result == expected
    
    def test_merge_overlap_ddos_wins(self):
        """Test merging with overlapping keys - DDoS cookies should override"""
        session = {"common": "session_value", "session": "sessionvalue"}
        ddos = {"common": "ddos_value", "ddg1": "ddgvalue"}
        result = merge_cookies(session, ddos)
        
        expected = {"common": "ddos_value", "session": "sessionvalue", "ddg1": "ddgvalue"}
        assert result == expected


class TestUpdateCookiesFromResponse:
    """Test response cookie update functionality"""
    
    def test_update_with_manager(self):
        """Test updating cookies with a manager"""
        manager = DDoSGuardCookieManager()
        response = Mock(spec=httpx.Response)
        response.headers = Mock()
        response.headers.get_list.return_value = ["ddg8=newvalue; Path=/"]
        
        result = update_cookies_from_response(response, manager)
        
        assert result is True
        assert manager.cookies["ddg8"] == "newvalue"
    
    def test_update_without_manager(self):
        """Test updating cookies without a manager"""
        response = Mock(spec=httpx.Response)
        
        result = update_cookies_from_response(response, None)
        
        assert result is False