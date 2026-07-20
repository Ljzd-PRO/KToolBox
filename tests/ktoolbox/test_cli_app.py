from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from ktoolbox.action.job import CreatorJobGeneration
from ktoolbox.cli_app import app
from ktoolbox.job.stream import DownloadSummary
from ktoolbox.project_config import CreatorReference
from ktoolbox.sync import CreatorSyncResult, SyncSummary


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


def test_sync_accepts_multiple_targets_and_returns_partial_failure(tmp_path: Path, capsys) -> None:
    class ClientScope:
        async def __aenter__(self) -> object:
            return object()

        async def __aexit__(self, *args: object) -> None:
            return None

    creators = [CreatorReference(service="fanbox", creator_id=value) for value in ("1", "2")]
    summary = SyncSummary(
        creators=[
            CreatorSyncResult(
                creator=creators[0],
                generation=CreatorJobGeneration(accepted_posts=1, generated_jobs=1),
            ),
            CreatorSyncResult(creator=creators[1], error="failed"),
        ],
        downloads=DownloadSummary(total=1, completed=1),
    )
    coordinator = SimpleNamespace(run=AsyncMock(return_value=summary))

    with (
        patch("ktoolbox.cli_app.create_pawchive_client", return_value=ClientScope()),
        patch("ktoolbox.cli_app.SyncCoordinator", return_value=coordinator) as coordinator_type,
    ):
        result = app(
            [
                "sync",
                "fanbox:1",
                "https://pawchive.pw/fanbox/user/2",
                "--config",
                str(tmp_path / "missing.toml"),
                "--length",
                "1",
            ]
        )

    assert result == 1
    assert "Synchronization summary" in capsys.readouterr().out
    selected, options = coordinator.run.await_args.args
    assert [creator.key for creator in selected] == ["fanbox:1", "fanbox:2"]
    assert options.length == 1
    coordinator_type.assert_called_once()
