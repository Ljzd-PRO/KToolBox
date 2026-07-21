from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from ktoolbox.action.job import CreatorJobGeneration
from ktoolbox.api.errors import PawchiveError
from ktoolbox.api.generated import CreatorSummary, Post
from ktoolbox.cli_app import app, run_cli, stderr, stdout
from ktoolbox.job.stream import DownloadSummary
from ktoolbox.project_config import CreatorReference
from ktoolbox.reporting import NullProgressReporter
from ktoolbox.sync import CreatorSyncResult, SyncSummary


def test_root_help_uses_hyphenated_commands(capsys) -> None:
    assert app(["--help"], result_action="return_int_as_exit_code_else_zero") == 0
    output = capsys.readouterr().out
    assert "download" in output
    assert "site-version" in output
    assert "download-post" not in output
    assert "download_post" not in output
    assert "--install-completion" in output
    assert "webui" in output


def test_webui_command_forwards_server_options(tmp_path: Path) -> None:
    project = tmp_path / "project"
    server = AsyncMock()
    with patch("ktoolbox.webui.server.run_webui", new=server):
        assert (
            app(
                [
                    "webui",
                    str(project),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "9000",
                    "--no-open",
                ]
            )
            == 0
        )
    server.assert_awaited_once_with(
        project,
        host="127.0.0.1",
        port=9000,
        open_browser=False,
    )


def test_webui_help_has_only_the_intended_no_open_flag(capsys) -> None:
    assert app(["webui", "--help"], result_action="return_int_as_exit_code_else_zero") == 0
    output = capsys.readouterr().out
    assert "--no-open" in output
    assert "--no-no-open" not in output


def test_webui_interrupt_returns_expected_status(capsys) -> None:
    with patch("ktoolbox.webui.server.run_webui", new=AsyncMock(side_effect=KeyboardInterrupt)):
        assert app(["webui"], result_action="return_int_as_exit_code_else_zero") == 130
    assert "WebUI stopped by user." in capsys.readouterr().err


def test_webui_hash_password_command(capsys) -> None:
    with patch("ktoolbox.webui.server.generate_password_hash", return_value="$argon2id$example"):
        assert app(["webui", "hash-password"]) == 0
    assert "$argon2id$example" in capsys.readouterr().out


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
                ["download-post", "--service", "fanbox", "--creator_id", "1", "--post_id", "2"],
                result_action="return_int_as_exit_code_else_zero",
            )
            == 0
        )
    download.assert_awaited_once()


def test_creator_roster_commands(tmp_path: Path, capsys) -> None:
    config = tmp_path / "ktoolbox.toml"
    common = ["--config", str(config)]

    assert run_cli(["creator", "add", "fanbox:123", "--alias", "artist", *common]) == 0
    assert run_cli(["creator", "disable", "artist", *common]) == 0
    capsys.readouterr()

    assert run_cli(["creator", "list", "--json", *common]) == 0
    roster = json.loads(capsys.readouterr().out)
    assert roster == [{"service": "fanbox", "creator_id": "123", "alias": "artist", "enabled": False}]

    assert run_cli(["creator", "remove", "artist", *common]) == 0
    assert run_cli(["config", "validate", *common]) == 0
    assert "0 creators" in capsys.readouterr().out


