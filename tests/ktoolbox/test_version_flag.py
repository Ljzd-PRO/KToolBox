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
        # Test that we don't accidentally catch normal arguments before Fire takes over.
        with patch.object(sys, 'argv', ['ktoolbox', 'version']), \
                patch('ktoolbox.__main__.logger_init'), \
                patch('ktoolbox.__main__.uvloop_init'), \
                patch('ktoolbox.__main__.fire.Fire') as mock_fire:
            main()

        mock_fire.assert_called_once()
