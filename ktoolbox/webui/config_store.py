from __future__ import annotations

import hashlib
import io
import os
import re
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from dotenv import set_key, unset_key
from dotenv.parser import parse_stream
from pydantic import ValidationError

from ktoolbox.configuration import Configuration, RuntimeContext

_ALLOWED_FILES = {"dotenv": ".env", "production": "prod.env"}
_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_MAX_FILE_SIZE = 1024 * 1024


class ConfigurationFileError(ValueError):
    pass


class ConfigurationConflictError(ConfigurationFileError):
    pass


@dataclass(frozen=True, slots=True)
class ConfigurationDocument:
    name: str
    path: Path
    content: str
    revision: str


def content_revision(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class DotenvFileStore:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def read(self, name: str) -> ConfigurationDocument:
        path = self._path(name)
        try:
            content = path.read_text(encoding="utf-8") if path.exists() else ""
        except OSError as error:
            raise ConfigurationFileError(f"unable to read {path.name}: {error}") from error
        return ConfigurationDocument(name, path, content, content_revision(content))

    def replace(self, name: str, content: str, expected_revision: str) -> RuntimeContext:
        current = self.read(name)
        self._check_revision(current, expected_revision)
        self.validate(name, content)
        self._atomic_write(current.path, content)
        return RuntimeContext.from_project(self.project_root)

    def validate(self, name: str, content: str) -> None:
        """Validate a dotenv candidate against the other project dotenv file."""
        self._path(name)
        self._validate_content(content)
        self._validate_configuration(name, content)

    def patch(self, name: str, values: dict[str, str | None], expected_revision: str) -> RuntimeContext:
        current = self.read(name)
        self._check_revision(current, expected_revision)
        for key in values:
            if not _KEY_PATTERN.fullmatch(key):
                raise ConfigurationFileError(f"invalid environment key: {key}")
        with TemporaryDirectory() as temporary_directory:
            candidate_path = Path(temporary_directory) / current.path.name
            candidate_path.write_text(current.content, encoding="utf-8")
            for key, value in values.items():
                if value is None:
                    unset_key(candidate_path, key)
                else:
                    set_key(candidate_path, key, value, quote_mode="auto")
            candidate = candidate_path.read_text(encoding="utf-8")
        return self.replace(name, candidate, expected_revision)

    def _validate_configuration(self, candidate_name: str, candidate: str) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for name, filename in _ALLOWED_FILES.items():
                content = candidate if name == candidate_name else self.read(name).content
                (root / filename).write_text(content, encoding="utf-8")
            try:
                Configuration(_env_file=[root / ".env", root / "prod.env"])
            except (ValidationError, ValueError, OSError) as error:
                raise ConfigurationFileError(f"configuration validation failed: {error}") from error

    @staticmethod
    def _validate_content(content: str) -> None:
        if len(content.encode("utf-8")) > _MAX_FILE_SIZE:
            raise ConfigurationFileError("dotenv file exceeds the 1 MiB limit")
        errors = [binding for binding in parse_stream(io.StringIO(content)) if binding.error]
        if errors:
            lines = ", ".join(str(binding.original.line) for binding in errors)
            raise ConfigurationFileError(f"invalid dotenv syntax on line(s): {lines}")

    @staticmethod
    def _check_revision(document: ConfigurationDocument, expected_revision: str) -> None:
        normalized = expected_revision.strip().strip('"')
        if normalized != document.revision:
            raise ConfigurationConflictError(f"{document.path.name} changed since it was loaded")

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
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
            os.chmod(temporary_path, 0o600)
            os.replace(temporary_path, path)
        except OSError as error:
            raise ConfigurationFileError(f"unable to save {path.name}: {error}") from error
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def _path(self, name: str) -> Path:
        try:
            filename = _ALLOWED_FILES[name]
        except KeyError as error:
            raise ConfigurationFileError(f"unknown dotenv document: {name}") from error
        return self.project_root / filename
