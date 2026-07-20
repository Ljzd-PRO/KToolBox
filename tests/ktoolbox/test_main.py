from __future__ import annotations

import sys
from unittest.mock import patch

from ktoolbox import __version__
from ktoolbox.__main__ import main
from ktoolbox.cli import KToolBoxCli


def test_version_flag_short_circuits(capsys) -> None:
    with patch.object(sys, "argv", ["ktoolbox", "--version"]), patch("ktoolbox.__main__.fire.Fire") as fire:
        main()
    assert capsys.readouterr().out.strip() == __version__
    fire.assert_not_called()


def test_main_initializes_runtime_and_handles_interrupt() -> None:
    with (
        patch.object(sys, "argv", ["ktoolbox"]),
        patch("ktoolbox.__main__.logger_init") as logger_init,
        patch("ktoolbox.__main__.uvloop_init") as uvloop_init,
        patch("ktoolbox.__main__.fire.Fire") as fire,
    ):
        main()
    logger_init.assert_called_once_with(cli_use=True)
    uvloop_init.assert_called_once_with()
    fire.assert_called_once_with(KToolBoxCli)

    with (
        patch.object(sys, "argv", ["ktoolbox"]),
        patch("ktoolbox.__main__.fire.Fire", side_effect=KeyboardInterrupt),
        patch("ktoolbox.__main__.logger.error") as error,
    ):
        main()
    error.assert_called_once()
