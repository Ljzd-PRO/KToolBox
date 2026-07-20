from __future__ import annotations

import builtins
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from ktoolbox import __version__
from ktoolbox._enum import RetCodeEnum, TextEnum
from ktoolbox.action import ActionRet
from ktoolbox.action.fetch import FetchInterruptError
from ktoolbox.api.errors import PawchiveHTTPError, PawchiveNotFoundError
from ktoolbox.api.generated import CreatorProfile, Post, Revision
from ktoolbox.cli import KToolBoxCli, _requested_post
from ktoolbox.configuration import config
from ktoolbox.job import Job


class ClientContext:
    def __init__(self, client: object) -> None:
        self.client = client

    async def __aenter__(self) -> object:
        return self.client

    async def __aexit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        return None


def api_error(status: int = 500) -> PawchiveHTTPError:
    request = httpx.Request("GET", "https://example.test/resource")
    response = httpx.Response(status, request=request)
    if status == 404:
        return PawchiveNotFoundError(response)
    return PawchiveHTTPError(response)


@pytest.fixture(autouse=True)
def reset_update_check() -> None:
    KToolBoxCli._update_checked = False


@pytest.mark.asyncio
async def test_site_version_uses_pawchive_client() -> None:
    client = SimpleNamespace(get_app_version=AsyncMock(return_value="custom"))
    with patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)):
        assert await KToolBoxCli.site_version() == "custom"
    client.get_app_version.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_get_post_selects_revision_from_list(tmp_path) -> None:
    revision = Revision(id="post", user="creator", service="fanbox", revision_id=7)
    client = SimpleNamespace(
        get_post=AsyncMock(),
        list_post_revisions=AsyncMock(return_value=[revision]),
    )
    dump_path = tmp_path / "revision.json"

    with patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)):
        result = await KToolBoxCli.get_post("fanbox", "creator", "post", "7", dump=dump_path)

    assert result == revision
    assert dump_path.exists()
    client.get_post.assert_not_awaited()
    client.list_post_revisions.assert_awaited_once_with("fanbox", "creator", "post")


@pytest.mark.asyncio
async def test_download_post_reuses_client_for_job_generation(tmp_path) -> None:
    post = Post(id="post", user="creator", service="fanbox", title="Example")
    client = SimpleNamespace(get_post=AsyncMock(return_value=post))
    runner = Mock()
    runner.start = AsyncMock(return_value=0)

    with (
        patch("ktoolbox.cli.check_for_updates", new_callable=AsyncMock),
        patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)),
        patch("ktoolbox.cli.create_job_from_post", new_callable=AsyncMock, return_value=[]) as create_jobs,
        patch("ktoolbox.cli.JobRunner", return_value=runner),
    ):
        result = await KToolBoxCli.download_post(
            service="fanbox",
            creator_id="creator",
            post_id="post",
            path=tmp_path,
        )

    assert result is None
    assert create_jobs.await_args.kwargs["client"] is client
    runner.start.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_download_post_reports_worker_failures(tmp_path) -> None:
    post = Post(id="post", user="creator", service="fanbox")
    client = SimpleNamespace(get_post=AsyncMock(return_value=post))
    runner = Mock(start=AsyncMock(return_value=2))

    with (
        patch("ktoolbox.cli.check_for_updates", new_callable=AsyncMock),
        patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)),
        patch("ktoolbox.cli.create_job_from_post", new_callable=AsyncMock, return_value=[]),
        patch("ktoolbox.cli.JobRunner", return_value=runner),
    ):
        result = await KToolBoxCli.download_post(
            service="fanbox",
            creator_id="creator",
            post_id="post",
            path=tmp_path,
        )

    assert result == "2 file downloads failed"


@pytest.mark.asyncio
async def test_sync_creator_uses_profile_and_reuses_client(tmp_path) -> None:
    profile = CreatorProfile(id="creator", name="Display Name", service="fanbox")
    client = SimpleNamespace(
        get_creator_profile=AsyncMock(return_value=profile),
        list_creators=AsyncMock(),
    )
    runner = Mock()
    runner.start = AsyncMock(return_value=0)

    with (
        patch("ktoolbox.cli.check_for_updates", new_callable=AsyncMock),
        patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)),
        patch(
            "ktoolbox.cli.create_job_from_creator",
            new_callable=AsyncMock,
            return_value=ActionRet(data=[]),
        ) as create_jobs,
        patch("ktoolbox.cli.JobRunner", return_value=runner),
    ):
        result = await KToolBoxCli.sync_creator(
            service="fanbox",
            creator_id="creator",
            path=tmp_path,
            length=1,
        )

    assert result is None
    client.get_creator_profile.assert_awaited_once_with("fanbox", "creator")
    client.list_creators.assert_not_awaited()
    assert create_jobs.await_args.kwargs["client"] is client
    assert create_jobs.await_args.kwargs["length"] == 1
    runner.start.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_download_post_rejects_missing_identity_without_client() -> None:
    with patch("ktoolbox.cli.create_pawchive_client") as factory:
        result = await KToolBoxCli.download_post()
    assert "Required parameters are missing" in result
    factory.assert_not_called()


