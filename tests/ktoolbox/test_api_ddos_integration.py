"""
Integration test for DDoS Guard cookie functionality with API
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from ktoolbox.api.base import BaseAPI
from ktoolbox.configuration import config, APIConfiguration
from ktoolbox.ddos_guard import DDoSGuardCookieManager


class TestAPIIntegrationWithDDoSGuard:
    """Test API integration with DDoS Guard cookies"""
    
    def setup_method(self):
        """Reset configuration before each test"""
        # Reset API configuration
        config.api = APIConfiguration()
        # Reset class variables
        BaseAPI._ddos_cookie_manager = None
    
    def test_api_without_ddos_cookies(self):
        """Test API works normally without DDoS Guard cookies"""
        cookies = BaseAPI._build_cookies()
        assert cookies is None
    
    def test_api_with_ddos_cookies_only(self):
        """Test API with only DDoS Guard cookies"""
        config.api.ddos_guard_cookies = {"ddg1": "test1", "ddg8": "test8"}
        
        cookies = BaseAPI._build_cookies()
        assert cookies == {"ddg1": "test1", "ddg8": "test8"}
    
    def test_api_with_session_and_ddos_cookies(self):
        """Test API with both session and DDoS Guard cookies"""
        config.api.session_key = "testsession"
        config.api.ddos_guard_cookies = {"ddg1": "test1", "ddg8": "test8"}
        
        cookies = BaseAPI._build_cookies()
        expected = {"session": "testsession", "ddg1": "test1", "ddg8": "test8"}
        assert cookies == expected
    
    def test_ddos_cookie_manager_initialization(self):
        """Test DDoS cookie manager is initialized properly"""
        config.api.ddos_guard_cookies = {"ddg1": "test1"}
        
        manager = BaseAPI._get_ddos_cookie_manager()
        assert manager is not None
        assert manager.cookies == {"ddg1": "test1"}
        
        # Should return same instance on subsequent calls
        manager2 = BaseAPI._get_ddos_cookie_manager()
        assert manager is manager2
    
    def test_ddos_cookie_manager_not_initialized_when_empty(self):
        """Test DDoS cookie manager is not initialized when no cookies configured"""
        config.api.ddos_guard_cookies = {}
        
        manager = BaseAPI._get_ddos_cookie_manager()
        assert manager is None
    
    @pytest.mark.asyncio
    async def test_api_request_updates_ddos_cookies(self):
        """Test that API requests update DDoS cookies from responses"""
        # Configure DDoS cookies
        config.api.ddos_guard_cookies = {"ddg1": "initial"}
        
        # Create a concrete API class for testing
        class TestAPI(BaseAPI):
            path = "/test"
            method = "get"
            
            @classmethod
            async def __call__(cls, *args, **kwargs):
                return await cls.request()
        
        # Mock the httpx client
        mock_response = Mock()
        mock_response.headers = Mock()
        mock_response.headers.get_list.return_value = [
            "ddg8=updated8; Path=/",
            "ddg10=updated10; Path=/"
        ]
        
        with patch.object(TestAPI.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            # Mock the handle_res method to return a successful result
            with patch.object(TestAPI, 'handle_res') as mock_handle:
                mock_handle.return_value = Mock()
                
                await TestAPI.request()
                
                # Verify that DDoS cookies were updated
                manager = TestAPI._get_ddos_cookie_manager()
                assert "ddg8" in manager.cookies
                assert "ddg10" in manager.cookies
                assert manager.cookies["ddg8"] == "updated8"
                assert manager.cookies["ddg10"] == "updated10"
    
    def test_api_cookies_merged_in_request_kwargs(self):
        """Test that cookies are properly merged into request kwargs"""
        config.api.session_key = "testsession"
        config.api.ddos_guard_cookies = {"ddg1": "test1"}
        
        # Test that _build_cookies returns the expected merged cookies
        cookies = BaseAPI._build_cookies()
        expected = {"session": "testsession", "ddg1": "test1"}
        assert cookies == expected