from __future__ import annotations

from pathlib import Path

import yaml
from openapi_spec_validator import validate

from ktoolbox.configuration import RuntimeContext
from ktoolbox.webui.app import create_app
from ktoolbox.webui.openapi_contract import OPERATIONS, dump_openapi_yaml

ROOT = Path(__file__).resolve().parents[2]
COMMITTED_SCHEMA = ROOT / "webui" / "openapi.yaml"
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}


def test_committed_webui_openapi_is_valid_and_current() -> None:
    schema = create_app(RuntimeContext.from_project(ROOT)).openapi()

    validate(schema)
    assert COMMITTED_SCHEMA.read_text(encoding="utf-8") == dump_openapi_yaml(schema)
    assert yaml.safe_load(COMMITTED_SCHEMA.read_text(encoding="utf-8")) == schema


def test_all_operations_have_stable_metadata_and_explicit_mcp_policy() -> None:
    schema = yaml.safe_load(COMMITTED_SCHEMA.read_text(encoding="utf-8"))
    operations = [
        operation
        for path_item in schema["paths"].values()
        for method, operation in path_item.items()
        if method in HTTP_METHODS
    ]

    operation_ids = [operation["operationId"] for operation in operations]
    assert len(operation_ids) == len(set(operation_ids))
    assert set(operation_ids) == set(OPERATIONS)
    assert all(operation["summary"] for operation in operations)
    assert all(operation["description"] for operation in operations)
    assert all(len(operation["tags"]) == 1 for operation in operations)
    assert all("x-ktoolbox-mcp" in operation for operation in operations)

    enabled = {
        operation["x-ktoolbox-mcp"]["name"]: operation["x-ktoolbox-mcp"]
        for operation in operations
        if operation["x-ktoolbox-mcp"]["enabled"]
    }
    assert enabled
    assert all(metadata["scope"] in {"mcp:read", "mcp:write"} for metadata in enabled.values())
    assert all(metadata["safety"] in {"read", "write", "destructive"} for metadata in enabled.values())
    assert (
        not {
            "login",
            "logout",
            "current_session",
            "event_stream",
            "browse_filesystem",
            "create_directory",
            "delete_directory",
            "delete_task",
        }
        & enabled.keys()
    )


def test_openapi_documents_browser_session_and_csrf_security() -> None:
    schema = yaml.safe_load(COMMITTED_SCHEMA.read_text(encoding="utf-8"))
    security = schema["components"]["securitySchemes"]["WebUISession"]

    assert security == {
        "type": "apiKey",
        "in": "cookie",
        "name": "ktoolbox_session",
        "description": "Opaque browser session created by the login operation.",
    }
    assert schema["paths"]["/api/v1/session/login"]["post"]["security"] == []
    create_task = schema["paths"]["/api/v1/tasks"]["post"]
    assert create_task["security"] == [{"WebUISession": []}]
    assert any(parameter["name"] == "X-CSRF-Token" for parameter in create_task["parameters"])
