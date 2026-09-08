from __future__ import annotations

import stat
from pathlib import Path

import pytest

import ktoolbox.project_initialization as initialization
from ktoolbox.project_config import ProjectConfigStore, ProjectConfiguration


@pytest.mark.parametrize(
    ("detected", "expected"),
    [
        ("Asia/Tokyo", "Asia/Tokyo"),
        ("America/New_York", "America/New_York"),
        ("Europe/Paris", "Europe/Paris"),
        ("CST", "UTC"),
        ("Not/AZone", "UTC"),
    ],
)
def test_detect_host_timezone_returns_valid_iana_or_utc(
    detected: str,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(initialization, "get_localzone_name", lambda: detected)
    assert initialization.detect_host_timezone() == expected


def test_initialize_new_project_preserves_dotenv_and_existing_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "# Keep this comment.\nKTOOLBOX_PUBLISHED_TIME__TARGET_TIMEZONE=Europe/Paris\nOTHER=value\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(initialization, "get_localzone_name", lambda: "Asia/Tokyo")

    detected = initialization.initialize_new_project(tmp_path)

    assert detected == "Europe/Paris"
    assert dotenv.read_text(encoding="utf-8") == (
        "# Keep this comment.\nKTOOLBOX_PUBLISHED_TIME__TARGET_TIMEZONE=Europe/Paris\nOTHER=value\n"
    )
    assert ProjectConfigStore(tmp_path / "ktoolbox.toml").load().schema_version == 5


def test_initialize_new_project_appends_target_and_secures_new_dotenv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(initialization, "get_localzone_name", lambda: "Asia/Seoul")

    initialization.initialize_new_project(tmp_path)

    dotenv = tmp_path / ".env"
    assert dotenv.read_text(encoding="utf-8") == "KTOOLBOX_PUBLISHED_TIME__TARGET_TIMEZONE=Asia/Seoul\n"
    assert stat.S_IMODE(dotenv.stat().st_mode) == 0o600


def test_existing_project_is_never_backfilled_by_initializer(tmp_path: Path) -> None:
    ProjectConfigStore(tmp_path / "ktoolbox.toml").save(ProjectConfiguration())
    with pytest.raises(FileExistsError):
        initialization.initialize_new_project(tmp_path)
    assert not (tmp_path / ".env").exists()