@pytest.mark.asyncio
async def test_requested_post_direct_and_missing_revision() -> None:
    item = Post(id="post", user="creator", service="fanbox")
    client = SimpleNamespace(
        get_post=AsyncMock(return_value=item),
        list_post_revisions=AsyncMock(return_value=[]),
    )
    assert await _requested_post(client, "fanbox", "creator", "post", None) is item
    with pytest.raises(LookupError, match="Revision 7"):
        await _requested_post(client, "fanbox", "creator", "post", "7")


@pytest.mark.asyncio
async def test_version_update_check_once_and_site_error() -> None:
    with patch("ktoolbox.cli.check_for_updates", new_callable=AsyncMock) as check:
        assert await KToolBoxCli.version() == __version__
        check.assert_awaited_once_with()

    with patch("ktoolbox.cli.check_for_updates", new_callable=AsyncMock, side_effect=RuntimeError("offline")) as check:
        await KToolBoxCli._ensure_update_check()
        await KToolBoxCli._ensure_update_check()
    check.assert_awaited_once_with()

    client = SimpleNamespace(get_app_version=AsyncMock(side_effect=api_error()))
    with patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)):
        assert "HTTP 500" in await KToolBoxCli.site_version()


@pytest.mark.asyncio
async def test_config_editor_and_example_env(capsys) -> None:
    editor = ModuleType("ktoolbox.editor")
    editor.run_config_editor = Mock()
    with patch.dict(sys.modules, {"ktoolbox.editor": editor}):
        await KToolBoxCli.config_editor()
    editor.run_config_editor.assert_called_once_with()

    editor.run_config_editor.reset_mock()
    project_path = Path("custom.toml")
    with patch.dict(sys.modules, {"ktoolbox.editor": editor}):
        await KToolBoxCli.config_editor(project_path)
    editor.run_config_editor.assert_called_once_with(project_path)

    real_import = builtins.__import__

    def missing_editor(name: str, *args: object, **kwargs: object):
        if name == "ktoolbox.editor":
            raise ModuleNotFoundError(name)
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=missing_editor), patch("ktoolbox.cli.logger.error") as error:
        await KToolBoxCli.config_editor()
    error.assert_called_once()

    with patch("ktoolbox.cli.render", return_value="KTOOLBOX_API__NETLOC=pawchive.pw") as render:
        await KToolBoxCli.example_env()
    assert "pawchive.pw" in capsys.readouterr().out
    render.assert_called_once()


@pytest.mark.asyncio
async def test_cli_search_commands_cover_success_empty_dump_and_failure(tmp_path: Path) -> None:
    client = object()
    creator = CreatorProfile(id="creator", name="Name", service="fanbox")
    item = Post(id="post", user="creator", service="fanbox")

    with (
        patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)),
        patch(
            "ktoolbox.cli.search_creator_action", new_callable=AsyncMock, return_value=ActionRet(data=iter([creator]))
        ),
        patch("ktoolbox.cli.dump_search", new_callable=AsyncMock) as dump,
    ):
        assert await KToolBoxCli.search_creator(name="Name", dump=tmp_path / "creators.json") == [creator]
    dump.assert_awaited_once()

    with (
        patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)),
        patch("ktoolbox.cli.search_creator_action", new_callable=AsyncMock, return_value=ActionRet(data=iter(()))),
    ):
        assert await KToolBoxCli.search_creator() == TextEnum.SearchResultEmpty.value

    failure = ActionRet(code=RetCodeEnum.GeneralFailure, message="failed")
    with (
        patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)),
        patch("ktoolbox.cli.search_creator_action", new_callable=AsyncMock, return_value=failure),
    ):
        assert await KToolBoxCli.search_creator() == "failed"

    with (
        patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)),
        patch("ktoolbox.cli.search_creator_post_action", new_callable=AsyncMock, return_value=ActionRet(data=[item])),
        patch("ktoolbox.cli.dump_search", new_callable=AsyncMock) as dump,
    ):
        assert await KToolBoxCli.search_creator_post(id="creator", dump=tmp_path / "posts.json") == [item]
    dump.assert_awaited_once()

    with (
        patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)),
        patch("ktoolbox.cli.search_creator_post_action", new_callable=AsyncMock, return_value=ActionRet(data=[])),
    ):
        assert await KToolBoxCli.search_creator_post(id="creator") == TextEnum.SearchResultEmpty.value

    with (
        patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)),
        patch("ktoolbox.cli.search_creator_post_action", new_callable=AsyncMock, return_value=failure),
    ):
        assert await KToolBoxCli.search_creator_post(id="creator") == "failed"


