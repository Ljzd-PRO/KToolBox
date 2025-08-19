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
    """Test PersistentWebUIState class functionality"""
    try:
        from ktoolbox.webui import PersistentWebUIState
        import tempfile
        import os
        from pathlib import Path
        
        # Use a temporary state file for testing
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_state_file = Path(temp_file.name)
        
        # Patch the STATE_FILE to use our temporary file
        with patch('ktoolbox.webui.STATE_FILE', temp_state_file):
            # Also mock the verify method to avoid thread checking in tests
            with patch.object(PersistentWebUIState, '_verify_running_operations'):
                state = PersistentWebUIState()
                
                # Test initial state
                assert not state.sync_creator_running
                assert not state.download_post_running
                assert len(state.logs) == 0
                
                # Test sync creator operations
                session_id = "test-session-123"
                state.start_sync_creator(session_id)
                assert state.sync_creator_running
                assert state.sync_creator_session_id == session_id
                assert state.sync_creator_running or state.download_post_running  # is_busy equivalent
                
                state.stop_sync_creator()
                assert not state.sync_creator_running
                assert state.sync_creator_session_id is None
                assert not (state.sync_creator_running or state.download_post_running)  # not busy
                
                # Test download post operations
                session_id2 = "test-session-456"
                state.start_download_post(session_id2)
                assert state.download_post_running
                assert state.download_post_session_id == session_id2
                assert state.sync_creator_running or state.download_post_running  # is_busy equivalent
                
                state.stop_download_post()
                assert not state.download_post_running
                assert state.download_post_session_id is None
                assert not (state.sync_creator_running or state.download_post_running)  # not busy
                
                # Test logging
                state.add_log("Test message")
                assert len(state.logs) == 1
                assert "Test message" in state.logs[0]
                
                # Test log clearing
                state.clear_logs()
                assert len(state.logs) == 0
        
        # Clean up
        try:
            temp_state_file.unlink()
        except:
            pass
        
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

def test_webui_state_persistence():
    """Test that state persists across instances"""
    try:
        from ktoolbox.webui import PersistentWebUIState
        import tempfile
        import os
        from pathlib import Path
        
        # Use a temporary state file for testing
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_state_file = Path(temp_file.name)
        
        # Patch the STATE_FILE to use our temporary file
        with patch('ktoolbox.webui.STATE_FILE', temp_state_file):
            # Also mock the verify method to avoid thread checking in tests
            with patch.object(PersistentWebUIState, '_verify_running_operations'):
                # Create first instance and modify state
                state1 = PersistentWebUIState()
                state1.start_sync_creator("session-123")
                state1.add_log("Persistent test message")
                
                # Create second instance - should load persisted state
                state2 = PersistentWebUIState()
                assert state2.sync_creator_running
                assert state2.sync_creator_session_id == "session-123"
                assert len(state2.logs) == 1
                assert "Persistent test message" in state2.logs[0]
        
        # Clean up
        try:
            temp_state_file.unlink()
        except:
            pass
        
    except ImportError as e:
        pytest.skip(f"WebUI dependencies not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__])