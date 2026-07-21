from pathlib import Path

import pytest

from ktoolbox.project_config import ProjectConfigStore, ProjectConfiguration
from ktoolbox.webui.server import _project_root


def test_project_root_creates_missing_configuration(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project_root = tmp_path / "new-project"

    assert _project_root(project_root) == project_root.resolve()

    project_config = project_root / "ktoolbox.toml"
    assert project_config.read_text(encoding="utf-8") == "schema_version = 1\n"
    assert ProjectConfigStore(project_config).load() == ProjectConfiguration()
    assert capsys.readouterr().err == f"Warning: {project_config} was not found; created a new project configuration.\n"


def test_project_root_preserves_existing_configuration(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project_config = tmp_path / "ktoolbox.toml"
    original = "# Keep this comment.\nschema_version = 1\n"
    project_config.write_text(original, encoding="utf-8")

    assert _project_root(tmp_path) == tmp_path.resolve()
    assert project_config.read_text(encoding="utf-8") == original
    assert capsys.readouterr().err == ""


def test_project_root_rejects_non_file_configuration(tmp_path: Path) -> None:
    (tmp_path / "ktoolbox.toml").mkdir()

    with pytest.raises(ValueError, match="is not a regular file"):
        _project_root(tmp_path)
