from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import BaseModel, ValidationError
from pydantic_settings import SettingsError

from ktoolbox import __version__
from ktoolbox.__main__ import main
from ktoolbox.cli_app import stderr
from ktoolbox.exceptions import KToolBoxUserError


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
        patch("ktoolbox.__main__.run_cli", return_value=0) as run_cli,
    ):
        assert main(["site-version"]) == 0
    logger_init.assert_called_once_with(cli_use=True, console=stderr, verbose=False, quiet=False)
    uvloop_init.assert_called_once_with()
    run_cli.assert_called_once_with(["site-version"])

    with (
        patch("ktoolbox.__main__.run_cli", side_effect=KeyboardInterrupt),
        patch("ktoolbox.__main__.logger.error") as error,
    ):
        assert main(["site-version"]) == 130
    error.assert_called_once_with("KToolBox was forcefully stopped by the user")


def test_main_logs_expected_refusals_without_tracebacks() -> None:
    with (
        patch("ktoolbox.__main__.logger_init"),
        patch("ktoolbox.__main__.uvloop_init"),
        patch(
            "ktoolbox.__main__.run_cli",
            side_effect=KToolBoxUserError("account password is missing", label="Configuration error"),
        ),
        patch("ktoolbox.__main__.logger.error") as error,
    ):
        assert main(["webui"]) == 2
    error.assert_called_once_with("Configuration error: account password is missing")

    class FixtureConfiguration(BaseModel):
        password: int

    try:
        FixtureConfiguration.model_validate({"password": "do-not-print-this"})
    except ValidationError as validation_error:
        with (
            patch("ktoolbox.__main__.logger_init"),
            patch("ktoolbox.__main__.uvloop_init"),
            patch("ktoolbox.__main__.run_cli", side_effect=validation_error),
            patch("ktoolbox.__main__.logger.error") as error,
        ):
            assert main(["sync"]) == 2
    message = error.call_args.args[0]
    assert message.startswith("Configuration error: password:")
    assert "do-not-print-this" not in message
    assert "Traceback" not in message


@pytest.mark.parametrize(
    ("exception", "exit_code", "message"),
    [
        (SettingsError("cannot read settings"), 2, "Configuration error: cannot read settings"),
        (PermissionError("output is read-only"), 1, "System error: output is read-only"),
    ],
)
def test_main_logs_operational_errors(exception: Exception, exit_code: int, message: str) -> None:
    with (
        patch("ktoolbox.__main__.logger_init"),
        patch("ktoolbox.__main__.uvloop_init"),
        patch("ktoolbox.__main__.run_cli", side_effect=exception),
        patch("ktoolbox.__main__.logger.error") as error,
    ):
        assert main(["sync"]) == exit_code
    error.assert_called_once_with(message)


def test_main_does_not_hide_unexpected_programming_errors() -> None:
    with (
        patch("ktoolbox.__main__.logger_init"),
        patch("ktoolbox.__main__.uvloop_init"),
        patch("ktoolbox.__main__.run_cli", side_effect=RuntimeError("unexpected defect")),
        pytest.raises(RuntimeError, match="unexpected defect"),
    ):
        main(["sync"])


def test_main_uses_sys_argv_when_not_provided() -> None:
    with (
        patch.object(sys, "argv", ["ktoolbox", "--help"]),
        patch("ktoolbox.__main__.run_cli", return_value=0) as run_cli,
    ):
        assert main() == 0
    run_cli.assert_called_once_with(["--help"])


def test_no_arguments_show_help_and_unknown_commands_suggest_fix(capsys) -> None:
    with patch("ktoolbox.__main__.logger_init"), patch("ktoolbox.__main__.uvloop_init"):
        assert main([]) == 0
        assert "Usage: ktoolbox COMMAND" in capsys.readouterr().out

        assert main(["synx"]) == 2
    captured = capsys.readouterr()
    assert 'Did you mean "sync"?' in captured.err
    assert "Traceback" not in captured.err


def test_legacy_warning_is_emitted_with_leading_global_options() -> None:
    with (
        patch("ktoolbox.__main__.logger_init"),
        patch("ktoolbox.__main__.uvloop_init"),
        patch("ktoolbox.__main__.run_cli", return_value=0),
        patch("ktoolbox.__main__.logger.warning") as warning,
    ):
        assert main(["--plain", "download-post", "--service", "fanbox"]) == 0
    warning.assert_called_once()


def test_help_never_invokes_hostile_pager(tmp_path: Path) -> None:
    marker = tmp_path / "pager-was-run"
    pager = tmp_path / "pager"
    pager.write_text(f"#!/bin/sh\ntouch '{marker}'\nsleep 10\n", encoding="utf-8")
    pager.chmod(0o755)
    environment = os.environ.copy()
    environment["PAGER"] = str(pager)

    result = subprocess.run(
        [sys.executable, "-m", "ktoolbox", "--help"],
        cwd=Path(__file__).parents[2],
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )

    assert result.returncode == 0
    assert "Usage: ktoolbox COMMAND" in result.stdout
    assert not marker.exists()


def test_terminal_password_refusal_has_no_traceback() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "ktoolbox", "webui", "hash-password"],
        cwd=Path(__file__).parents[2],
        input="",
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )

    assert result.returncode == 2
    assert "Password error: password input was cancelled" in result.stderr
    assert "Traceback" not in result.stderr


def test_terminal_webui_configuration_refusal_has_no_traceback(tmp_path: Path) -> None:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("KTOOLBOX_")}
    environment.update(
        {
            "KTOOLBOX_WEBUI__USERNAME": "owner",
            "KTOOLBOX_WEBUI__PASSWORD_HASH": "not-an-argon-hash",
        }
    )
    result = subprocess.run(
        [sys.executable, "-m", "ktoolbox", "webui", str(tmp_path), "--no-open"],
        cwd=Path(__file__).parents[2],
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )

    assert result.returncode == 2
    assert "Configuration error:" in result.stderr
    assert "not a valid Argon2 hash" in result.stderr
    assert "Traceback" not in result.stderr
