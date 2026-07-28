from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, ClassVar

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ktoolbox.project_config import (
    ProjectConfigStore,
    ProjectNamingConfiguration,
    ProjectPostStructureConfiguration,
)

MIGRATION_ID = "project-naming-v2"
MIGRATION_NOTICE_PATH = Path(".ktoolbox") / "startup-notices" / f"{MIGRATION_ID}.json"
MIGRATION_BACKUP_DIR = Path(".ktoolbox") / "migrations" / MIGRATION_ID


class _LegacyPostStructure(BaseModel):
    attachments: Path = Path("attachments")
    content: Path = Path("content.txt")
    external_links: Path = Path("external_links.txt")
    file: str = "{id}_{}"
    revisions: Path = Path("revisions")


class _LegacyJobNaming(BaseModel):
    post_dirname_format: str = "{title}"
    post_structure: _LegacyPostStructure = Field(default_factory=_LegacyPostStructure)
    mix_posts: bool = False
    sequential_filename: bool = False
    sequential_filename_excludes: set[str] = Field(default_factory=set)
    filename_format: str = "{}"
    group_by_year: bool = False
    group_by_month: bool = False
    year_dirname_format: str = "{year}"
    month_dirname_format: str = "{year}-{month:02d}"


class _LegacyNamingSettings(BaseSettings):
    job: _LegacyJobNaming = Field(default_factory=_LegacyJobNaming)

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="ktoolbox_",
        env_nested_delimiter="__",
        env_file=[".env", "prod.env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: Any,
        env_settings: Any,
        dotenv_settings: Any,
        file_secret_settings: Any,
    ) -> tuple[Any, ...]:
        del settings_cls, env_settings
        return init_settings, dotenv_settings, file_secret_settings


LEGACY_ENV_KEYS = frozenset(
    {
        "KTOOLBOX_JOB__POST_DIRNAME_FORMAT",
        "KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS",
        "KTOOLBOX_JOB__POST_STRUCTURE__CONTENT",
        "KTOOLBOX_JOB__POST_STRUCTURE__EXTERNAL_LINKS",
        "KTOOLBOX_JOB__POST_STRUCTURE__FILE",
        "KTOOLBOX_JOB__POST_STRUCTURE__REVISIONS",
        "KTOOLBOX_JOB__MIX_POSTS",
        "KTOOLBOX_JOB__SEQUENTIAL_FILENAME",
        "KTOOLBOX_JOB__SEQUENTIAL_FILENAME_EXCLUDES",
        "KTOOLBOX_JOB__FILENAME_FORMAT",
        "KTOOLBOX_JOB__GROUP_BY_YEAR",
        "KTOOLBOX_JOB__GROUP_BY_MONTH",
        "KTOOLBOX_JOB__YEAR_DIRNAME_FORMAT",
        "KTOOLBOX_JOB__MONTH_DIRNAME_FORMAT",
    }
)
_LEGACY_LINE = re.compile(
    rf"^\s*(?:export\s+)?(?:{'|'.join(re.escape(key) for key in sorted(LEGACY_ENV_KEYS))})\s*=",
    re.IGNORECASE,
)
LEGACY_FIELD_PATHS = {
    "KTOOLBOX_JOB__POST_DIRNAME_FORMAT": "post_dirname_format",
    "KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS": "post_structure.attachments",
    "KTOOLBOX_JOB__POST_STRUCTURE__CONTENT": "post_structure.content",
    "KTOOLBOX_JOB__POST_STRUCTURE__EXTERNAL_LINKS": "post_structure.external_links",
    "KTOOLBOX_JOB__POST_STRUCTURE__FILE": "post_structure.file",
    "KTOOLBOX_JOB__POST_STRUCTURE__REVISIONS": "post_structure.revisions",
    "KTOOLBOX_JOB__MIX_POSTS": "mix_posts",
    "KTOOLBOX_JOB__SEQUENTIAL_FILENAME": "sequential_filename",
    "KTOOLBOX_JOB__SEQUENTIAL_FILENAME_EXCLUDES": "sequential_filename_excludes",
    "KTOOLBOX_JOB__FILENAME_FORMAT": "filename_format",
    "KTOOLBOX_JOB__GROUP_BY_YEAR": "group_by_year",
    "KTOOLBOX_JOB__GROUP_BY_MONTH": "group_by_month",
    "KTOOLBOX_JOB__YEAR_DIRNAME_FORMAT": "year_dirname_format",
    "KTOOLBOX_JOB__MONTH_DIRNAME_FORMAT": "month_dirname_format",
}


@dataclass(frozen=True, slots=True)
class NamingMigrationResult:
    migrated: bool
    backup_paths: tuple[Path, ...] = ()
    ignored_environment_keys: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LegacyNamingDetection:
    """Legacy naming settings that still require an explicit user decision."""

    dotenv_keys: dict[Path, tuple[str, ...]]
    ignored_environment_keys: tuple[str, ...] = ()

    @property
    def pending(self) -> bool:
        return any(self.dotenv_keys.values())


