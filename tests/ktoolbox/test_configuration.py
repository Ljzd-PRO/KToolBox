from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

from ktoolbox.configuration import (
    Configuration,
    DownloaderConfiguration,
    RuntimeContext,
    active_configuration,
    config,
    configuration_scope,
    load_configuration,
)


def test_pawchive_defaults_and_nested_environment(monkeypatch) -> None:
    defaults = Configuration(_env_file=None)
    assert defaults.api.netloc == "pawchive.pw"
    assert defaults.api.path == "/api/v1"
    assert defaults.downloader.files_netloc == "file.pawchive.pw"
    assert defaults.downloader.file_path_prefix == "/data"
    assert not hasattr(defaults.api, "session_key")

    monkeypatch.setenv("KTOOLBOX_API__NETLOC", "api.example.test")
    monkeypatch.setenv("KTOOLBOX_DOWNLOADER__SESSION_KEY", "download-only")
    monkeypatch.setenv("KTOOLBOX_JOB__DOWNLOAD_ATTACHMENTS", "false")
    monkeypatch.setenv("KTOOLBOX_JOB__CREATOR_CONCURRENCY", "7")
    configured = Configuration(_env_file=None)
    assert configured.api.netloc == "api.example.test"
    assert configured.downloader.session_key == "download-only"
    assert configured.job.download_attachments is False
    assert configured.job.creator_concurrency == 7
    assert configured.webui.host == "0.0.0.0"
    assert configured.webui.port == 8789
    assert configured.webui.max_active_tasks == 2
    assert configured.webui.password.get_secret_value() == ""


def test_project_configuration_uses_project_dotenv_priority(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("KTOOLBOX_API__NETLOC", raising=False)
    (tmp_path / ".env").write_text("KTOOLBOX_API__NETLOC=base.example\n", encoding="utf-8")
    (tmp_path / "prod.env").write_text(
        "KTOOLBOX_API__NETLOC=prod.example\nKTOOLBOX_WEBUI__PORT=9000\n",
        encoding="utf-8",
    )

    configured = load_configuration(tmp_path)

    assert configured.api.netloc == "prod.example"
    assert configured.webui.port == 9000


def test_runtime_context_isolates_concurrent_async_tasks(tmp_path: Path) -> None:
    first = RuntimeContext(tmp_path / "first", Configuration(_env_file=None, api={"netloc": "first.example"}))
    second = RuntimeContext(tmp_path / "second", Configuration(_env_file=None, api={"netloc": "second.example"}))

    async def read_context(context: RuntimeContext) -> tuple[str, Path]:
        with context.activate():
            await asyncio.sleep(0)
            return config.api.netloc, context.project_root

    async def run() -> list[tuple[str, Path]]:
        return await asyncio.gather(read_context(first), read_context(second))

    assert asyncio.run(run()) == [
        ("first.example", tmp_path / "first"),
        ("second.example", tmp_path / "second"),
    ]
    assert active_configuration() is not first.configuration


def test_configuration_scope_restores_default_and_snapshot_redacts_secrets(tmp_path: Path) -> None:
    configured = Configuration(
        _env_file=None,
        downloader={"session_key": "cookie"},
        webui={"password": "plain", "password_hash": "hash"},
    )
    context = RuntimeContext(tmp_path, configured)
    previous = active_configuration()

    with configuration_scope(configured):
        assert config.downloader.session_key == "cookie"
    assert active_configuration() is previous

    snapshot = context.snapshot()
    snapshot.configuration.api.netloc = "changed.example"
    assert context.configuration.api.netloc == "pawchive.pw"
    redacted = context.redacted_configuration()
    assert "session_key" not in redacted["downloader"]
    assert "password" not in redacted["webui"]
    assert "password_hash" not in redacted["webui"]


def test_bucket_validator_accepts_hardlink_capable_directory(tmp_path: Path) -> None:
    bucket = tmp_path / "bucket"
    configured = DownloaderConfiguration(use_bucket=True, bucket_path=bucket)
    assert configured.use_bucket is True
    assert bucket.is_dir()
    assert list(bucket.iterdir()) == []


def test_bucket_validator_disables_unavailable_directory(tmp_path: Path) -> None:
    with patch("ktoolbox.configuration.os.link", side_effect=OSError("unsupported")):
        configured = DownloaderConfiguration(use_bucket=True, bucket_path=tmp_path / "bucket")
    assert configured.use_bucket is False
    assert list(configured.bucket_path.iterdir()) == []
