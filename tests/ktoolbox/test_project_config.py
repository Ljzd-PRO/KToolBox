from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from ktoolbox.project_config import (
    AutomaticSyncOptions,
    AutomaticSyncPlan,
    CreatorReference,
    CronAutomaticSyncSchedule,
    IntervalAutomaticSyncSchedule,
    ProjectConfigError,
    ProjectConfigStore,
    ProjectConfiguration,
    ProjectNamingConfiguration,
    parse_creator_reference,
    project_config_path,
)

UTC = timezone.utc


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
    assert "schema_version = 5" in content
    assert 'default_output = "downloads"' in content
    assert "[naming]" in content
    assert not list(tmp_path.glob(".*.tmp"))
    configuration = store.load()
    assert configuration.find_creator("artist") == configuration.creators[0]
    assert configuration.find_creator("https://pawchive.pw/fanbox/user/123") == configuration.creators[0]


def test_store_replaces_validated_editor_text(tmp_path: Path) -> None:
    path = tmp_path / "ktoolbox.toml"
    store = ProjectConfigStore(path)
    configuration = store.replace_text('schema_version = 1\n[[creators]]\nservice = "fanbox"\ncreator_id = "123"\n')
    assert configuration.creators[0].key == "fanbox:123"
    with pytest.raises(ProjectConfigError, match="invalid project configuration"):
        store.replace_text('schema_version = 1\n[[creators]]\nservice = "fanbox"\n')


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


def test_schema_v1_loads_with_project_naming_defaults(tmp_path: Path) -> None:
    path = tmp_path / "ktoolbox.toml"
    path.write_text("schema_version = 1\n", encoding="utf-8")

    configuration = ProjectConfigStore(path).load()

    assert configuration.schema_version == 5
    assert configuration.default_output == Path("downloads")
    assert configuration.naming.creator_dirname_format == "{creator_name} [{service}-{creator_id}]"
    assert configuration.naming.post_dirname_format == "{title} [{post_id}]"
    assert configuration.naming.sequential_filename is True
    assert configuration.naming.post_structure.attachments == Path("attachments")
    assert configuration.automatic_sync == []


@pytest.mark.parametrize(
    "value",
    [
        Path("downloads"),
        Path("../shared-downloads"),
        Path("/tmp/ktoolbox-downloads"),
    ],
)
def test_project_default_output_accepts_relative_and_absolute_paths(value: Path) -> None:
    configuration = ProjectConfiguration(default_output=value)

    assert configuration.default_output == value


def test_project_default_output_rejects_empty_path() -> None:
    with pytest.raises(ValueError, match="default output directory cannot be empty"):
        ProjectConfiguration(default_output=Path(" "))


def test_naming_configuration_validates_templates_and_paths() -> None:
    configuration = ProjectNamingConfiguration(
        post_dirname_format="[{published}] {title}",
        filename_format="{post_id}_{}",
        month_dirname_format="{year}-{month:02d}",
    )
    assert configuration.filename_format == "{post_id}_{}"

    with pytest.raises(ValueError, match="unsupported naming variable"):
        ProjectNamingConfiguration(post_dirname_format="{unknown}")
    with pytest.raises(ValueError, match="one path component"):
        ProjectNamingConfiguration(creator_dirname_format="{creator_name}/works")
    with pytest.raises(ValueError, match="month grouping requires"):
        ProjectNamingConfiguration(group_by_month=True)


def test_schema_v2_loads_with_automatic_sync_defaults(tmp_path: Path) -> None:
    path = tmp_path / "ktoolbox.toml"
    path.write_text("schema_version = 2\n", encoding="utf-8")

    configuration = ProjectConfigStore(path).load()

    assert configuration.schema_version == 5
    assert configuration.default_output == Path("downloads")
    assert configuration.automatic_sync == []


def test_automatic_sync_plan_round_trip_and_lifecycle(tmp_path: Path) -> None:
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.add_creator(CreatorReference(service="fanbox", creator_id="123", alias="artist"))
    plan = AutomaticSyncPlan(
        id="daily-art",
        name="Daily art",
        creators=["fanbox:123", "FANBOX:123"],
        initial_start_date=date(2026, 7, 1),
        schedule=CronAutomaticSyncSchedule(expression="30 4 * * 1,3,5", timezone="Asia/Shanghai"),
        options=AutomaticSyncOptions(
            output=Path("downloads"),
            save_creator_indices=True,
            download_file=False,
            keywords={"illustration", "comic"},
        ),
    )

    configuration = store.add_automatic_sync_plan(plan)
    assert configuration.automatic_sync[0].creators == ["fanbox:123"]

    content = store.path.read_text(encoding="utf-8")
    assert 'expression = "30 4 * * 1,3,5"' in content
    assert 'timezone = "Asia/Shanghai"' in content
    assert "initial_start_date = 2026-07-01" in content
    assert 'output = "downloads"' in content
    assert "download_file = false" in content
    assert store.load().automatic_sync == configuration.automatic_sync

    updated = plan.model_copy(
        update={
            "name": "Every other day",
            "schedule": IntervalAutomaticSyncSchedule(
                every=2,
                unit="days",
                anchor_at=datetime(2026, 7, 1, tzinfo=UTC),
                timezone="Asia/Shanghai",
            ),
        }
    )
    assert store.update_automatic_sync_plan("daily-art", updated).name == "Every other day"
    assert store.set_automatic_sync_plan_enabled("daily-art", False).enabled is False
    assert store.remove_automatic_sync_plan("daily-art").id == "daily-art"
    assert store.load().automatic_sync == []


@pytest.mark.parametrize(
    "expression",
    ["@daily", "0 0 * *", "60 0 * * *"],
)
def test_automatic_sync_rejects_invalid_cron(expression: str) -> None:
    with pytest.raises(ValueError, match="Cron"):
        CronAutomaticSyncSchedule(expression=expression)


def test_automatic_sync_rejects_invalid_intervals_timezones_and_references(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least 15 minutes"):
        IntervalAutomaticSyncSchedule(every=14, unit="minutes")
    with pytest.raises(ValueError, match="include a timezone"):
        IntervalAutomaticSyncSchedule(anchor_at=datetime(2026, 7, 1))
    with pytest.raises(ValueError, match="unknown IANA timezone"):
        CronAutomaticSyncSchedule(timezone="Moon/Sea_of_Tranquility")

    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    with pytest.raises(ProjectConfigError, match="missing creators"):
        store.add_automatic_sync_plan(
            AutomaticSyncPlan(
                id="missing",
                name="Missing creator",
                creators=["fanbox:404"],
            )
        )


def test_automatic_sync_plan_references_prevent_creator_deletion(tmp_path: Path) -> None:
    store = ProjectConfigStore(tmp_path / "ktoolbox.toml")
    store.add_creator(CreatorReference(service="fanbox", creator_id="123"))
    store.add_automatic_sync_plan(
        AutomaticSyncPlan(
            id="daily",
            name="Daily sync",
            creators=["fanbox:123"],
        )
    )

    with pytest.raises(ProjectConfigError, match="used by automatic sync plans: Daily sync"):
        store.remove_creator("fanbox:123")
    with pytest.raises(ProjectConfigError, match="ID cannot be changed"):
        store.update_automatic_sync_plan(
            "daily",
            AutomaticSyncPlan(id="renamed", name="Renamed", creators=["fanbox:123"]),
        )
    with pytest.raises(ProjectConfigError, match="not found"):
        store.remove_automatic_sync_plan("missing")
