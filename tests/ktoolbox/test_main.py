from __future__ import annotations

import sys
from unittest.mock import patch

from ktoolbox import __version__
from ktoolbox.__main__ import main


def test_version_and_help_skip_runtime_initialization(capsys) -> None:
    with (
        patch("ktoolbox.__main__.logger_init") as logger_init,
        patch("ktoolbox.__main__.uvloop_init") as uvloop_init,
    ):
        assert main(["--version"]) == 0
    assert capsys.readouterr().out.strip() == __version__
    logger_init.assert_not_called()
    uvloop_init.assert_not_called()

    assert main(["--help"]) == 0
    assert "Usage: ktoolbox COMMAND" in capsys.readouterr().out


def test_main_initializes_runtime_and_handles_interrupt() -> None:
    with (
        patch("ktoolbox.__main__.logger_init") as logger_init,
        patch("ktoolbox.__main__.uvloop_init") as uvloop_init,
        patch("ktoolbox.__main__.app", return_value=0) as app,
    ):
        assert main(["site-version"]) == 0
    logger_init.assert_called_once_with(cli_use=True)
    uvloop_init.assert_called_once_with()
    app.assert_called_once()

    with (
        patch("ktoolbox.__main__.app", side_effect=KeyboardInterrupt),
        patch("ktoolbox.__main__.logger.error") as error,
    ):
        assert main(["site-version"]) == 130
    error.assert_called_once()


def test_main_uses_sys_argv_when_not_provided() -> None:
    with patch.object(sys, "argv", ["ktoolbox", "--help"]), patch("ktoolbox.__main__.app", return_value=0) as app:
        assert main() == 0
    app.assert_called_once()
