from __future__ import annotations

import inspect
import json
from pathlib import Path

from openapi_spec_validator import validate

from k_generator.main import check as check_generated_artifacts
from k_generator.normalize import operation_keys
from ktoolbox.api.client import PawchiveClient
from ktoolbox.api.generated import models

ROOT = Path(__file__).resolve().parents[2]
RAW_SCHEMA = ROOT / "k_generator" / "pawchive_openapi.json"
NORMALIZED_SCHEMA = ROOT / "k_generator" / "pawchive_openapi.normalized.json"
OVERRIDES = ROOT / "k_generator" / "pawchive_openapi.overrides.json"

METHODS_BY_OPERATION = {
    "GET /creators": "list_creators",
    "GET /posts": "list_recent_posts",
    "GET /{service}/user/{creator_id}/profile": "get_creator_profile",
    "GET /{service}/user/{creator_id}": "list_creator_posts",
    "GET /{service}/user/{creator_id}/announcements": "list_announcements",
    "GET /{service}/user/{creator_id}/fancards": "list_fancards",
    "GET /{service}/user/{creator_id}/links": "list_creator_links",
    "GET /{service}/user/{creator_id}/post/{post_id}": "get_post",
    "GET /search_hash/{file_hash}": "search_file_by_hash",
    "POST /{service}/user/{creator_id}/post/{post}/flag": "flag_post",
    "GET /{service}/user/{creator_id}/post/{post}/flag": "is_post_flagged",
    "GET /{service}/user/{creator_id}/post/{post_id}/revisions": "list_post_revisions",
    "GET /{service}/user/{creator_id}/post/{post_id}/comments": "list_post_comments",
    "GET /app_version": "get_app_version",
}


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_contract_has_exact_public_and_authenticated_coverage() -> None:
    raw = load(RAW_SCHEMA)
    normalized = load(NORMALIZED_SCHEMA)
    overrides = load(OVERRIDES)

    assert len(operation_keys(raw)) == 19
    assert set(overrides["public_operations"]) == set(METHODS_BY_OPERATION)
    assert len(overrides["authenticated_operations"]) == 5
    assert set(overrides["public_operations"]) | set(overrides["authenticated_operations"]) == operation_keys(raw)
    assert operation_keys(normalized) == operation_keys(raw)
    assert all(hasattr(PawchiveClient, method) for method in METHODS_BY_OPERATION.values())

    public_methods = {
        name
        for name, member in inspect.getmembers(PawchiveClient, inspect.iscoroutinefunction)
        if not name.startswith("_") and name != "aclose"
    }
    assert public_methods == set(METHODS_BY_OPERATION.values())


def test_authenticated_operations_are_explicitly_excluded() -> None:
    overrides = load(OVERRIDES)
    normalized = load(NORMALIZED_SCHEMA)
    for operation_key in overrides["authenticated_operations"]:
        method, path = operation_key.split(" ", 1)
        operation = normalized["paths"][path][method.lower()]
        assert operation["security"] == [{"cookieAuth": []}]
        assert operation["operationId"] not in METHODS_BY_OPERATION.values()


def test_every_component_property_has_a_generated_field() -> None:
    overrides = load(OVERRIDES)
    schemas = overrides["component_schemas"]
    for name, schema in schemas.items():
        model = getattr(models, name)
        properties = set(schema.get("properties", {}))
        if name == "Revision":
            properties = set(models.Post.model_fields) | {"revision_id"}
        assert properties <= set(model.model_fields), name
        assert model.model_config["extra"] == "allow"


def test_normalized_schema_is_valid_and_generated_artifacts_are_current() -> None:
    normalized = load(NORMALIZED_SCHEMA)
    validate(normalized)
    check_generated_artifacts()


def test_raw_schema_remains_unmodified_by_normalization() -> None:
    raw = load(RAW_SCHEMA)
    assert "contact" in raw
    assert "contact" not in raw["info"]
    assert all(
        "operationId" not in operation
        for path_item in raw["paths"].values()
        for method, operation in path_item.items()
        if method in {"get", "post", "delete"}
    )
