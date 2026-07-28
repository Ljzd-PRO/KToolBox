from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import date, datetime
from pathlib import Path
from string import Formatter
from tempfile import NamedTemporaryFile
from typing import Annotated, Any, Literal
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import tomlkit
from croniter import CroniterBadCronError, croniter
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from tomlkit.items import AoT
from tomlkit.toml_document import TOMLDocument

from ktoolbox.blocker.model import BlockerSpec

PROJECT_CONFIG_ENV = "KTOOLBOX_PROJECT_CONFIG"
DEFAULT_PROJECT_CONFIG_PATH = Path("ktoolbox.toml")


class ProjectConfigError(ValueError):
    """Raised when the project configuration cannot be loaded or updated."""


class CreatorReference(BaseModel):
    """A stable Pawchive creator identity stored in the project roster."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    service: Annotated[str, Field(min_length=1)]
    creator_id: Annotated[str, Field(min_length=1)]
    alias: str | None = None
    enabled: bool = True

    @field_validator("alias")
    @classmethod
    def validate_alias(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        if ":" in value:
            raise ValueError("creator aliases cannot contain ':'")
        return value

    @property
    def key(self) -> str:
        return f"{self.service}:{self.creator_id}"


_POST_TEMPLATE_FIELDS = frozenset(
    {
        "id",
        "post_id",
        "user",
        "creator_id",
        "service",
        "platform",
        "title",
        "added",
        "published",
        "edited",
    }
)
_CREATOR_TEMPLATE_FIELDS = frozenset(
    {
        "creator_name",
        "creator_id",
        "service",
        "platform",
        "alias",
    }
)
_DATE_TEMPLATE_FIELDS = frozenset({"year", "month"})
_REVISION_TEMPLATE_FIELDS = _POST_TEMPLATE_FIELDS | frozenset({"revision_id"})


def _validate_component_template(
    value: str,
    *,
    fields: frozenset[str],
    allow_automatic_field: bool = False,
) -> str:
    value = value.strip()
    if not value:
        raise ValueError("naming templates cannot be empty")
    if "/" in value or "\\" in value or "\0" in value:
        raise ValueError("naming templates must describe one path component")
    try:
        parsed = Formatter().parse(value)
        for _, field_name, _, _ in parsed:
            if field_name is None:
                continue
            if field_name == "":
                if allow_automatic_field:
                    continue
                raise ValueError("automatic fields are not supported by this template")
            if field_name not in fields:
                raise ValueError(f"unsupported naming variable: {field_name}")
    except ValueError:
        raise
    except Exception as error:
        raise ValueError(f"invalid naming template: {error}") from error
    return value


def _validate_relative_path(value: Path) -> Path:
    if value.is_absolute() or ".." in value.parts:
        raise ValueError("naming paths must stay within their work directory")
    if not value.parts or str(value) in {"", "."}:
        raise ValueError("naming paths cannot be empty")
    return value


class ProjectPostStructureConfiguration(BaseModel):
    """Project-local names used inside each downloaded work directory."""

    model_config = ConfigDict(extra="forbid")

    attachments: Path = Path("attachments")
    content: Path = Path("content.txt")
    external_links: Path = Path("external_links.txt")
    file: str = "{id}_{}"
    revisions: Path = Path("revisions")

    @field_validator("attachments", "content", "external_links", "revisions")
    @classmethod
    def validate_relative_paths(cls, value: Path) -> Path:
        return _validate_relative_path(value)

    @field_validator("file")
    @classmethod
    def validate_primary_file_template(cls, value: str) -> str:
        return _validate_component_template(
            value,
            fields=_POST_TEMPLATE_FIELDS,
            allow_automatic_field=True,
        )


class ProjectNamingConfiguration(BaseModel):
    """Project-local directory layout and filename templates."""

    model_config = ConfigDict(extra="forbid")

    creator_dirname_format: str = "{creator_name} [{service}-{creator_id}]"
    post_dirname_format: str = "{title}"
    revision_dirname_format: str = "{revision_id}"
    post_structure: ProjectPostStructureConfiguration = Field(default_factory=ProjectPostStructureConfiguration)
    mix_posts: bool = False
    sequential_filename: bool = False
    sequential_filename_excludes: set[str] = Field(default_factory=set)
    filename_format: str = "{}"
    group_by_year: bool = False
    group_by_month: bool = False
    year_dirname_format: str = "{year}"
    month_dirname_format: str = "{year}-{month:02d}"

    @field_validator("creator_dirname_format")
    @classmethod
    def validate_creator_template(cls, value: str) -> str:
        return _validate_component_template(value, fields=_CREATOR_TEMPLATE_FIELDS)

    @field_validator("post_dirname_format")
    @classmethod
    def validate_post_template(cls, value: str) -> str:
        return _validate_component_template(value, fields=_POST_TEMPLATE_FIELDS)

    @field_validator("revision_dirname_format")
    @classmethod
    def validate_revision_template(cls, value: str) -> str:
        return _validate_component_template(value, fields=_REVISION_TEMPLATE_FIELDS)

    @field_validator("filename_format")
    @classmethod
    def validate_filename_template(cls, value: str) -> str:
        return _validate_component_template(
            value,
            fields=_POST_TEMPLATE_FIELDS,
            allow_automatic_field=True,
        )

    @field_validator("year_dirname_format", "month_dirname_format")
    @classmethod
    def validate_date_templates(cls, value: str) -> str:
        return _validate_component_template(value, fields=_DATE_TEMPLATE_FIELDS)

    @model_validator(mode="after")
    def validate_grouping(self) -> ProjectNamingConfiguration:
        if self.group_by_month and not self.group_by_year:
            raise ValueError("month grouping requires year grouping")
        return self


class AutomaticSyncOptions(BaseModel):
    """Reusable synchronization settings attached to an automatic plan."""

    model_config = ConfigDict(extra="forbid")

    output: Path = Path(".")
    save_creator_indices: bool = False
    mix_posts: bool | None = None
    keywords: set[str] = Field(default_factory=set)
    keywords_exclude: set[str] = Field(default_factory=set)


class CronAutomaticSyncSchedule(BaseModel):
    """A standard five-field Cron schedule evaluated in an IANA timezone."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    kind: Literal["cron"] = "cron"
    expression: str = "0 3 * * *"
    timezone: str = "UTC"

    @field_validator("expression")
    @classmethod
    def validate_expression(cls, value: str) -> str:
        fields = value.split()
        if len(fields) != 5 or value.startswith("@"):
            raise ValueError("automatic sync Cron expressions must contain exactly five fields")
        try:
            croniter(value, datetime(2026, 1, 1))
        except (CroniterBadCronError, ValueError, KeyError) as error:
            raise ValueError(f"invalid automatic sync Cron expression: {error}") from error
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError(f"unknown IANA timezone: {value}") from error
        return value


