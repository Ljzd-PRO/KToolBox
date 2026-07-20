from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from openapi_spec_validator import validate

from k_generator.normalize import normalize_schema

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_ROOT = Path(__file__).resolve().parent
RAW_SCHEMA_PATH = GENERATOR_ROOT / "pawchive_openapi.json"
OVERRIDES_PATH = GENERATOR_ROOT / "pawchive_openapi.overrides.json"
NORMALIZED_SCHEMA_PATH = GENERATOR_ROOT / "pawchive_openapi.normalized.json"
MODEL_PATH = REPOSITORY_ROOT / "ktoolbox" / "api" / "generated" / "models.py"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return cast(dict[str, Any], json.load(file))


def _write_normalized_schema(path: Path) -> None:
    raw_schema = _load_json(RAW_SCHEMA_PATH)
    overrides = _load_json(OVERRIDES_PATH)
    normalized_schema = normalize_schema(raw_schema, overrides)
    validate(normalized_schema)
    path.write_text(json.dumps(normalized_schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _generate_models(schema_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "datamodel_code_generator",
            "--input",
            str(schema_path),
            "--input-file-type",
            "openapi",
            "--output",
            str(output_path),
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--target-python-version",
            "3.10",
            "--openapi-scopes",
            "schemas",
            "--use-standard-collections",
            "--use-union-operator",
            "--use-annotated",
            "--field-constraints",
            "--use-field-description",
            "--extra-fields",
            "allow",
            "--reuse-model",
            "--disable-timestamp",
            "--formatters",
            "ruff-format",
            "ruff-check",
        ],
        check=True,
    )


def generate() -> None:
    """Regenerate the normalized contract and Pydantic response models."""
    _write_normalized_schema(NORMALIZED_SCHEMA_PATH)
    _generate_models(NORMALIZED_SCHEMA_PATH, MODEL_PATH)


def check() -> None:
    """Fail when committed generated artifacts are not reproducible."""
    # Keep temporary output beneath the repository so Ruff discovers the same
    # formatter configuration used for committed generated files.
    with TemporaryDirectory(prefix=".ktoolbox-contract-", dir=REPOSITORY_ROOT) as directory:
        temporary_root = Path(directory)
        normalized_path = temporary_root / NORMALIZED_SCHEMA_PATH.name
        model_path = temporary_root / MODEL_PATH.name
        _write_normalized_schema(normalized_path)
        _generate_models(normalized_path, model_path)

        stale = [
            tracked_path
            for tracked_path, generated_path in (
                (NORMALIZED_SCHEMA_PATH, normalized_path),
                (MODEL_PATH, model_path),
            )
            if not tracked_path.exists() or tracked_path.read_bytes() != generated_path.read_bytes()
        ]
        if stale:
            rendered = ", ".join(str(path.relative_to(REPOSITORY_ROOT)) for path in stale)
            raise SystemExit(f"Generated artifacts are stale: {rendered}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the normalized Pawchive API contract and Pydantic models.")
    parser.add_argument("--check", action="store_true", help="Check generated artifacts without modifying them.")
    arguments = parser.parse_args()
    check() if arguments.check else generate()


if __name__ == "__main__":
    main()
