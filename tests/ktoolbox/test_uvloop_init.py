import sys
import pytest
from unittest.mock import patch, MagicMock

from ktoolbox.utils import uvloop_init
from ktoolbox.configuration import config


class TestUvloopInit:
    """Test uvloop_init function for both Windows and Unix-like systems."""

    def test_uvloop_init_disabled(self):
        """Test that uvloop_init returns False when use_uvloop is disabled."""
        with patch.object(config, 'use_uvloop', False):
            result = uvloop_init()
            assert result is False

    @patch('sys.platform', 'win32')
    def test_winloop_init_success_on_windows(self):
        """Test successful winloop initialization on Windows."""
        mock_winloop = MagicMock()
        mock_policy = MagicMock()
        mock_winloop.EventLoopPolicy.return_value = mock_policy
        
        with patch.object(config, 'use_uvloop', True), \
             patch('ktoolbox.utils.asyncio.set_event_loop_policy') as mock_set_policy, \
             patch.dict('sys.modules', {'winloop': mock_winloop}):
            
            result = uvloop_init()
            
            assert result is True
            mock_set_policy.assert_called_once_with(mock_policy)

    @patch('sys.platform', 'win32')
    def test_winloop_init_missing_on_windows(self):
        """Test winloop initialization when winloop is not installed on Windows."""
        with patch.object(config, 'use_uvloop', True), \
             patch('builtins.__import__', side_effect=ModuleNotFoundError):
            
            result = uvloop_init()
            
            assert result is False

    @patch('sys.platform', 'linux')
    def test_uvloop_init_success_on_unix(self):
        """Test successful uvloop initialization on Unix-like systems."""
        mock_uvloop = MagicMock()
        mock_policy = MagicMock()
        mock_uvloop.EventLoopPolicy.return_value = mock_policy
        
        with patch.object(config, 'use_uvloop', True), \
             patch('ktoolbox.utils.asyncio.set_event_loop_policy') as mock_set_policy, \
             patch.dict('sys.modules', {'uvloop': mock_uvloop}):
            
            result = uvloop_init()
            
            assert result is True
            mock_set_policy.assert_called_once_with(mock_policy)

    @patch('sys.platform', 'linux')
    def test_uvloop_init_missing_on_unix(self):
        """Test uvloop initialization when uvloop is not installed on Unix-like systems."""
        with patch.object(config, 'use_uvloop', True), \
             patch('builtins.__import__', side_effect=ModuleNotFoundError):
            
            result = uvloop_init()
            
            assert result is False

    @patch('sys.platform', 'darwin')
    def test_uvloop_init_on_macos(self):
        """Test uvloop initialization on macOS (should use uvloop, not winloop)."""
        mock_uvloop = MagicMock()
        mock_policy = MagicMock()
        mock_uvloop.EventLoopPolicy.return_value = mock_policy
        
        with patch.object(config, 'use_uvloop', True), \
             patch('ktoolbox.utils.asyncio.set_event_loop_policy') as mock_set_policy, \
             patch.dict('sys.modules', {'uvloop': mock_uvloop}):
            
            result = uvloop_init()
            
            assert result is True
            mock_set_policy.assert_called_once_with(mock_policy)