@pytest.mark.asyncio
async def test_get_post_maps_missing_revision_error() -> None:
    client = SimpleNamespace(list_post_revisions=AsyncMock(return_value=[]))
    with patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)):
        assert "Revision 7 was not found" in await KToolBoxCli.get_post("fanbox", "creator", "post", "7")


@pytest.mark.asyncio
async def test_download_post_url_revision_expansion_and_errors(tmp_path: Path) -> None:
    item = Post(id="post", user="creator", service="fanbox", title="Title")
    revision = Revision(id="post", user="creator", service="fanbox", title="Revision", revision_id=7)
    job = Job(path=tmp_path, server_path="/file")
    client = SimpleNamespace(
        get_post=AsyncMock(return_value=item),
        list_post_revisions=AsyncMock(return_value=[revision]),
    )
    runner = Mock()
    runner.start = AsyncMock(return_value=0)
    config.job.include_revisions = True

    with (
        patch("ktoolbox.cli.check_for_updates", new_callable=AsyncMock),
        patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)),
        patch("ktoolbox.cli.create_job_from_post", new_callable=AsyncMock, side_effect=[[job], [job]]) as create,
        patch("ktoolbox.cli.JobRunner", return_value=runner) as runner_factory,
    ):
        assert (
            await KToolBoxCli.download_post(
                url="https://pawchive.pw/fanbox/user/creator/post/post",
                path=str(tmp_path),
            )
            is None
        )
    assert create.await_count == 2
    assert runner_factory.call_args.kwargs["job_list"] == [job, job]

    client.list_post_revisions.side_effect = api_error(404)
    create.reset_mock(side_effect=True)
    create.return_value = [job]
    with (
        patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)),
        patch("ktoolbox.cli.create_job_from_post", create),
        patch("ktoolbox.cli.JobRunner", return_value=runner),
    ):
        assert (
            await KToolBoxCli.download_post(service="fanbox", creator_id="creator", post_id="post", path=tmp_path)
            is None
        )
    assert create.await_count == 1

    failure = api_error()
    with (
        patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)),
        patch("ktoolbox.cli._requested_post", new_callable=AsyncMock, side_effect=FetchInterruptError(failure)),
    ):
        assert "HTTP 500" in await KToolBoxCli.download_post(
            service="fanbox",
            creator_id="creator",
            post_id="post",
        )


@pytest.mark.asyncio
async def test_sync_creator_url_dates_keywords_and_failures(tmp_path: Path) -> None:
    profile = CreatorProfile(id="creator", name="", service="fanbox")
    client = SimpleNamespace(get_creator_profile=AsyncMock(return_value=profile))
    runner = Mock()
    runner.start = AsyncMock(return_value=0)

    with (
        patch("ktoolbox.cli.check_for_updates", new_callable=AsyncMock),
        patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)),
        patch(
            "ktoolbox.cli.create_job_from_creator", new_callable=AsyncMock, return_value=ActionRet(data=[])
        ) as create,
        patch("ktoolbox.cli.JobRunner", return_value=runner),
    ):
        assert (
            await KToolBoxCli.sync_creator(
                url="https://pawchive.pw/fanbox/user/creator",
                path=str(tmp_path),
                start_time="2025-01-01",
                end_time="2025-01-31",
                keywords="keep",
                keywords_exclude=("block",),
            )
            is None
        )
    assert create.await_args.kwargs["all_pages"] is True
    assert create.await_args.kwargs["keywords"] == {"keep"}
    assert create.await_args.kwargs["keywords_exclude"] == {"block"}
    assert create.await_args.kwargs["start_time"].year == 2025
    assert (tmp_path / "creator").is_dir()

    with patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)):
        assert "does not match format" in await KToolBoxCli.sync_creator(
            service="fanbox",
            creator_id="creator",
            start_time="invalid",
        )

    with (
        patch("ktoolbox.cli.create_pawchive_client", return_value=ClientContext(client)),
        patch(
            "ktoolbox.cli.create_job_from_creator",
            new_callable=AsyncMock,
            return_value=ActionRet(code=RetCodeEnum.GeneralFailure, message="generation failed"),
        ),
    ):
        assert await KToolBoxCli.sync_creator(service="fanbox", creator_id="creator") == "generation failed"
