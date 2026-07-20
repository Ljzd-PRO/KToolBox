from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated, Literal
from urllib.parse import urlparse

import tomlkit
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


class ProjectConfiguration(BaseModel):
    """Versioned project-local configuration."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    creators: list[CreatorReference] = Field(default_factory=list)
    blockers: list[BlockerSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_creators(self) -> ProjectConfiguration:
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
        document.add("schema_version", 1)
        document.add("creators", tomlkit.aot())
        document.add("blockers", tomlkit.aot())
        return tomlkit.dumps(document)

    def replace_text(self, content: str) -> ProjectConfiguration:
        try:
            document = tomlkit.parse(content)
            configuration = ProjectConfiguration.model_validate(document.unwrap())
        except (ValueError, TypeError) as error:
            raise ProjectConfigError(f"invalid project configuration {self.path}: {error}") from error
        self._document = document
        self.save(configuration)
        return configuration

    def save(self, configuration: ProjectConfiguration) -> None:
        configuration = ProjectConfiguration.model_validate(configuration)
        document = self._document.copy()
        document["schema_version"] = configuration.schema_version
        document["creators"] = _creator_tables(configuration.creators)
        document["blockers"] = _blocker_tables(configuration.blockers)
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
