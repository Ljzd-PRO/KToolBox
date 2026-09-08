from __future__ import annotations

import os
import re
from pathlib import Path
from tempfile import NamedTemporaryFile

from tzlocal import get_localzone_name

from ktoolbox.project_config import ProjectConfigStore, ProjectConfiguration
from ktoolbox.publication_time import PublishedTimeError, validate_iana_timezone

TARGET_TIMEZONE_ENV = "KTOOLBOX_PUBLISHED_TIME__TARGET_TIMEZONE"
_TARGET_LINE = re.compile(rf"^\s*(?:export\s+)?{re.escape(TARGET_TIMEZONE_ENV)}\s*=", re.MULTILINE)


def detect_host_timezone() -> str:
    """Return a validated, unambiguous IANA timezone for a newly created project."""

    try:
        candidate = get_localzone_name().strip()
        if "/" not in candidate and candidate not in {"UTC", "Etc/UTC", "GMT", "Etc/GMT"}:
            return "UTC"
        return validate_iana_timezone(candidate)
    except (PublishedTimeError, OSError, RuntimeError, ValueError):
        return "UTC"


def initialize_new_project(project_root: Path) -> str:
    """Create project configuration and persist the host timezone exactly once."""

    root = project_root.resolve()
    project_path = root / "ktoolbox.toml"
    dotenv_path = root / ".env"
    if project_path.exists():
        raise FileExistsError(project_path)

    original_dotenv = dotenv_path.read_bytes() if dotenv_path.is_file() else None
    original_mode = dotenv_path.stat().st_mode & 0o777 if dotenv_path.is_file() else None
    target_timezone = detect_host_timezone()
    dotenv_changed = _ensure_target_timezone(dotenv_path, target_timezone)
    try:
        ProjectConfigStore(project_path).save(ProjectConfiguration())
    except Exception:
        if dotenv_changed:
            if original_dotenv is None:
                dotenv_path.unlink(missing_ok=True)
            else:
                _atomic_write(dotenv_path, original_dotenv, mode=original_mode)
        raise
    from ktoolbox.configuration import load_configuration

    return load_configuration(root).published_time.target_timezone


def _ensure_target_timezone(path: Path, timezone_name: str) -> bool:
    content = path.read_text(encoding="utf-8") if path.is_file() else ""
    if _TARGET_LINE.search(content):
        return False
    separator = "" if not content or content.endswith("\n") else "\n"
    updated = f"{content}{separator}{TARGET_TIMEZONE_ENV}={timezone_name}\n"
    mode = path.stat().st_mode & 0o777 if path.is_file() else 0o600
    _atomic_write(path, updated.encode("utf-8"), mode=mode)
    return True


def _atomic_write(path: Path, content: bytes, *, mode: int | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="wb",
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
