from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from io import StringIO
from typing import Any, Literal

import tomlkit
from dotenv.parser import parse_stream
from pydantic import ValidationError

from ktoolbox.naming_migration import LEGACY_FIELD_PATHS
from ktoolbox.project_config import ProjectNamingConfiguration

MAX_NAMING_SOURCE_BYTES = 128 * 1024
NamingSourceFormat = Literal["env", "toml"]

_BOOLEAN_FIELDS = {
    "mix_posts",
    "sequential_filename",
    "group_by_year",
    "group_by_month",
}
_SET_FIELDS = {"sequential_filename_excludes"}


@dataclass(frozen=True, slots=True)
class NamingSourceIssue:
    code: str
    message: str
    path: str | None = None
    line: int | None = None
    column: int | None = None


@dataclass(frozen=True, slots=True)
class NamingSourceWarning:
    code: str
    count: int


@dataclass(frozen=True, slots=True)
class NamingSourceDifference:
    path: str
    source_value: object
    target_value: object


@dataclass(frozen=True, slots=True)
class ParsedNamingSource:
    format: NamingSourceFormat
    naming: ProjectNamingConfiguration
    digest: str
    recognized_fields: tuple[str, ...]
    defaulted_fields: tuple[str, ...]
    warnings: tuple[NamingSourceWarning, ...]
    differences: tuple[NamingSourceDifference, ...]


class NamingSourceParseError(ValueError):
    def __init__(self, issues: list[NamingSourceIssue]) -> None:
        super().__init__("invalid pasted naming configuration")
        self.issues = tuple(issues)