@dataclass(frozen=True, slots=True)
class LegacyNamingSource:
    path: Path
    revision: str
    keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LegacyNamingField:
    path: str
    env_key: str
    legacy_value: object
    current_value: object
    sources: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LegacyNamingPreview:
    pending: bool
    project_revision: str
    sources: tuple[LegacyNamingSource, ...]
    fields: tuple[LegacyNamingField, ...]
    ignored_environment_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LegacyNamingApplyResult:
    migrated: bool
    backup_paths: tuple[Path, ...]
    naming: ProjectNamingConfiguration
    project_revision: str
    ignored_environment_keys: tuple[str, ...]


def detect_legacy_naming(project_root: Path) -> LegacyNamingDetection:
    """Inspect legacy naming sources without changing project files."""

    root = project_root.expanduser().resolve()
    dotenv_keys: dict[Path, tuple[str, ...]] = {}
    for path in (root / ".env", root / "prod.env"):
        if path.is_file():
            keys = tuple(find_legacy_naming_keys(path.read_text(encoding="utf-8")))
            if keys:
                dotenv_keys[path] = keys
    ignored_environment = tuple(sorted(key for key in LEGACY_ENV_KEYS if key in os.environ))
    return LegacyNamingDetection(
        dotenv_keys=dotenv_keys,
        ignored_environment_keys=ignored_environment,
    )


def preview_legacy_naming(project_root: Path) -> LegacyNamingPreview:
    """Build a field-level migration preview without changing any files."""

    root = project_root.expanduser().resolve()
    project_store = ProjectConfigStore(root / "ktoolbox.toml")
    project_text = project_store.load_text()
    project = project_store.load()
    detection = detect_legacy_naming(root)
    sources = tuple(
        LegacyNamingSource(
            path=path,
            revision=_content_revision(path.read_text(encoding="utf-8")),
            keys=keys,
        )
        for path, keys in detection.dotenv_keys.items()
    )
    if not detection.pending:
        return LegacyNamingPreview(
            pending=False,
            project_revision=_content_revision(project_text),
            sources=sources,
            fields=(),
            ignored_environment_keys=detection.ignored_environment_keys,
        )

    legacy = _legacy_naming_from_dotenv(root)
    legacy_values = legacy.model_dump(mode="json")
    current_values = project.naming.model_dump(mode="json")
    fields: list[LegacyNamingField] = []
    for env_key, field_path in LEGACY_FIELD_PATHS.items():
        field_sources = tuple(
            source.path.name
            for source in sources
            if env_key in {key.upper() for key in source.keys}
        )
        if field_sources:
            fields.append(
                LegacyNamingField(
                    path=field_path,
                    env_key=env_key,
                    legacy_value=_nested_value(legacy_values, field_path),
                    current_value=_nested_value(current_values, field_path),
                    sources=field_sources,
                )
            )
    return LegacyNamingPreview(
        pending=True,
        project_revision=_content_revision(project_text),
        sources=sources,
        fields=tuple(fields),
        ignored_environment_keys=detection.ignored_environment_keys,
    )


def apply_legacy_naming(
    project_root: Path,
    *,
    selected_fields: set[str],
    project_revision: str,
    source_revisions: dict[str, str],
) -> LegacyNamingApplyResult:
    """Apply a confirmed field selection and remove all legacy dotenv keys."""

    root = project_root.expanduser().resolve()
    preview = preview_legacy_naming(root)
    if not preview.pending:
        raise ValueError("legacy naming settings are no longer present")
    if preview.project_revision != project_revision:
        raise ValueError("project configuration changed; reload the migration preview")
    expected_sources = {source.path.name: source.revision for source in preview.sources}
    if source_revisions != expected_sources:
        raise ValueError("legacy dotenv files changed; reload the migration preview")
    allowed_fields = {field.path for field in preview.fields}
    if unknown := sorted(selected_fields - allowed_fields):
        raise ValueError("unknown legacy naming fields: " + ", ".join(unknown))

    project_path = root / "ktoolbox.toml"
    project_store = ProjectConfigStore(project_path)
    original_project = project_store.load_text()
    originals = {
        source.path: source.path.read_text(encoding="utf-8")
        for source in preview.sources
    }
    project = project_store.load()
    candidate_values = project.naming.model_dump(mode="python")
    legacy_values = _legacy_naming_from_dotenv(root).model_dump(mode="python")
    for field_path in selected_fields:
        _set_nested_value(
            candidate_values,
            field_path,
            _nested_value(legacy_values, field_path),
        )
    candidate = ProjectNamingConfiguration.model_validate(candidate_values)

    backup_dir = root / MIGRATION_BACKUP_DIR
    backup_paths: list[Path] = []
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        project_backup = backup_dir / "ktoolbox.toml.bak"
        _atomic_write(project_backup, original_project, mode=0o600)
        backup_paths.append(project_backup)
        for path, content in originals.items():
            backup = backup_dir / f"{path.name}.bak"
            _atomic_write(backup, content, mode=0o600)
            backup_paths.append(backup)
            _atomic_write(path, _without_legacy_keys(content), mode=0o600)
        project.naming = candidate
        project_store.save(project)
    except Exception:
        for path, content in originals.items():
            _atomic_write(path, content, mode=0o600)
        _atomic_write(project_path, original_project)
        raise

    return LegacyNamingApplyResult(
        migrated=True,
        backup_paths=tuple(backup_paths),
        naming=candidate,
        project_revision=_content_revision(project_store.load_text()),
        ignored_environment_keys=preview.ignored_environment_keys,
    )


