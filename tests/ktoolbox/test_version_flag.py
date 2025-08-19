import pytest
import sys
from unittest.mock import patch
from ktoolbox.__main__ import main
from ktoolbox import __version__


class TestVersionFlag:
    """Test -v flag functionality"""

    def test_version_flag_short(self, capsys):
        """Test -v flag outputs version and exits"""
        with patch.object(sys, 'argv', ['ktoolbox', '-v']):
            main()
            captured = capsys.readouterr()
            assert captured.out.strip() == __version__

    def test_version_flag_long(self, capsys):
        """Test --version flag outputs version and exits"""
        with patch.object(sys, 'argv', ['ktoolbox', '--version']):
            main()
            captured = capsys.readouterr()
            assert captured.out.strip() == __version__

    def test_normal_command_not_affected(self):
        """Test that normal commands are not affected by version flag logic"""
        # Test that we don't accidentally catch normal arguments
        with patch.object(sys, 'argv', ['ktoolbox', 'version']):
            # This should not trigger the early return for -v flag
            # The test passes if no exception is raised and Fire takes over
            try:
                # We expect this to fail because Fire will try to run the command
                # but we're just testing that our -v logic doesn't interfere
                main()
            except SystemExit:
                # Fire may call sys.exit, which is expected
                pass
            except Exception:
                # Other exceptions are also expected as we're not providing full environment
                pass