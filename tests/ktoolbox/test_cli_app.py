from __future__ import annotations

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