class IntervalAutomaticSyncSchedule(BaseModel):
    """A fixed interval anchored to a stable UTC instant."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["interval"] = "interval"
    every: int = Field(default=24, ge=1)
    unit: Literal["minutes", "hours", "days"] = "hours"
    anchor_at: datetime | None = None
    timezone: str = "UTC"

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        return CronAutomaticSyncSchedule.validate_timezone(value)

    @model_validator(mode="after")
    def validate_minimum_interval(self) -> IntervalAutomaticSyncSchedule:
        seconds = self.every * {"minutes": 60, "hours": 3600, "days": 86400}[self.unit]
        if seconds < 15 * 60:
            raise ValueError("automatic sync intervals must be at least 15 minutes")
        if self.anchor_at is not None and self.anchor_at.tzinfo is None:
            raise ValueError("automatic sync interval anchors must include a timezone")
        return self


AutomaticSyncSchedule = Annotated[
    CronAutomaticSyncSchedule | IntervalAutomaticSyncSchedule,
    Field(discriminator="kind"),
]


class AutomaticSyncPlan(BaseModel):
    """Project-local definition for one recurring creator synchronization."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")]
    name: Annotated[str, Field(min_length=1, max_length=120)]
    enabled: bool = True
    creators: list[str] = Field(min_length=1)
    schedule: AutomaticSyncSchedule = Field(default_factory=CronAutomaticSyncSchedule)
    initial_start_date: date | None = None
    options: AutomaticSyncOptions = Field(default_factory=AutomaticSyncOptions)

    @field_validator("creators")
    @classmethod
    def validate_creators(cls, value: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for target in value:
            creator = parse_creator_reference(target)
            normalized = creator.key.casefold()
            if normalized not in seen:
                unique.append(creator.key)
                seen.add(normalized)
        if not unique:
            raise ValueError("automatic sync plans require at least one creator")
        return unique


class ProjectConfiguration(BaseModel):
    """Versioned project-local configuration."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[4] = 4
    creators: list[CreatorReference] = Field(default_factory=list)
    blockers: list[BlockerSpec] = Field(default_factory=list)
    naming: ProjectNamingConfiguration = Field(default_factory=ProjectNamingConfiguration)
    automatic_sync: list[AutomaticSyncPlan] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def upgrade_schema(cls, value: Any) -> Any:
        if isinstance(value, Mapping) and value.get("schema_version", 1) in {1, 2, 3}:
            upgraded = dict(value)
            upgraded["schema_version"] = 4
            naming = dict(upgraded.get("naming") or {})
            naming.pop("download_roots", None)
            upgraded["naming"] = naming
            upgraded.setdefault("automatic_sync", [])
            return upgraded
        return value

    @model_validator(mode="after")
    def validate_project_references(self) -> ProjectConfiguration:
        keys: set[str] = set()
        aliases: set[str] = set()
        for creator in self.creators:
            normalized_key = creator.key.casefold()
            if normalized_key in keys:
                raise ValueError(f"duplicate creator: {creator.key}")
            keys.add(normalized_key)
            if creator.alias:
                normalized_alias = creator.alias.casefold()
                if normalized_alias in aliases:
                    raise ValueError(f"duplicate creator alias: {creator.alias}")
                aliases.add(normalized_alias)
        blocker_ids: set[str] = set()
        from ktoolbox.blocker.engine import blocker_registry

        for blocker in self.blockers:
            normalized_id = blocker.id.casefold()
            if normalized_id in blocker_ids:
                raise ValueError(f"duplicate blocker ID: {blocker.id}")
            blocker_ids.add(normalized_id)
            blocker_registry.validate(blocker)
        plan_ids: set[str] = set()
        plan_names: set[str] = set()
        for plan in self.automatic_sync:
            normalized_id = plan.id.casefold()
            normalized_name = plan.name.casefold()
            if normalized_id in plan_ids:
                raise ValueError(f"duplicate automatic sync plan ID: {plan.id}")
            if normalized_name in plan_names:
                raise ValueError(f"duplicate automatic sync plan name: {plan.name}")
            plan_ids.add(normalized_id)
            plan_names.add(normalized_name)
            missing = [target for target in plan.creators if target.casefold() not in keys]
            if missing:
                raise ValueError(f"automatic sync plan {plan.name!r} references missing creators: {', '.join(missing)}")
        return self

    def find_creator(self, target: str) -> CreatorReference | None:
        normalized = target.casefold()
        for creator in self.creators:
            if creator.key.casefold() == normalized or (creator.alias and creator.alias.casefold() == normalized):
                return creator
        try:
            parsed = parse_creator_reference(target)
        except ProjectConfigError:
            return None
        return next((creator for creator in self.creators if creator.key.casefold() == parsed.key.casefold()), None)


def parse_creator_reference(target: str) -> CreatorReference:
    """Parse a Pawchive creator URL or ``service:creator_id`` reference."""
    target = target.strip()
    parsed_url = urlparse(target)
    if parsed_url.scheme and parsed_url.netloc:
        parts = [part for part in parsed_url.path.split("/") if part]
        if len(parts) >= 3 and parts[1] == "user":
            return CreatorReference(service=parts[0], creator_id=parts[2])
        raise ProjectConfigError(f"not a Pawchive creator URL: {target}")

    service, separator, creator_id = target.partition(":")
    if separator and service and creator_id:
        return CreatorReference(service=service, creator_id=creator_id)
    raise ProjectConfigError("creator must be a Pawchive URL or service:creator_id")


def project_config_path(
    explicit: Path | str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> Path:
    """Resolve the project configuration path in documented priority order."""
    if explicit is not None:
        return Path(explicit).expanduser()
    values = os.environ if environ is None else environ
    if configured := values.get(PROJECT_CONFIG_ENV):
        return Path(configured).expanduser()
    return DEFAULT_PROJECT_CONFIG_PATH


class ProjectConfigStore:
    """Load and atomically update a project configuration document."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = project_config_path(path)
        self._document: TOMLDocument = tomlkit.document()

    def load(self) -> ProjectConfiguration:
        if not self.path.exists():
            self._document = tomlkit.document()
            return ProjectConfiguration()
        try:
            self._document = tomlkit.parse(self.path.read_text(encoding="utf-8"))
            return ProjectConfiguration.model_validate(self._document.unwrap())
        except (OSError, ValueError, TypeError) as error:
            raise ProjectConfigError(f"invalid project configuration {self.path}: {error}") from error

    def load_text(self) -> str:
        if self.path.exists():
            try:
                return self.path.read_text(encoding="utf-8")
            except OSError as error:
                raise ProjectConfigError(f"unable to read project configuration {self.path}: {error}") from error
        document = tomlkit.document()
        document.add("schema_version", 4)
        document.add("creators", tomlkit.aot())
        document.add("blockers", tomlkit.aot())
        document.add("naming", tomlkit.item(ProjectNamingConfiguration().model_dump(mode="json")))
        document.add("automatic_sync", tomlkit.aot())
        return tomlkit.dumps(document)

    def replace_text(self, content: str) -> ProjectConfiguration:
        configuration, document = self.validate_text(content)
        self._document = document
        self.save(configuration)
        return configuration

    def validate_text(self, content: str) -> tuple[ProjectConfiguration, TOMLDocument]:
        """Parse and validate project TOML without changing the stored file."""
        try:
            document = tomlkit.parse(content)
            configuration = ProjectConfiguration.model_validate(document.unwrap())
        except (ValueError, TypeError) as error:
            raise ProjectConfigError(f"invalid project configuration {self.path}: {error}") from error
        return configuration, document

    def save(self, configuration: ProjectConfiguration) -> None:
        configuration = ProjectConfiguration.model_validate(configuration)
        document = self._document.copy()
        document["schema_version"] = configuration.schema_version
        document["creators"] = _creator_tables(configuration.creators)
        document["blockers"] = _blocker_tables(configuration.blockers)
        document["naming"] = tomlkit.item(configuration.naming.model_dump(mode="json"))
        document["automatic_sync"] = _automatic_sync_tables(configuration.automatic_sync)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(tomlkit.dumps(document))
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, self.path)
        except OSError as error:
            raise ProjectConfigError(f"unable to save project configuration {self.path}: {error}") from error
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        self._document = document

    def add_creator(self, creator: CreatorReference) -> ProjectConfiguration:
        configuration = self.load()
        configuration.creators.append(creator)
        try:
            configuration = ProjectConfiguration.model_validate(configuration.model_dump())
        except ValueError as error:
            raise ProjectConfigError(str(error)) from error
        self.save(configuration)
        return configuration

    def remove_creator(self, target: str) -> CreatorReference:
        configuration = self.load()
        creator = configuration.find_creator(target)
        if creator is None:
            raise ProjectConfigError(f"creator not found: {target}")
        referencing_plans = [plan.name for plan in configuration.automatic_sync if creator.key in plan.creators]
        if referencing_plans:
            names = ", ".join(referencing_plans)
            raise ProjectConfigError(f"creator {creator.key} is used by automatic sync plans: {names}")
        configuration.creators.remove(creator)
        self.save(configuration)
        return creator

    def set_creator_enabled(self, target: str, enabled: bool) -> CreatorReference:
        configuration = self.load()
        creator = configuration.find_creator(target)
        if creator is None:
            raise ProjectConfigError(f"creator not found: {target}")
        creator.enabled = enabled
        self.save(configuration)
        return creator

    def add_automatic_sync_plan(self, plan: AutomaticSyncPlan) -> ProjectConfiguration:
        configuration = self.load()
        configuration.automatic_sync.append(plan)
        validated = self._validate_configuration(configuration)
        self.save(validated)
        return validated

    def update_automatic_sync_plan(self, plan_id: str, plan: AutomaticSyncPlan) -> AutomaticSyncPlan:
        configuration = self.load()
        index = self._automatic_sync_plan_index(configuration, plan_id)
        if plan.id.casefold() != plan_id.casefold():
            raise ProjectConfigError("automatic sync plan ID cannot be changed")
        configuration.automatic_sync[index] = plan
        validated = self._validate_configuration(configuration)
        self.save(validated)
        return validated.automatic_sync[index]

    def remove_automatic_sync_plan(self, plan_id: str) -> AutomaticSyncPlan:
        configuration = self.load()
        index = self._automatic_sync_plan_index(configuration, plan_id)
        plan = configuration.automatic_sync.pop(index)
        self.save(configuration)
        return plan

    def set_automatic_sync_plan_enabled(self, plan_id: str, enabled: bool) -> AutomaticSyncPlan:
        configuration = self.load()
        index = self._automatic_sync_plan_index(configuration, plan_id)
        configuration.automatic_sync[index].enabled = enabled
        self.save(configuration)
        return configuration.automatic_sync[index]

    @staticmethod
    def _automatic_sync_plan_index(configuration: ProjectConfiguration, plan_id: str) -> int:
        normalized = plan_id.casefold()
        for index, plan in enumerate(configuration.automatic_sync):
            if plan.id.casefold() == normalized:
                return index
        raise ProjectConfigError(f"automatic sync plan not found: {plan_id}")

    @staticmethod
    def _validate_configuration(configuration: ProjectConfiguration) -> ProjectConfiguration:
        try:
            return ProjectConfiguration.model_validate(configuration.model_dump())
        except ValueError as error:
            raise ProjectConfigError(str(error)) from error