def test_creator_roster_command_reports_invalid_target(tmp_path: Path, capsys) -> None:
    result = run_cli(["creator", "add", "invalid", "--config", str(tmp_path / "ktoolbox.toml")])
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
        result = run_cli(
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


def test_meta_options_apply_project_path_progress_and_color(tmp_path: Path, capsys) -> None:
    project_path = tmp_path / "custom.toml"
    assert run_cli(["--config", str(project_path), "creator", "add", "fanbox:123"]) == 0
    capsys.readouterr()
    assert run_cli(["--config", str(project_path), "creator", "list", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["creator_id"] == "123"

    observed_color: list[tuple[bool | None, bool | None]] = []

    async def fake_download(**kwargs) -> None:
        observed_color.append((stdout.no_color, stderr.no_color))

    reporter = NullProgressReporter()
    stdout_no_color = stdout.no_color
    stderr_no_color = stderr.no_color
    with (
        patch("ktoolbox.cli_app.KToolBoxCli.download_post", new=fake_download),
        patch("ktoolbox.cli_app.create_progress_reporter", return_value=reporter) as factory,
    ):
        assert run_cli(["--plain", "--no-color", "download", "https://pawchive.pw/fanbox/user/1/post/2"]) == 0

    factory.assert_called_once_with(stderr, plain=True, quiet=False)
    assert observed_color == [(True, True)]
    assert stdout.no_color is stdout_no_color
    assert stderr.no_color is stderr_no_color

    with (
        patch("ktoolbox.cli_app.KToolBoxCli.download_post", new=AsyncMock(return_value=None)),
        patch("ktoolbox.cli_app.create_progress_reporter", return_value=reporter) as quiet_factory,
    ):
        assert run_cli(["--quiet", "download", "https://pawchive.pw/fanbox/user/1/post/2"]) == 0
    quiet_factory.assert_called_once_with(stderr, plain=False, quiet=True)


def test_meta_options_reject_conflicting_verbosity(capsys) -> None:
    assert run_cli(["--verbose", "--quiet", "site-version"]) == 2
    assert "cannot be used together" in capsys.readouterr().err


def test_query_commands_offer_tables_and_json(capsys) -> None:
    creator = CreatorSummary(
        favorited=0,
        id="123",
        indexed=0.0,
        name="Example Creator",
        service="fanbox",
        updated=0.0,
    )
    post = Post(id="456", user="123", service="fanbox", title="Example Post")

    with patch("ktoolbox.cli_app.KToolBoxCli.search_creator", new=AsyncMock(return_value=[creator])):
        assert app(["creator", "search", "--name", "Example", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["name"] == "Example Creator"

    with patch("ktoolbox.cli_app.KToolBoxCli.search_creator_post", new=AsyncMock(return_value=[post])):
        assert app(["post", "search", "--creator-id", "123"]) == 0
    post_table = capsys.readouterr().out
    assert "Post search results" in post_table
    assert "Example Post" in post_table

    with patch("ktoolbox.cli_app.KToolBoxCli.get_post", new=AsyncMock(return_value=post)):
        assert app(["post", "show", "fanbox", "123", "456", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["id"] == "456"


def test_download_maps_usage_and_file_failures_to_exit_codes(capsys) -> None:
    assert app(["download"]) == 2
    assert "Usage error" in capsys.readouterr().err

    with patch(
        "ktoolbox.cli_app.KToolBoxCli.download_post",
        new=AsyncMock(return_value="2 file downloads failed"),
    ):
        assert app(["download", "https://pawchive.pw/fanbox/user/1/post/2"]) == 1
    assert "Download failed" in capsys.readouterr().err


def test_query_commands_handle_empty_results_and_errors(capsys) -> None:
    creator = CreatorSummary(
        favorited=0,
        id="123",
        indexed=0.0,
        name="Example Creator",
        service="fanbox",
        updated=0.0,
    )
    post = Post(id="456", user="123", service="fanbox", title="Example Post")

    with patch("ktoolbox.cli_app.KToolBoxCli.search_creator", new=AsyncMock(return_value=[creator])):
        assert app(["creator", "search", "--name", "Example"]) == 0
    assert "Creator search results" in capsys.readouterr().out

    with patch("ktoolbox.cli_app.KToolBoxCli.search_creator", new=AsyncMock(return_value="None")):
        assert app(["creator", "search"]) == 0
    assert "No creators found" in capsys.readouterr().out

    with patch("ktoolbox.cli_app.KToolBoxCli.search_creator", new=AsyncMock(return_value="offline")):
        assert app(["creator", "search"]) == 1
    assert "Creator search failed" in capsys.readouterr().err

    with patch("ktoolbox.cli_app.KToolBoxCli.search_creator_post", new=AsyncMock(return_value=[post])):
        assert app(["post", "search", "--creator-id", "123", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["id"] == "456"

    with patch("ktoolbox.cli_app.KToolBoxCli.search_creator_post", new=AsyncMock(return_value="None")):
        assert app(["post", "search", "--creator-id", "123"]) == 0
    assert "No posts found" in capsys.readouterr().out

    with patch("ktoolbox.cli_app.KToolBoxCli.search_creator_post", new=AsyncMock(return_value="missing selector")):
        assert app(["post", "search"]) == 2
    assert "Post search failed" in capsys.readouterr().err

    with patch("ktoolbox.cli_app.KToolBoxCli.get_post", new=AsyncMock(return_value=post)):
        assert app(["post", "show", "fanbox", "123", "456"]) == 0
    assert "Post details" in capsys.readouterr().out

    with patch("ktoolbox.cli_app.KToolBoxCli.get_post", new=AsyncMock(return_value="not found")):
        assert app(["post", "show", "fanbox", "123", "missing"]) == 1
    assert "Post lookup failed" in capsys.readouterr().err


def test_config_helpers_and_roster_tables(tmp_path: Path, capsys) -> None:
    config = tmp_path / "ktoolbox.toml"
    common = ["--config", str(config)]
    assert run_cli(["creator", "add", "fanbox:123", "--alias", "artist", *common]) == 0
    capsys.readouterr()
    assert run_cli(["creator", "list", *common]) == 0
    assert "Creator roster" in capsys.readouterr().out

    assert run_cli(["creator", "enable", "missing", *common]) == 2
    assert "Configuration error" in capsys.readouterr().err
    assert run_cli(["creator", "remove", "missing", *common]) == 2
    capsys.readouterr()

    with patch("ktoolbox.cli_app.KToolBoxCli.config_editor", new=AsyncMock()) as edit:
        assert run_cli(["config", "edit", *common]) == 0
    edit.assert_awaited_once_with(config)

    with patch("ktoolbox.cli_app.KToolBoxCli.example_env", new=AsyncMock()) as example:
        assert app(["config", "example"]) == 0
    example.assert_awaited_once_with()

    assert run_cli(["config", "path", *common]) == 0
    assert str(config) in capsys.readouterr().out


def test_sync_validation_and_site_version_status_mapping(tmp_path: Path, capsys) -> None:
    assert run_cli(["sync", "--service", "fanbox", "--config", str(tmp_path / "missing.toml")]) == 2
    assert "must be used together" in capsys.readouterr().err

    assert (
        run_cli(
            [
                "sync",
                "fanbox:1",
                "--start-time",
                "not-a-date",
                "--config",
                str(tmp_path / "missing.toml"),
            ]
        )
        == 2
    )
    assert "Configuration error" in capsys.readouterr().err

    class ClientScope:
        def __init__(self, client: object) -> None:
            self.client = client

        async def __aenter__(self) -> object:
            return self.client

        async def __aexit__(self, *args: object) -> None:
            return None

    version_client = SimpleNamespace(get_app_version=AsyncMock(return_value="2026.7"))
    with patch("ktoolbox.cli_app.create_pawchive_client", return_value=ClientScope(version_client)):
        assert app(["site-version"]) == 0
    assert "2026.7" in capsys.readouterr().out

    version_client.get_app_version = AsyncMock(side_effect=PawchiveError("offline"))
    with patch("ktoolbox.cli_app.create_pawchive_client", return_value=ClientScope(version_client)):
        assert app(["site-version"]) == 1
    assert "Pawchive error" in capsys.readouterr().err
