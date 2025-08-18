"""
Test for WebUI module
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock, patch

def test_webui_import():
    """Test that webui module can be imported"""
    try:
        import ktoolbox.webui as webui
        assert webui is not None
    except ImportError as e:
        pytest.skip(f"WebUI dependencies not available: {e}")

def test_webui_state():
    """Test WebUIState class functionality"""
    try:
        from ktoolbox.webui import WebUIState
        
        state = WebUIState()
        
        # Test initial state
        assert not state.is_busy()
        assert not state.sync_creator_running
        assert not state.download_post_running
        assert len(state.logs) == 0
        
        # Test sync creator operations
        state.start_sync_creator()
        assert state.sync_creator_running
        assert state.is_busy()
        
        state.stop_sync_creator()
        assert not state.sync_creator_running
        assert not state.is_busy()
        
        # Test download post operations
        state.start_download_post()
        assert state.download_post_running
        assert state.is_busy()
        
        state.stop_download_post()
        assert not state.download_post_running
        assert not state.is_busy()
        
        # Test logging
        state.add_log("Test message")
        assert len(state.logs) == 1
        assert "Test message" in state.logs[0]
        
    except ImportError as e:
        pytest.skip(f"WebUI dependencies not available: {e}")

@patch('ktoolbox.webui.st')
def test_webui_main_without_streamlit(mock_st):
    """Test webui main function behavior when streamlit is not available"""
    try:
        from ktoolbox.webui import main
        
        # Mock streamlit as None
        mock_st = None
        with patch('ktoolbox.webui.st', None):
            # Should not raise an exception
            main()
            
    except ImportError as e:
        pytest.skip(f"WebUI dependencies not available: {e}")

def test_webui_cli_integration():
    """Test that webui command is available in CLI"""
    try:
        from ktoolbox.cli import KToolBoxCli
        
        # Check that webui method exists
        assert hasattr(KToolBoxCli, 'webui')
        assert callable(getattr(KToolBoxCli, 'webui'))
        
        # Check method signature
        import inspect
        sig = inspect.signature(KToolBoxCli.webui)
        assert len(sig.parameters) == 0  # Should be a static method with no params
        
    except ImportError as e:
        pytest.skip(f"KToolBox dependencies not available: {e}")

if __name__ == "__main__":
    pytest.main([__file__])