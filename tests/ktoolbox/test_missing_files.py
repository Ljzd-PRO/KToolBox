from __future__ import annotations

import asyncio
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx
from loguru import logger

from ktoolbox._enum import RetCodeEnum
from ktoolbox.cli_app import run_cli
from ktoolbox.configuration import config
from ktoolbox.downloader import Downloader
from ktoolbox.downloader.missing_files import MissingFileHistory

FILE_ROOT = "https://file.pawchive.pw/data/fixture/"


@respx.mock
def test_sync_remembers_missing_files_but_only_skips_on_request(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    creator = "https://pawchive.pw/api/v1/fanbox/user/1"
    respx.get(creator + "/profile").respond(200, json={"id": "1", "service": "fanbox", "name": "Artist"})
    posts = respx.get(creator, params={"o": "0"})
    missing = respx.get(FILE_ROOT + "old.png").respond(404)
    new_missing = respx.get(FILE_ROOT + "new.png").respond(404)
    project = tmp_path / "project"
    project.mkdir()
    db = project / ".ktoolbox" / "missing-files.sqlite3"
    command = ["--plain", "--config", str(project / "ktoolbox.toml"), "sync", "fanbox:1", "-o", str(tmp_path / "other")]

    def publish(*names: str) -> None:
        posts.respond(
            200,
            json=[
                {
                    "id": "42",
                    "user": "1",
                    "service": "fanbox",
                    "attachments": [{"name": "same.png", "path": f"/fixture/{name}"} for name in names],
                }
            ],
        )

    publish("old.png")
    assert run_cli(command) == 1
    assert db.is_file()
    assert "1 missing on server (HTTP 404)" in " ".join(capsys.readouterr().out.split())
    assert run_cli(command) == 1
    assert missing.call_count == 2
    assert run_cli([*command, "--skip-missing"]) == 0
    assert missing.call_count == 2
    output = capsys.readouterr()
    assert "0 failed, 1 known missing skipped" in " ".join(output.out.split())
    assert "0 downloaded, 0 existing, 0 failed, 1 known missing skipped" in " ".join(output.err.split())

    publish("old.png", "new.png")
    assert run_cli([*command, "--skip-missing"]) == 1
    assert new_missing.call_count == 1
    assert missing.call_count == 2

    with closing(sqlite3.connect(db)) as connection, connection:
        connection.execute("UPDATE missing_files SET observed_at = ?", (time.time() - 8 * 86400,))
    publish("old.png")
    missing.respond(206, headers={"Content-Range": "bytes 0-2/3"}, content=b"PNG")
    assert run_cli([*command, "--skip-missing"]) == 0
    assert missing.call_count == 3
    with closing(sqlite3.connect(db)) as connection:
        assert (
            connection.execute(
                "SELECT 1 FROM missing_files WHERE key = ?",
                (MissingFileHistory.key(FILE_ROOT + "old.png", config.downloader.session_key),),
            ).fetchone()
            is None
        )


async def test_history_expiry_auth_scope_and_parallel_upserts(tmp_path: Path) -> None:
    db = tmp_path / "missing.sqlite3"
    write_only = MissingFileHistory(db, skip=False)
    history = MissingFileHistory(db, skip=True)
    keys = [history.key(FILE_ROOT + f"{i}.png?token=private", "session-secret") for i in range(12)]
    with patch("ktoolbox.downloader.missing_files.time.time", return_value=1000.0):
        await asyncio.gather(*(MissingFileHistory(db, skip=False).record(key) for key in keys))
        assert all(await asyncio.gather(*(history.should_skip(key) for key in keys)))
        assert not await write_only.should_skip(keys[0])
        assert not await history.should_skip(history.key(FILE_ROOT + "0.png?token=private", "other-session"))
    assert b"session-secret" not in db.read_bytes() and b"token=private" not in db.read_bytes()

    with patch("ktoolbox.downloader.missing_files.time.time", return_value=1000.0 + 7 * 86400 - 1):
        assert await history.should_skip(keys[0])
    with patch("ktoolbox.downloader.missing_files.time.time", return_value=1000.0 + 7 * 86400):
        assert not await history.should_skip(keys[0])


async def test_history_uses_only_records_before_the_current_sync(tmp_path: Path) -> None:
    db = tmp_path / "missing.sqlite3"
    current_run = MissingFileHistory(db, skip=True)
    await current_run.record("a")
    assert not await current_run.should_skip("a")
    assert await MissingFileHistory(db, skip=True).should_skip("a")


async def test_bad_history_is_a_single_warning_and_does_not_skip(tmp_path: Path) -> None:
    db = tmp_path / "not-a-database"
    db.write_bytes(b"invalid")
    history = MissingFileHistory(db, skip=True)
    messages: list[str] = []
    sink = logger.add(messages.append, level="WARNING")
    try:
        assert not await history.should_skip("first")
        await history.record("second")
        assert not await history.should_skip("second")
    finally:
        logger.remove(sink)
    assert len(messages) == 1
    assert "continuing without it" in messages[0]


@pytest.mark.parametrize("indirect", ["proxy", "redirect"])
async def test_indirect_404_does_not_poison_history(tmp_path: Path, indirect: str) -> None:
    config.downloader.reverse_proxy = "https://proxy.example/{}" if indirect == "proxy" else "{}"
    config.downloader.tps_limit = 1000
    history = MissingFileHistory(tmp_path / "missing.sqlite3", skip=True)
    url = FILE_ROOT + "file.png"
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if indirect == "redirect" and request.url.host == "file.pawchive.pw":
            return httpx.Response(302, headers={"Location": "https://elsewhere.example/missing"})
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        download = Downloader(url, tmp_path, client, server_path="/fixture/file.png", missing_files=history)
        assert (await download.run()).status_code == 404
        assert (await download.run()).status_code == 404
    assert calls == (2 if indirect == "proxy" else 4)
    assert not (tmp_path / "missing.sqlite3").exists()


async def test_existing_bucket_file_wins_over_missing_record(tmp_path: Path) -> None:
    config.downloader.use_bucket = True
    config.downloader.bucket_path = tmp_path / "bucket"
    bucket = config.downloader.bucket_path / "fixture" / "file.png"
    bucket.parent.mkdir(parents=True)
    bucket.write_bytes(b"existing")
    url = FILE_ROOT + "file.png"
    history = MissingFileHistory(tmp_path / "missing.sqlite3", skip=True)
    await history.record(history.key(url, config.downloader.session_key))
    history = MissingFileHistory(tmp_path / "missing.sqlite3", skip=True)
    assert await history.should_skip(history.key(url, config.downloader.session_key))

    def unexpectedly_requested(_: httpx.Request) -> httpx.Response:
        raise AssertionError("a file exists in the bucket")

    async with httpx.AsyncClient(transport=httpx.MockTransport(unexpectedly_requested)) as client:
        download = Downloader(url, tmp_path, client, server_path="/fixture/file.png", missing_files=history)
        assert (await download.run()).code == RetCodeEnum.FileExisted
    assert (tmp_path / "file.png").read_bytes() == b"existing"


@respx.mock
def test_sync_mixed_failures_do_not_record_temporary_failures_or_retryable_statuses(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    config.downloader.tps_limit = 1000
    config.downloader.retry_interval = 0.001
    config.downloader.retry_times = 2
    config.job.count = 1
    monkeypatch.setattr(Downloader, "_paused_until", 0.0)
    monkeypatch.setattr(Downloader, "_rate_limit_generation", 0)
    monkeypatch.setattr(Downloader, "_rate_limit_strikes", 0)
    base = "https://pawchive.pw/api/v1/fanbox/user/1"
    respx.get(base + "/profile").respond(200, json={"id": "1", "service": "fanbox", "name": "Artist"})
    temporary_url = "https://t2.pawchive.pw/d/demo.zip?key=private"
    work = {
        "id": "42",
        "user": "1",
        "service": "fanbox",
        "attachments": [
            *({"name": f"{code}.png", "path": f"/fixture/{code}.png"} for code in (404, 429, 503, 206)),
            {"name": "temp.zip", "deferred": True, "temp_download_url": temporary_url},
        ],
    }
    respx.get(base, params={"o": "0"}).respond(200, json=[work])
    respx.get(base + "/post/42").respond(200, json=work)
    missing, limited, server_error = [respx.get(FILE_ROOT + f"{code}.png").respond(code) for code in (404, 429, 503)]
    respx.get(FILE_ROOT + "206.png").respond(206, headers={"Content-Range": "bytes 0-2/3"}, content=b"PNG")
    respx.get(temporary_url).respond(404)

    assert run_cli(["--config", str(tmp_path / "ktoolbox.toml"), "sync", "fanbox:1", "--skip-missing"]) == 1
    assert missing.call_count == 1
    assert limited.call_count == server_error.call_count == 2
    out = " ".join(capsys.readouterr().out.split())
    assert (
        "1 downloaded, 0 existing, 4 failed (1 missing on server (HTTP 404), 2 retryable, 1 other non-retryable)" in out
    )
    with closing(sqlite3.connect(tmp_path / ".ktoolbox" / "missing-files.sqlite3")) as connection:
        records = connection.execute("SELECT key FROM missing_files").fetchall()
    assert records == [(MissingFileHistory.key(FILE_ROOT + "404.png", ""),)]
