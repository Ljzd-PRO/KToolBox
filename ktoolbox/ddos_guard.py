"""
DDoS Guard cookie management utilities
"""
import time
import random
import string
from typing import Dict, Optional
from urllib.parse import urlparse

import httpx
from loguru import logger

__all__ = ["DDoSGuardCookieManager", "merge_cookies", "update_cookies_from_response"]


def generate_ddg_cookie_value(cookie_name: str, client_ip: Optional[str] = None) -> str:
    """
    Generate a DDoS Guard cookie value based on the cookie name
    
    :param cookie_name: Name of the DDoS Guard cookie (e.g., ddg1, ddg8, ddg9, ddg10)
    :param client_ip: Client IP address for ddg9 cookie
    :return: Generated cookie value
    """
    if cookie_name == "ddg1":
        # ddg1 can be any random value, expires in ~1 year
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    elif cookie_name == "ddg5":
        # ddg5 is not validated by DDoS Guard 
        return ''.join(random.choices(string.ascii_letters + string.digits, k=24))
    elif cookie_name == "ddg8":
        # ddg8 is a random string value
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    elif cookie_name == "ddg9":
        # ddg9 is the client IP, but can work with any IP-like value
        return client_ip or "127.0.0.1"
    elif cookie_name == "ddg10":
        # ddg10 is time/request dependent, use current timestamp
        return str(int(time.time() * 1000))
    else:
        # For any other ddg cookie, generate random value
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


class DDoSGuardCookieManager:
    """
    Manager for DDoS Guard cookies to help bypass protection
    """
    
    def __init__(self, initial_cookies: Optional[Dict[str, str]] = None):
        """
        Initialize the DDoS Guard cookie manager
        
        :param initial_cookies: Initial DDoS Guard cookies to use
        """
        self._cookies: Dict[str, str] = initial_cookies.copy() if initial_cookies else {}
        
    @property
    def cookies(self) -> Dict[str, str]:
        """Get current DDoS Guard cookies"""
        return self._cookies.copy()
    
    def generate_default_cookies(self, client_ip: Optional[str] = None) -> Dict[str, str]:
        """
        Generate a default set of DDoS Guard cookies
        
        :param client_ip: Client IP address for ddg9 cookie
        :return: Dictionary of generated DDoS Guard cookies
        """
        ddg_cookies = {
            "ddg1": generate_ddg_cookie_value("ddg1"),
            "ddg8": generate_ddg_cookie_value("ddg8"),
            "ddg9": generate_ddg_cookie_value("ddg9", client_ip),
            "ddg10": generate_ddg_cookie_value("ddg10"),
        }
        self._cookies.update(ddg_cookies)
        logger.debug(f"Generated default DDoS Guard cookies: {list(ddg_cookies.keys())}")
        return ddg_cookies
    
    def update_from_response(self, response: httpx.Response) -> bool:
        """
        Update DDoS Guard cookies from HTTP response
        
        :param response: HTTP response that may contain DDoS Guard cookies
        :return: True if any DDoS Guard cookies were updated
        """
        updated = False
        
        # Extract Set-Cookie headers and update DDoS Guard cookies
        for cookie_header in response.headers.get_list("set-cookie"):
            if "ddg" in cookie_header.lower():
                # Parse cookie name and value
                try:
                    cookie_parts = cookie_header.split(';')[0].strip()
                    if '=' in cookie_parts:
                        name, value = cookie_parts.split('=', 1)
                        name = name.strip()
                        value = value.strip()
                        
                        if name.startswith("ddg"):
                            self._cookies[name] = value
                            updated = True
                            logger.debug(f"Updated DDoS Guard cookie {name} from response")
                except Exception as e:
                    logger.warning(f"Failed to parse DDoS Guard cookie from response: {e}")
        
        return updated
    
    def refresh_time_dependent_cookies(self):
        """
        Refresh time-dependent DDoS Guard cookies (like ddg10)
        """
        if "ddg10" in self._cookies:
            old_value = self._cookies["ddg10"]
            self._cookies["ddg10"] = generate_ddg_cookie_value("ddg10")
            logger.debug(f"Refreshed ddg10 cookie: {old_value} -> {self._cookies['ddg10']}")


def merge_cookies(session_cookies: Optional[Dict[str, str]], 
                  ddos_cookies: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    Merge session cookies with DDoS Guard cookies
    
    :param session_cookies: Existing session cookies
    :param ddos_cookies: DDoS Guard cookies to add
    :return: Merged cookie dictionary or None if no cookies
    """
    if not session_cookies and not ddos_cookies:
        return None
    
    merged = {}
    if session_cookies:
        merged.update(session_cookies)
    if ddos_cookies:
        merged.update(ddos_cookies)
    
    return merged


def update_cookies_from_response(response: httpx.Response, 
                                cookie_manager: Optional[DDoSGuardCookieManager] = None) -> bool:
    """
    Update DDoS Guard cookies from an HTTP response
    
    :param response: HTTP response to extract cookies from
    :param cookie_manager: Optional cookie manager to update
    :return: True if any DDoS Guard cookies were found and updated
    """
    if not cookie_manager:
        return False
    
    return cookie_manager.update_from_response(response)