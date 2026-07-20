from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

from ktoolbox.cli_app import app


def test_root_help_uses_hyphenated_commands(capsys) -> None:
    assert app(["--help"], result_action="return_int_as_exit_code_else_zero") == 0
    output = capsys.readouterr().out
    assert "download" in output
    assert "site-version" in output
    assert "download-post" not in output
    assert "download_post" not in output


def test_download_uses_friendly_option_names() -> None:
    with patch("ktoolbox.cli_app.KToolBoxCli.download_post", new=AsyncMock(return_value=None)) as download:
        assert (
            app(
                ["download", "https://pawchive.pw/fanbox/user/1/post/2", "--output", "downloads"],
                result_action="return_int_as_exit_code_else_zero",
            )
            == 0
        )
    download.assert_awaited_once()
    assert str(download.await_args.kwargs["path"]) == "downloads"


def test_legacy_download_alias_keeps_signature() -> None:
    with patch("ktoolbox.cli_app.KToolBoxCli.download_post", new=AsyncMock(return_value=None)) as download:
        assert (
            app(
                ["download-post", "--service", "fanbox", "--creator-id", "1", "--post-id", "2"],
                result_action="return_int_as_exit_code_else_zero",
            )
            == 0
        )
    download.assert_awaited_once()


def test_creator_roster_commands(tmp_path: Path, capsys) -> None:
    config = tmp_path / "ktoolbox.toml"
    common = ["--config", str(config)]

    assert app(["creator", "add", "fanbox:123", "--alias", "artist", *common]) == 0
    assert app(["creator", "disable", "artist", *common]) == 0
    capsys.readouterr()

    assert app(["creator", "list", "--json", *common]) == 0
    roster = json.loads(capsys.readouterr().out)
    assert roster == [{"service": "fanbox", "creator_id": "123", "alias": "artist", "enabled": False}]

    assert app(["creator", "remove", "artist", *common]) == 0
    assert app(["config", "validate", *common]) == 0
    assert "0 creators" in capsys.readouterr().out


def test_creator_roster_command_reports_invalid_target(tmp_path: Path, capsys) -> None:
    result = app(["creator", "add", "invalid", "--config", str(tmp_path / "ktoolbox.toml")])
    assert result == 2
    assert "Configuration error" in capsys.readouterr().err
