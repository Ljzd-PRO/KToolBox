from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from ktoolbox.configuration import Configuration, DownloaderConfiguration


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
