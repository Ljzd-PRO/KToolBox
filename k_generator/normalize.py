from __future__ import annotations

from copy import deepcopy
from typing import Any

HTTP_METHODS = {"delete", "get", "head", "options", "patch", "post", "put", "trace"}


class ContractOverrideError(ValueError):
    """Raised when the raw contract and compatibility overrides disagree."""


def operation_keys(document: dict[str, Any]) -> set[str]:
    """Return normalized ``METHOD /path`` keys for every OpenAPI operation."""
    return {
        f"{method.upper()} {path}"
        for path, path_item in document["paths"].items()
        for method in path_item
        if method in HTTP_METHODS
    }


def _response_schema(response: dict[str, Any]) -> dict[str, Any]:
    if response.get("type") == "string":
        return {"type": "string"}

    model = response["model"]
    schema: dict[str, Any] = {"$ref": f"#/components/schemas/{model}"}
    if response.get("many", False):
        schema = {"type": "array", "items": schema}
    return schema


def _apply_parameter_constraints(operation: dict[str, Any]) -> None:
    for parameter in operation.get("parameters", []):
        schema = parameter.setdefault("schema", {})
        name = parameter.get("name")
        location = parameter.get("in")

        if location == "path" and schema.get("type") == "string":
            schema["minLength"] = 1
        if location == "query" and name == "q":
            schema["minLength"] = 3
        if location == "query" and name == "o":
            schema.update({"minimum": 0, "multipleOf": 50})
        if location == "path" and name == "file_hash":
            schema.update({"minLength": 64, "maxLength": 64, "pattern": "^[0-9a-fA-F]{64}$"})
            schema.pop("format", None)


def normalize_schema(raw: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Apply the reviewed Pawchive compatibility overlay to the raw schema."""
    normalized = deepcopy(raw)

    contact = normalized.pop("contact", None)
    if contact:
        normalized["info"]["contact"] = contact

    expected_operations = set(overrides["operations"])
    actual_operations = operation_keys(normalized)
    if actual_operations != expected_operations:
        missing = sorted(actual_operations - expected_operations)
        stale = sorted(expected_operations - actual_operations)
        raise ContractOverrideError(f"Operation override mismatch; missing={missing}, stale={stale}")

    public_operations = set(overrides["public_operations"])
    authenticated_operations = set(overrides["authenticated_operations"])
    if public_operations & authenticated_operations:
        raise ContractOverrideError("Public and authenticated operation sets overlap")
    if public_operations | authenticated_operations != actual_operations:
        raise ContractOverrideError("Public and authenticated operation sets do not cover the raw schema")

    normalized["components"]["schemas"] = deepcopy(overrides["component_schemas"])
    normalized["x-ktoolbox-source-schema"] = overrides["source"]
    normalized["x-ktoolbox-public-operations"] = sorted(public_operations)
    normalized["x-ktoolbox-authenticated-operations"] = sorted(authenticated_operations)
    normalized["x-ktoolbox-observations"] = list(overrides["observations"])

    for operation_key, operation_override in overrides["operations"].items():
        method, path = operation_key.split(" ", 1)
        operation = normalized["paths"][path][method.lower()]
        operation["operationId"] = operation_override["operationId"]
        _apply_parameter_constraints(operation)

        for status, response in tuple(operation["responses"].items()):
            if response.get("$ref") == "#/components/schemas/401":
                operation["responses"][status] = {
                    "description": "Authentication required.",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
                }

        response_override = operation_override.get("response")
        if response_override is None:
            continue
        status = response_override["status"]
        media_type = response_override["media_type"]
        response = operation["responses"][status]
        response["content"] = {media_type: {"schema": _response_schema(response_override)}}

    return normalized
