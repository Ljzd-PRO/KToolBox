from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from ktoolbox.naming_migration import (
    LEGACY_ENV_KEYS,
    MIGRATION_NOTICE_PATH,
    apply_legacy_naming,
    detect_legacy_naming,
    migrate_legacy_naming,
    preview_legacy_naming,
)
from ktoolbox.project_config import ProjectConfigStore, ProjectConfiguration


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
    assert project.naming.filename_format == "{}"
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


def test_detection_reports_sources_without_modifying_them(tmp_path: Path) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "# keep\nKTOOLBOX_JOB__POST_DIRNAME_FORMAT={id}\n",
        encoding="utf-8",
    )
    original = dotenv.read_text(encoding="utf-8")

    detection = detect_legacy_naming(tmp_path)

    assert detection.pending is True
    assert detection.dotenv_keys == {
        dotenv: ("KTOOLBOX_JOB__POST_DIRNAME_FORMAT",),
    }
    assert dotenv.read_text(encoding="utf-8") == original
    assert not (tmp_path / "ktoolbox.toml").exists()


def test_environment_only_legacy_values_warn_but_do_not_require_migration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KTOOLBOX_JOB__FILENAME_FORMAT", "{post_id}_{}")

    detection = detect_legacy_naming(tmp_path)

    assert detection.pending is False
    assert detection.ignored_environment_keys == ("KTOOLBOX_JOB__FILENAME_FORMAT",)


def test_field_preview_and_apply_keep_unselected_project_values(tmp_path: Path) -> None:
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    project = ProjectConfiguration()
    project.naming.post_dirname_format = "{id}"
    project.naming.filename_format = "{post_id}_{}"
    store.save(project)
    (tmp_path / ".env").write_text(
        "KTOOLBOX_JOB__POST_DIRNAME_FORMAT={title} [{id}]\n"
        "KTOOLBOX_JOB__FILENAME_FORMAT={id}_{}\n",
        encoding="utf-8",
    )

    preview = preview_legacy_naming(tmp_path)

    assert preview.pending is True
    assert {field.path for field in preview.fields} == {
        "post_dirname_format",
        "filename_format",
    }
    post_field = next(field for field in preview.fields if field.path == "post_dirname_format")
    assert post_field.legacy_value == "{title} [{id}]"
    assert post_field.current_value == "{id}"

    result = apply_legacy_naming(
        tmp_path,
        selected_fields={"post_dirname_format"},
        project_revision=preview.project_revision,
        source_revisions={source.path.name: source.revision for source in preview.sources},
    )

    migrated = store.load()
    assert migrated.naming.post_dirname_format == "{title} [{id}]"
    assert migrated.naming.filename_format == "{post_id}_{}"
    assert result.project_revision != preview.project_revision
    assert not preview_legacy_naming(tmp_path).pending
    assert "KTOOLBOX_JOB__" not in (tmp_path / ".env").read_text(encoding="utf-8")
    assert {path.name for path in result.backup_paths} == {
        "ktoolbox.toml.bak",
        ".env.bak",
    }


def test_apply_rejects_stale_dotenv_without_modifying_files(tmp_path: Path) -> None:
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.save(ProjectConfiguration())
    dotenv = tmp_path / ".env"
    dotenv.write_text("KTOOLBOX_JOB__MIX_POSTS=true\n", encoding="utf-8")
    preview = preview_legacy_naming(tmp_path)
    dotenv.write_text("KTOOLBOX_JOB__MIX_POSTS=false\n", encoding="utf-8")

    with pytest.raises(ValueError, match="dotenv files changed"):
        apply_legacy_naming(
            tmp_path,
            selected_fields={"mix_posts"},
            project_revision=preview.project_revision,
            source_revisions={source.path.name: source.revision for source in preview.sources},
        )

    assert store.load().naming.mix_posts is False
    assert dotenv.read_text(encoding="utf-8") == "KTOOLBOX_JOB__MIX_POSTS=false\n"


def test_migration_does_not_repeat_for_newer_project_schema(tmp_path: Path) -> None:
    project_path = tmp_path / "ktoolbox.toml"
    ProjectConfigStore(project_path).save(ProjectConfiguration())
    original = project_path.read_text(encoding="utf-8")

    result = migrate_legacy_naming(tmp_path)

    assert result.migrated is False
    assert project_path.read_text(encoding="utf-8") == original
