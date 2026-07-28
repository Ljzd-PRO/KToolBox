from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import ClassVar

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
