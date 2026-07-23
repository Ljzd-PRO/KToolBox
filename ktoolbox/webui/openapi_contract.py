from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast

import yaml  # type: ignore[import-untyped]
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

from ktoolbox.webui.auth import CSRF_HEADER, SESSION_COOKIE

Safety = Literal["read", "write", "destructive"]


@dataclass(frozen=True, slots=True)
class MCPMetadata:
    enabled: bool = False
    name: str | None = None
    scope: Literal["mcp:read", "mcp:write"] | None = None
    safety: Safety | None = None
    open_world: bool = False


@dataclass(frozen=True, slots=True)
class OperationMetadata:
    summary: str
    description: str
    tag: str
    public: bool = False
    csrf: bool = False
    mcp: MCPMetadata = MCPMetadata()


def _read(name: str | None = None, *, open_world: bool = False) -> MCPMetadata:
    return MCPMetadata(True, name, "mcp:read", "read", open_world)


def _write(name: str | None = None, *, destructive: bool = False) -> MCPMetadata:
    return MCPMetadata(True, name, "mcp:write", "destructive" if destructive else "write")


OPERATIONS: dict[str, OperationMetadata] = {
    "config_schema": OperationMetadata(
        "Get configuration schema",
        "Return localized field metadata and redacted effective values for the project configuration.",
        "configuration",
        mcp=_read(),
    ),
    "get_dotenv": OperationMetadata(
        "Read an environment file",
        "Read the raw project .env or prod.env document together with its revision.",
        "configuration",
    ),
    "replace_dotenv": OperationMetadata(
        "Replace an environment file",
        "Atomically replace the raw project .env or prod.env document after an ETag check.",
        "configuration",
        csrf=True,
    ),
    "patch_dotenv": OperationMetadata(
        "Patch environment values",
        "Atomically update selected values in .env or prod.env after an ETag check.",
        "configuration",
        csrf=True,
    ),
    "validate_dotenv": OperationMetadata(
        "Validate an environment file",
        "Validate environment-file text without saving it.",
        "configuration",
    ),
    "example_configuration": OperationMetadata(
        "Download example configuration",
        "Render and download a documented example environment file.",
        "configuration",
    ),
    "get_project_config": OperationMetadata(
        "Read project configuration",
        "Read the raw ktoolbox.toml document and its parsed project configuration.",
        "configuration",
    ),
    "replace_project_config": OperationMetadata(
        "Replace project configuration",
        "Atomically replace ktoolbox.toml after validation and an ETag check.",
        "configuration",
        csrf=True,
    ),
    "validate_project_config": OperationMetadata(
        "Validate project configuration",
        "Validate ktoolbox.toml text without saving it.",
        "configuration",
    ),
    "list_creators": OperationMetadata(
        "List configured creators",
        "List the project creator roster with cached Pawchive presentation names.",
        "creators",
        mcp=_read(),
    ),
    "add_creator": OperationMetadata(
        "Add a creator",
        "Add a creator identity to the project roster.",
        "creators",
        csrf=True,
        mcp=_write(),
    ),
    "update_creator": OperationMetadata(
        "Update a creator",
        "Update the note and enabled state of a configured creator.",
        "creators",
        csrf=True,
        mcp=_write(),
    ),
    "delete_creator": OperationMetadata(
        "Remove a creator",
        "Remove a creator from the project roster and clear its cached presentation profile.",
        "creators",
        csrf=True,
        mcp=_write(destructive=True),
    ),
    "list_blockers": OperationMetadata(
        "List ignore rules",
        "Return the ordered project ignore-rule definitions.",
        "ignore-rules",
        mcp=_read(),
    ),
    "replace_blockers": OperationMetadata(
        "Replace ignore rules",
        "Validate and replace the complete ordered ignore-rule collection.",
        "ignore-rules",
        csrf=True,
        mcp=_write(destructive=True),
    ),
    "browse_filesystem": OperationMetadata(
        "Browse files and directories",
        "Browse a project or host filesystem location for the WebUI path picker.",
        "filesystem",
    ),
    "create_directory": OperationMetadata(
        "Create a directory",
        "Create a directory through the WebUI path picker.",
        "filesystem",
        csrf=True,
    ),
    "delete_directory": OperationMetadata(
        "Delete an empty directory",
        "Delete an empty directory through the WebUI path picker.",
        "filesystem",
        csrf=True,
    ),
    "creators": OperationMetadata(
        "Search Pawchive creators",
        "Search Pawchive for creators using an ID, name, or platform filter.",
        "pawchive",
        mcp=_read("search_creators", open_world=True),
    ),
    "posts": OperationMetadata(
        "Search Pawchive works",
        "Search Pawchive for works using creator identity and text filters.",
        "pawchive",
        mcp=_read("search_works", open_world=True),
    ),
    "post_details": OperationMetadata(
        "Get a Pawchive work",
        "Return one Pawchive work or a selected historical revision.",
        "pawchive",
    ),
    "post_revisions": OperationMetadata(
        "List work revisions",
        "Return the known historical revisions for one Pawchive work.",
        "pawchive",
        mcp=_read("list_work_revisions", open_world=True),
    ),
    "site_version": OperationMetadata(
        "Get Pawchive version",
        "Return the version reported by the configured Pawchive service.",
        "pawchive",
        mcp=_read("get_pawchive_version", open_world=True),
    ),
    "list_tasks": OperationMetadata(
        "List tasks",
        "Return the persistent task queue in scheduling order.",
        "tasks",
        mcp=_read(),
    ),
    "create_task": OperationMetadata(
        "Create a task",
        "Create and enqueue a sync-author or download-work task.",
        "tasks",
        csrf=True,
        mcp=_write(),
    ),
    "get_task": OperationMetadata(
        "Get a task",
        "Return one persistent task with its current progress and presentation snapshot.",
        "tasks",
        mcp=_read(),
    ),
    "update_task": OperationMetadata(
        "Update a task",
        "Update the editable definition of a non-running task.",
        "tasks",
        csrf=True,
        mcp=_write(),
    ),
    "delete_task": OperationMetadata(
        "Delete a task",
        "Delete a task record and optionally its verified output artifacts.",
        "tasks",
        csrf=True,
    ),
    "pause_task": OperationMetadata(
        "Pause a task",
        "Request cooperative pause for a running task.",
        "tasks",
        csrf=True,
        mcp=_write(),
    ),
    "stop_task": OperationMetadata(
        "Stop a task",
        "Request cooperative stop for an active task.",
        "tasks",
        csrf=True,
        mcp=_write(),
    ),
    "resume_task": OperationMetadata(
        "Resume a task",
        "Resume a paused, stopped, interrupted, or failed task as a new attempt.",
        "tasks",
        csrf=True,
        mcp=_write(),
    ),
    "task_attempts": OperationMetadata(
        "List task attempts",
        "Return the immutable execution attempts recorded for one task.",
        "tasks",
        mcp=_read(),
    ),
    "task_events": OperationMetadata(
        "List task events",
        "Return at most 200 task progress and log events after a cursor.",
        "tasks",
        mcp=_read(),
    ),
    "cleanup_preview": OperationMetadata(
        "Preview task cleanup",
        "Preview artifacts that may be removed with a task without changing files.",
        "tasks",
        mcp=_read(),
    ),
    "event_stream": OperationMetadata(
        "Stream task events",
        "Stream task and progress events to the browser using server-sent events.",
        "tasks",
    ),
    "health": OperationMetadata(
        "Check service health",
        "Return a minimal process health response.",
        "system",
        public=True,
    ),
    "login": OperationMetadata(
        "Log in",
        "Authenticate the configured WebUI account and create a browser session.",
        "session",
        public=True,
    ),
    "current_session": OperationMetadata(
        "Get current session",
        "Return the authenticated WebUI browser session.",
        "session",
    ),
    "logout": OperationMetadata(
        "Log out",
        "Revoke the current WebUI browser session.",
        "session",
        csrf=True,
    ),
    "project": OperationMetadata(
        "Get project summary",
        "Return the active project root, configuration files, and KToolBox version.",
        "project",
        mcp=_read("get_project_summary"),
    ),
    "download_openapi": OperationMetadata(
        "Download WebUI OpenAPI",
        "Download the canonical YAML contract for the authenticated WebUI REST API.",
        "mcp",
    ),
    "mcp_status": OperationMetadata(
        "Get MCP status",
        "Return the in-process MCP endpoint, transport, and curated tool count.",
        "mcp",
    ),
    "list_mcp_tools": OperationMetadata(
        "List MCP tools",
        "Return the curated MCP tool catalog shown in the WebUI.",
        "mcp",
    ),
    "list_mcp_tokens": OperationMetadata(
        "List MCP tokens",
        "List MCP token metadata without returning token secrets.",
        "mcp",
    ),
    "create_mcp_token": OperationMetadata(
        "Create an MCP token",
        "Confirm the WebUI account password and create a one-time MCP bearer token.",
        "mcp",
        csrf=True,
    ),
    "revoke_mcp_token": OperationMetadata(
        "Revoke an MCP token",
        "Immediately revoke an MCP bearer token owned by the current WebUI account.",
        "mcp",
        csrf=True,
    ),
    "browse_project_files": OperationMetadata(
        "Browse project files",
        "Browse visible files and directories below the active project root without following paths outside it.",
        "project",
        mcp=_read(),
    ),
    "patch_mcp_configuration": OperationMetadata(
        "Patch safe configuration fields",
        "Update validated non-secret environment configuration fields by their documented field paths.",
        "configuration",
        csrf=True,
        mcp=_write(),
    ),
    "delete_task_record": OperationMetadata(
        "Delete a task record",
        "Delete an inactive task record and its logs while always preserving downloaded output files.",
        "tasks",
        csrf=True,
        mcp=_write(destructive=True),
    ),
    "get_mcp_work": OperationMetadata(
        "Get a bounded Pawchive work",
        "Return one Pawchive work with content omitted by default and explicitly capped when requested.",
        "pawchive",
        mcp=_read("get_work", open_world=True),
    ),
}


