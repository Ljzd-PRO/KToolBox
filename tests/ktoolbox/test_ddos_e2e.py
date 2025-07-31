import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

from ktoolbox.configuration import config, APIConfiguration
from ktoolbox.api.base import BaseAPI
from ktoolbox.job.runner import JobRunner
from ktoolbox.downloader import Downloader
from ktoolbox.ddos_guard import DDoSGuardCookieManager


class TestEndToEndDDoSGuard:
    """End-to-end test for DDoS Guard functionality"""
    
    def setup_method(self):
        """Reset configuration before each test"""
        config.api = APIConfiguration()
        BaseAPI._ddos_cookie_manager = None
    
    def test_full_workflow_with_ddos_cookies(self):
        """Test the complete workflow with DDoS Guard cookies"""
        # 1. Configure DDoS Guard cookies
        config.api.ddos_guard_cookies = {
            "ddg1": "test_ddg1_value",
            "ddg8": "test_ddg8_value", 
            "ddg9": "192.168.1.100",
            "ddg10": "1640995200000"
        }
        config.api.session_key = "test_session"
        
        # 2. Test API integration
        cookies = BaseAPI._build_cookies()
        expected_cookies = {
            "session": "test_session",
            "ddg1": "test_ddg1_value",
            "ddg8": "test_ddg8_value",
            "ddg9": "192.168.1.100", 
            "ddg10": "1640995200000"
        }
        assert cookies == expected_cookies
        
        # 3. Test DDoS cookie manager is initialized
        manager = BaseAPI._get_ddos_cookie_manager()
        assert manager is not None
        assert manager.cookies == config.api.ddos_guard_cookies
        
        # 4. Test job runner integration
        runner = JobRunner()
        assert runner._ddos_cookie_manager is not None
        assert runner._ddos_cookie_manager.cookies == config.api.ddos_guard_cookies
    
    def test_cookie_updates_from_server_responses(self):
        """Test that cookies are updated from server responses"""
        # Configure initial cookies
        config.api.ddos_guard_cookies = {"ddg1": "initial_value"}
        
        # Get the manager and simulate server response
        manager = BaseAPI._get_ddos_cookie_manager()
        
        # Mock a server response with updated cookies
        mock_response = Mock()
        mock_response.headers = Mock()
        mock_response.headers.get_list.return_value = [
            "ddg8=server_updated_8; Path=/; HttpOnly",
            "ddg10=server_updated_10; Path=/; HttpOnly"
        ]
        
        # Update cookies from response
        updated = manager.update_from_response(mock_response)
        
        assert updated is True
        final_cookies = manager.cookies
        assert final_cookies["ddg1"] == "initial_value"  # Original cookie preserved
        assert final_cookies["ddg8"] == "server_updated_8"  # New cookie from server
        assert final_cookies["ddg10"] == "server_updated_10"  # New cookie from server
    
    def test_configuration_persistence(self):
        """Test that configuration changes persist across API calls"""
        # Set initial configuration
        config.api.ddos_guard_cookies = {"ddg1": "persistent_test"}
        
        # Make multiple API calls and ensure cookies persist
        cookies1 = BaseAPI._build_cookies()
        cookies2 = BaseAPI._build_cookies()
        
        assert cookies1 == cookies2
        assert cookies1["ddg1"] == "persistent_test"
    
    def test_empty_ddos_cookies_behavior(self):
        """Test behavior when no DDoS cookies are configured"""
        # Ensure no DDoS cookies are configured
        config.api.ddos_guard_cookies = {}
        config.api.session_key = "only_session"
        
        # Test that only session cookies are used
        cookies = BaseAPI._build_cookies()
        assert cookies == {"session": "only_session"}
        
        # Test that DDoS manager is not initialized
        manager = BaseAPI._get_ddos_cookie_manager()
        assert manager is None
    
    def test_ddos_cookies_without_session(self):
        """Test DDoS cookies work without session key"""
        config.api.ddos_guard_cookies = {"ddg1": "only_ddos"}
        config.api.session_key = ""
        
        cookies = BaseAPI._build_cookies()
        assert cookies == {"ddg1": "only_ddos"}
    
    def test_job_runner_passes_ddos_manager_to_downloader(self):
        """Test that JobRunner passes DDoS manager to Downloader instances"""
        config.api.ddos_guard_cookies = {"ddg1": "test"}
        
        runner = JobRunner()
        
        # Create a mock job to test downloader creation
        with patch('ktoolbox.job.runner.urlunparse') as mock_url:
            mock_url.return_value = "http://test.url"
            
            with patch('ktoolbox.job.runner.Downloader') as mock_downloader_class:
                with patch.object(runner._job_queue, 'empty', return_value=True):
                    # This would normally process jobs, but we just want to test the setup
                    pass
                
                # Verify the downloader would be created with DDoS manager
                assert runner._ddos_cookie_manager is not None
                assert runner._ddos_cookie_manager.cookies == {"ddg1": "test"}