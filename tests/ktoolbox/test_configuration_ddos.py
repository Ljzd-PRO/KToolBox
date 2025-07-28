import pytest
from ktoolbox.configuration import APIConfiguration, Configuration


class TestAPIConfiguration:
    """Test API configuration including DDoS Guard cookies"""
    
    def test_default_ddos_guard_cookies(self):
        """Test that default DDoS Guard cookies is empty dict"""
        config = APIConfiguration()
        assert config.ddos_guard_cookies == {}
    
    def test_set_ddos_guard_cookies(self):
        """Test setting DDoS Guard cookies"""
        ddos_cookies = {
            "ddg1": "testvalue1",
            "ddg8": "testvalue8", 
            "ddg9": "192.168.1.1",
            "ddg10": "1234567890"
        }
        config = APIConfiguration(ddos_guard_cookies=ddos_cookies)
        assert config.ddos_guard_cookies == ddos_cookies
    
    def test_configuration_with_ddos_guard_cookies(self):
        """Test full configuration with DDoS Guard cookies"""
        ddos_cookies = {"ddg1": "test", "ddg8": "test8"}
        config = Configuration(api=APIConfiguration(ddos_guard_cookies=ddos_cookies))
        assert config.api.ddos_guard_cookies == ddos_cookies
    
    def test_empty_ddos_guard_cookies_is_falsy(self):
        """Test that empty DDoS Guard cookies dictionary is falsy"""
        config = APIConfiguration()
        assert not config.ddos_guard_cookies
    
    def test_populated_ddos_guard_cookies_is_truthy(self):
        """Test that populated DDoS Guard cookies dictionary is truthy"""
        config = APIConfiguration(ddos_guard_cookies={"ddg1": "test"})
        assert config.ddos_guard_cookies