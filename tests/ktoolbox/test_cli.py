from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ktoolbox.action import ActionRet
from ktoolbox.api.generated import CreatorProfile, Post, Revision
from ktoolbox.cli import KToolBoxCli


class ClientContext:
    def __init__(self, client: object) -> None:
        self.client = client

    async def __aenter__(self) -> object:
        return self.client

    async def __aexit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        return None


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
