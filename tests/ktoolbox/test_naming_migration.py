from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from ktoolbox.naming_migration import (
    LEGACY_ENV_KEYS,
    MIGRATION_NOTICE_PATH,
    migrate_legacy_naming,
)
from ktoolbox.project_config import ProjectConfigStore


@pytest.fixture(autouse=True)
def clear_legacy_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in LEGACY_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_migration_moves_effective_values_backs_up_and_removes_old_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "ktoolbox.toml").write_text(
        "# project\nschema_version = 1\n",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text(
        "# keep\nKTOOLBOX_JOB__POST_DIRNAME_FORMAT={id}\n"
        "KTOOLBOX_JOB__SEQUENTIAL_FILENAME=true\n"
        "KTOOLBOX_JOB__COUNT=8\n",
        encoding="utf-8",
    )
    (tmp_path / "prod.env").write_text(
        "KTOOLBOX_JOB__POST_DIRNAME_FORMAT=[{published}] {title}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("KTOOLBOX_JOB__FILENAME_FORMAT", "{post_id}_{}")

    result = migrate_legacy_naming(tmp_path)

    assert result.migrated is True
    assert result.ignored_environment_keys == ("KTOOLBOX_JOB__FILENAME_FORMAT",)
    project = ProjectConfigStore(tmp_path / "ktoolbox.toml").load()
    assert project.naming.post_dirname_format == "[{published}] {title}"
    assert project.naming.filename_format == "{post_id}_{}"
    assert project.naming.sequential_filename is True
    assert "KTOOLBOX_JOB__COUNT=8" in (tmp_path / ".env").read_text(encoding="utf-8")
    assert "POST_DIRNAME_FORMAT" not in (tmp_path / ".env").read_text(encoding="utf-8")
    assert "POST_DIRNAME_FORMAT" not in (tmp_path / "prod.env").read_text(encoding="utf-8")
    assert [path.name for path in result.backup_paths] == [".env.bak", "prod.env.bak"]
    assert (tmp_path / MIGRATION_NOTICE_PATH).is_file()
    assert migrate_legacy_naming(tmp_path).migrated is False


def test_migration_restores_sources_when_project_save_fails(tmp_path: Path) -> None:
    project_path = tmp_path / "ktoolbox.toml"
    dotenv_path = tmp_path / ".env"
    project_path.write_text("schema_version = 1\n", encoding="utf-8")
    dotenv_path.write_text("KTOOLBOX_JOB__MIX_POSTS=true\n", encoding="utf-8")

    with (
        patch.object(ProjectConfigStore, "save", side_effect=OSError("disk full")),
        pytest.raises(OSError, match="disk full"),
    ):
        migrate_legacy_naming(tmp_path)

    assert project_path.read_text(encoding="utf-8") == "schema_version = 1\n"
    assert dotenv_path.read_text(encoding="utf-8") == "KTOOLBOX_JOB__MIX_POSTS=true\n"


def test_missing_project_without_legacy_values_is_not_reported_as_migration(
    tmp_path: Path,
) -> None:
    assert migrate_legacy_naming(tmp_path).migrated is False
    assert not (tmp_path / "ktoolbox.toml").exists()
    assert not (tmp_path / MIGRATION_NOTICE_PATH).exists()