def _creator_tables(creators: list[CreatorReference]) -> AoT:
    tables = tomlkit.aot()
    for creator in creators:
        table = tomlkit.table()
        table.add("service", creator.service)
        table.add("creator_id", creator.creator_id)
        if creator.alias is not None:
            table.add("alias", creator.alias)
        table.add("enabled", creator.enabled)
        tables.append(table)
    return tables


def _blocker_tables(blockers: list[BlockerSpec]) -> AoT:
    tables = tomlkit.aot()
    for blocker in blockers:
        table = tomlkit.table()
        table.add("id", blocker.id)
        table.add("type", blocker.type)
        table.add("enabled", blocker.enabled)
        table.add("scope", tomlkit.item(blocker.scope.model_dump(mode="python")))
        table.add("options", tomlkit.item(blocker.options))
        tables.append(table)
    return tables


def _automatic_sync_tables(plans: list[AutomaticSyncPlan]) -> AoT:
    tables = tomlkit.aot()
    for plan in plans:
        table = tomlkit.table()
        table.add("id", plan.id)
        table.add("name", plan.name)
        table.add("enabled", plan.enabled)
        table.add("creators", plan.creators)
        if plan.initial_start_date is not None:
            table.add("initial_start_date", plan.initial_start_date)
        schedule = plan.schedule.model_dump(mode="json", exclude_none=True)
        options = plan.options.model_dump(mode="json", exclude_none=True)
        options["keywords"] = sorted(plan.options.keywords)
        options["keywords_exclude"] = sorted(plan.options.keywords_exclude)
        table.add("schedule", tomlkit.item(schedule))
        table.add("options", tomlkit.item(options))
        tables.append(table)
    return tables