def parse_naming_source(
    source_format: NamingSourceFormat,
    content: str,
    *,
    target: ProjectNamingConfiguration,
) -> ParsedNamingSource:
    """Parse an in-memory naming source without expanding or persisting it."""

    if len(content.encode("utf-8")) > MAX_NAMING_SOURCE_BYTES:
        raise NamingSourceParseError(
            [
                NamingSourceIssue(
                    code="source_too_large",
                    message="pasted configuration exceeds the 128 KiB limit",
                )
            ]
        )
    if "\0" in content:
        raise NamingSourceParseError(
            [
                NamingSourceIssue(
                    code="invalid_character",
                    message="pasted configuration cannot contain NUL characters",
                )
            ]
        )
    if not content.strip():
        raise NamingSourceParseError(
            [
                NamingSourceIssue(
                    code="source_empty",
                    message="paste a legacy naming configuration before parsing",
                )
            ]
        )

    if source_format == "env":
        values, recognized, ignored, line_map = _parse_env(content)
    else:
        values, recognized, ignored, line_map = _parse_toml(content)

    try:
        naming = ProjectNamingConfiguration.model_validate(values)
    except ValidationError as error:
        issues = []
        for item in error.errors(
            include_url=False,
            include_context=False,
            include_input=False,
        ):
            path = ".".join(str(part) for part in item["loc"])
            issues.append(
                NamingSourceIssue(
                    code=str(item["type"]),
                    message=str(item["msg"]),
                    path=path or None,
                    line=line_map.get(path),
                )
            )
        raise NamingSourceParseError(issues) from error

    flattened_source = _flatten(naming.model_dump(mode="json"))
    flattened_target = _flatten(target.model_dump(mode="json"))
    recognized_set = set(recognized)
    defaulted = tuple(sorted(set(flattened_source) - recognized_set))
    differences = tuple(
        NamingSourceDifference(path, flattened_source[path], flattened_target.get(path))
        for path in sorted(flattened_source)
        if flattened_source[path] != flattened_target.get(path)
    )
    warnings = (NamingSourceWarning(code="ignored_unknown_entries", count=ignored),) if ignored else ()
    canonical = json.dumps(
        naming.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return ParsedNamingSource(
        format=source_format,
        naming=naming,
        digest=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        recognized_fields=tuple(sorted(recognized_set)),
        defaulted_fields=defaulted,
        warnings=warnings,
        differences=differences,
    )


def _parse_env(
    content: str,
) -> tuple[dict[str, Any], list[str], int, dict[str, int]]:
    values = ProjectNamingConfiguration().model_dump(mode="python")
    recognized: list[str] = []
    ignored = 0
    line_map: dict[str, int] = {}
    issues: list[NamingSourceIssue] = []
    for binding in parse_stream(StringIO(content)):
        if binding.error:
            issues.append(
                NamingSourceIssue(
                    code="dotenv_syntax",
                    message="invalid dotenv statement",
                    line=binding.original.line,
                )
            )
            continue
        if binding.key is None:
            continue
        field_path = LEGACY_FIELD_PATHS.get(binding.key.upper())
        if field_path is None:
            ignored += 1
            continue
        if binding.value is None:
            issues.append(
                NamingSourceIssue(
                    code="missing_value",
                    message="legacy naming entry requires a value",
                    path=field_path,
                    line=binding.original.line,
                )
            )
            continue
        try:
            value = _coerce_env_value(field_path, binding.value)
        except ValueError as error:
            issues.append(
                NamingSourceIssue(
                    code="invalid_value",
                    message=str(error),
                    path=field_path,
                    line=binding.original.line,
                )
            )
            continue
        _set_nested(values, field_path, value)
        recognized.append(field_path)
        line_map[field_path] = binding.original.line
    if issues:
        raise NamingSourceParseError(issues)
    if not recognized:
        raise NamingSourceParseError(
            [
                NamingSourceIssue(
                    code="no_legacy_naming_fields",
                    message="no supported legacy KTOOLBOX_JOB naming fields were found",
                )
            ]
        )
    return values, recognized, ignored, line_map


def _parse_toml(
    content: str,
) -> tuple[dict[str, Any], list[str], int, dict[str, int]]:
    try:
        document = tomlkit.parse(content).unwrap()
    except Exception as error:
        raise NamingSourceParseError(
            [
                NamingSourceIssue(
                    code="toml_syntax",
                    message="invalid TOML syntax",
                    line=getattr(error, "line", None),
                    column=getattr(error, "col", None),
                )
            ]
        ) from error
    if not isinstance(document, dict):
        raise NamingSourceParseError(
            [
                NamingSourceIssue(
                    code="invalid_toml_document",
                    message="TOML source must contain naming fields",
                )
            ]
        )

    naming_keys = set(ProjectNamingConfiguration.model_fields)
    if "naming" in document:
        raw = document["naming"]
        ignored = len(set(document) - {"naming"})
    elif naming_keys.intersection(document):
        raw = document
        ignored = 0
    else:
        raise NamingSourceParseError(
            [
                NamingSourceIssue(
                    code="no_naming_section",
                    message="TOML source does not contain a [naming] section or naming fields",
                )
            ]
        )
    if not isinstance(raw, dict):
        raise NamingSourceParseError(
            [
                NamingSourceIssue(
                    code="invalid_naming_section",
                    message="the naming section must be a TOML table",
                    path="naming",
                )
            ]
        )

    recognized = _provided_paths(raw)
    line_map = _toml_line_map(content, recognized)
    return dict(raw), recognized, ignored, line_map


def _coerce_env_value(path: str, value: str) -> object:
    if path in _BOOLEAN_FIELDS:
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        raise ValueError("expected a boolean value")
    if path in _SET_FIELDS:
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError("expected a JSON array") from error
        if not isinstance(decoded, list) or not all(isinstance(item, str) for item in decoded):
            raise ValueError("expected a JSON array of strings")
        return set(decoded)
    return value


def _set_nested(values: dict[str, Any], path: str, value: object) -> None:
    parts = path.split(".")
    current = values
    for part in parts[:-1]:
        current = current[part]
    current[parts[-1]] = value


def _flatten(value: object, prefix: str = "") -> dict[str, object]:
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, nested in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            result.update(_flatten(nested, path))
        return result
    return {prefix: value}


def _provided_paths(value: dict[str, Any], prefix: str = "") -> list[str]:
    result: list[str] = []
    for key, nested in value.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(nested, dict):
            result.extend(_provided_paths(nested, path))
        else:
            result.append(path)
    return result


def _toml_line_map(content: str, paths: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    current_table = ""
    wanted = set(paths)
    for line_number, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current_table = stripped.strip("[]").removeprefix("naming.").removeprefix("naming")
            current_table = current_table.strip(".")
            continue
        if "=" not in stripped or stripped.startswith("#"):
            continue
        key = stripped.split("=", 1)[0].strip().strip('"').strip("'")
        path = f"{current_table}.{key}" if current_table else key
        if path in wanted:
            result[path] = line_number
    return result