def stable_operation_id(route: APIRoute) -> str:
    return route.name


def build_openapi_schema(app: FastAPI) -> dict[str, Any]:
    schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=(
            "Authenticated REST API for the KToolBox WebUI. Selected operations also define the curated "
            "MCP tool surface through x-ktoolbox-mcp metadata."
        ),
        routes=app.routes,
    )
    schema["info"]["license"] = {"name": "BSD-3-Clause", "identifier": "BSD-3-Clause"}
    components = schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["WebUISession"] = {
        "type": "apiKey",
        "in": "cookie",
        "name": SESSION_COOKIE,
        "description": "Opaque browser session created by the login operation.",
    }

    found: set[str] = set()
    for path_item in schema.get("paths", {}).values():
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete", "options", "head", "trace"}:
                continue
            operation_id = operation["operationId"]
            metadata = OPERATIONS.get(operation_id)
            if metadata is None:
                raise RuntimeError(f"missing OpenAPI metadata for operation {operation_id!r}")
            found.add(operation_id)
            operation["summary"] = metadata.summary
            operation["description"] = metadata.description
            operation["tags"] = [metadata.tag]
            operation["security"] = [] if metadata.public else [{"WebUISession": []}]
            operation["x-ktoolbox-mcp"] = {
                "enabled": metadata.mcp.enabled,
                "name": metadata.mcp.name or operation_id,
                "scope": metadata.mcp.scope,
                "safety": metadata.mcp.safety,
                "openWorld": metadata.mcp.open_world,
            }
            if metadata.csrf:
                parameters = operation.setdefault("parameters", [])
                parameters.append(
                    {
                        "name": CSRF_HEADER,
                        "in": "header",
                        "required": True,
                        "description": "CSRF token returned by the current browser session.",
                        "schema": {"type": "string", "minLength": 1},
                    }
                )

    unknown = set(OPERATIONS) - found
    if unknown:
        raise RuntimeError(f"OpenAPI metadata references missing operations: {', '.join(sorted(unknown))}")
    schema["tags"] = [
        {"name": "session", "description": "Browser account sessions."},
        {"name": "project", "description": "Active project information."},
        {"name": "configuration", "description": "Typed and raw project configuration."},
        {"name": "creators", "description": "Configured creator roster."},
        {"name": "ignore-rules", "description": "Ordered work ignore rules."},
        {"name": "tasks", "description": "Persistent task queue and execution history."},
        {"name": "pawchive", "description": "Public Pawchive search and work data."},
        {"name": "filesystem", "description": "WebUI filesystem path picker."},
        {"name": "system", "description": "Service status."},
        {"name": "mcp", "description": "MCP status, connection metadata, and access tokens."},
    ]
    return schema


def mcp_tool_catalog() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for operation_id, metadata in OPERATIONS.items():
        if not metadata.mcp.enabled:
            continue
        result.append(
            {
                "name": metadata.mcp.name or operation_id,
                "operation_id": operation_id,
                "description": metadata.description,
                "category": metadata.tag,
                "scope": metadata.mcp.scope,
                "safety": metadata.mcp.safety,
                "open_world": metadata.mcp.open_world,
            }
        )
    return result


class _NoAliasDumper(yaml.SafeDumper):  # type: ignore[misc]
    def ignore_aliases(self, data: Any) -> bool:
        return True


def dump_openapi_yaml(schema: dict[str, Any]) -> str:
    return cast(
        str,
        yaml.dump(
            schema,
            Dumper=_NoAliasDumper,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            width=120,
        ),
    )