def migrate_legacy_naming(project_root: Path) -> NamingMigrationResult:
    """Explicitly move legacy dotenv naming values into ``ktoolbox.toml``."""
    root = project_root.expanduser().resolve()
    project_path = root / "ktoolbox.toml"
    sources = [path for path in (root / ".env", root / "prod.env") if path.exists()]
    originals = {path: path.read_text(encoding="utf-8") for path in sources}
    detection = detect_legacy_naming(root)
    if not detection.pending:
        return NamingMigrationResult(migrated=False)

    original_project = project_path.read_text(encoding="utf-8") if project_path.exists() else ""
    legacy = _LegacyNamingSettings(_env_file=[root / ".env", root / "prod.env"]).job
    naming = ProjectNamingConfiguration(
        post_dirname_format=legacy.post_dirname_format,
        post_structure=ProjectPostStructureConfiguration.model_validate(
            legacy.post_structure.model_dump(mode="python")
        ),
        mix_posts=legacy.mix_posts,
        sequential_filename=legacy.sequential_filename,
        sequential_filename_excludes=legacy.sequential_filename_excludes,
        filename_format=legacy.filename_format,
        group_by_year=legacy.group_by_year,
        group_by_month=legacy.group_by_month,
        year_dirname_format=legacy.year_dirname_format,
        month_dirname_format=legacy.month_dirname_format,
    )

    backup_dir = root / MIGRATION_BACKUP_DIR
    backup_paths: list[Path] = []

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        for path, content in originals.items():
            backup = backup_dir / f"{path.name}.bak"
            _atomic_write(backup, content, mode=0o600)
            backup_paths.append(backup)
            _atomic_write(path, _without_legacy_keys(content), mode=0o600)

        store = ProjectConfigStore(project_path)
        configuration = store.load()
        configuration.naming = naming
        store.save(configuration)
        _write_notice(
            root,
            {
                "id": MIGRATION_ID,
                "backup_paths": [str(path.relative_to(root)) for path in backup_paths],
                "ignored_environment_keys": list(detection.ignored_environment_keys),
            },
        )
    except Exception:
        for path, content in originals.items():
            _atomic_write(path, content, mode=0o600)
        if original_project:
            _atomic_write(project_path, original_project)
        elif project_path.exists():
            project_path.unlink()
        raise

    return NamingMigrationResult(
        migrated=True,
        backup_paths=tuple(backup_paths),
        ignored_environment_keys=detection.ignored_environment_keys,
    )


def _legacy_naming_from_dotenv(project_root: Path) -> ProjectNamingConfiguration:
    legacy = _LegacyNamingSettings(
        _env_file=[project_root / ".env", project_root / "prod.env"],
    ).job
    return ProjectNamingConfiguration(
        post_dirname_format=legacy.post_dirname_format,
        post_structure=ProjectPostStructureConfiguration.model_validate(
            legacy.post_structure.model_dump(mode="python")
        ),
        mix_posts=legacy.mix_posts,
        sequential_filename=legacy.sequential_filename,
        sequential_filename_excludes=legacy.sequential_filename_excludes,
        filename_format=legacy.filename_format,
        group_by_year=legacy.group_by_year,
        group_by_month=legacy.group_by_month,
        year_dirname_format=legacy.year_dirname_format,
        month_dirname_format=legacy.month_dirname_format,
    )


def _content_revision(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _nested_value(values: dict[str, Any], field_path: str) -> Any:
    current: Any = values
    for part in field_path.split("."):
        current = current[part]
    return current


def _set_nested_value(values: dict[str, Any], field_path: str, value: Any) -> None:
    parts = field_path.split(".")
    current = values
    for part in parts[:-1]:
        current = current[part]
    current[parts[-1]] = value


def find_legacy_naming_keys(content: str) -> list[str]:
    """Return legacy naming keys still present in a dotenv document."""
    result: list[str] = []
    for line in content.splitlines():
        match = re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
        if match and match.group(1).upper() in LEGACY_ENV_KEYS:
            result.append(match.group(1))
    return result


def _without_legacy_keys(content: str) -> str:
    lines = content.splitlines(keepends=True)
    return "".join(line for line in lines if not _LEGACY_LINE.match(line))


def _write_notice(project_root: Path, payload: dict[str, object]) -> None:
    _atomic_write(
        project_root / MIGRATION_NOTICE_PATH,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        mode=0o600,
    )


def _atomic_write(path: Path, content: str, *, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        if mode is not None:
            os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
