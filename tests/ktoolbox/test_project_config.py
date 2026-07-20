from __future__ import annotations

from pathlib import Path

import pytest

from ktoolbox.project_config import (
    CreatorReference,
    ProjectConfigError,
    ProjectConfigStore,
    ProjectConfiguration,
    parse_creator_reference,
    project_config_path,
)


def test_project_config_path_priority(tmp_path: Path) -> None:
    explicit = tmp_path / "explicit.toml"
    environment = tmp_path / "environment.toml"
    assert project_config_path(explicit, environ={"KTOOLBOX_PROJECT_CONFIG": str(environment)}) == explicit
    assert project_config_path(environ={"KTOOLBOX_PROJECT_CONFIG": str(environment)}) == environment
    assert project_config_path(environ={}) == Path("ktoolbox.toml")


@pytest.mark.parametrize(
    ("target", "key"),
    [
        ("fanbox:123", "fanbox:123"),
        ("https://pawchive.pw/fanbox/user/123", "fanbox:123"),
        ("https://pawchive.pw/fanbox/user/123/post/456", "fanbox:123"),
    ],
)
def test_parse_creator_reference(target: str, key: str) -> None:
    assert parse_creator_reference(target).key == key


def test_parse_creator_reference_rejects_invalid_target() -> None:
    with pytest.raises(ProjectConfigError, match="Pawchive creator URL"):
        parse_creator_reference("https://pawchive.pw/posts")
    with pytest.raises(ProjectConfigError, match="service:creator_id"):
        parse_creator_reference("fanbox")


def test_store_round_trip_is_atomic_and_preserves_top_comment(tmp_path: Path) -> None:
    path = tmp_path / "ktoolbox.toml"
    path.write_text("# Keep this comment\nschema_version = 1\n", encoding="utf-8")
    store = ProjectConfigStore(path)
    store.add_creator(CreatorReference(service="fanbox", creator_id="123", alias="artist"))

    content = path.read_text(encoding="utf-8")
    assert content.startswith("# Keep this comment")
    assert not list(tmp_path.glob(".*.tmp"))
    configuration = store.load()
    assert configuration.find_creator("artist") == configuration.creators[0]
    assert configuration.find_creator("https://pawchive.pw/fanbox/user/123") == configuration.creators[0]


def test_store_manages_creator_lifecycle(tmp_path: Path) -> None:
    store = ProjectConfigStore(tmp_path / "nested" / "ktoolbox.toml")
    assert store.load() == ProjectConfiguration()
    store.add_creator(CreatorReference(service="fanbox", creator_id="123"))
    assert store.set_creator_enabled("fanbox:123", False).enabled is False
    assert store.load().creators[0].enabled is False
    assert store.remove_creator("fanbox:123").key == "fanbox:123"
    assert store.load().creators == []


def test_store_rejects_duplicate_creators_and_aliases(tmp_path: Path) -> None:
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.add_creator(CreatorReference(service="fanbox", creator_id="123", alias="artist"))
    with pytest.raises(ProjectConfigError, match="duplicate creator"):
        store.add_creator(CreatorReference(service="fanbox", creator_id="123"))
    with pytest.raises(ProjectConfigError, match="duplicate creator alias"):
        store.add_creator(CreatorReference(service="patreon", creator_id="456", alias="ARTIST"))


def test_store_reports_invalid_toml_and_unknown_fields(tmp_path: Path) -> None:
    path = tmp_path / "ktoolbox.toml"
    path.write_text("not = [valid", encoding="utf-8")
    with pytest.raises(ProjectConfigError, match="invalid project configuration"):
        ProjectConfigStore(path).load()

    path.write_text('schema_version = 1\nunknown = "value"\n', encoding="utf-8")
    with pytest.raises(ProjectConfigError, match="unknown"):
        ProjectConfigStore(path).load()


def test_store_reports_missing_creator(tmp_path: Path) -> None:
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    with pytest.raises(ProjectConfigError, match="creator not found"):
        store.remove_creator("fanbox:missing")
