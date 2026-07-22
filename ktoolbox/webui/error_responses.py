from __future__ import annotations

from collections.abc import Mapping, Sequence
from http import HTTPStatus
from typing import Any

_LOCATION_PREFIXES = {"body", "cookie", "header", "path", "query"}
_MESSAGE_KEYS = ("message", "detail", "error", "reason", "title")
_EXACT_CODES = {
    "Too many login attempts. Try again later.": "auth_rate_limited",
    "Invalid username or password": "auth_invalid_credentials",
    "Authentication required": "auth_required",
    "Session expired": "auth_session_expired",
    "Invalid CSRF token": "auth_csrf_invalid",
    "Cross-origin request rejected": "auth_origin_rejected",
    "If-Match is required": "precondition_required",
    "creator not found": "creator_not_found",
    "revision not found": "revision_not_found",
    "task not found": "task_not_found",
    "invalid Last-Event-ID": "invalid_event_id",
    "task output must stay inside the project directory": "task_output_invalid",
    "no enabled creators are configured": "no_enabled_creators",
    "the post URL does not contain a service, creator, and post ID": "post_identity_invalid",
    "provide a post URL or service, creator_id, and post_id": "post_identity_invalid",
    "start_time must not be later than end_time": "date_range_invalid",
    "presentation snapshots are only supported for download tasks": "presentation_invalid",
    "presentation target_key does not match the task target": "presentation_invalid",
    "not found": "resource_not_found",
}


def error_payload(detail: Any, status_code: int) -> dict[str, Any]:
    message = error_message(detail, status_code)
    code, params = _error_identity(detail, message, status_code)
    return {"detail": detail, "code": code, "params": params, "message": message}


def validation_error_payload(errors: Sequence[Mapping[str, Any]], status_code: int) -> dict[str, Any]:
    detail = [_sanitized_validation_issue(issue) for issue in errors]
    return error_payload(detail, status_code)


def error_message(detail: Any, status_code: int) -> str:
    messages = list(dict.fromkeys(_detail_messages(detail)))
    if messages:
        return "; ".join(messages)
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return f"HTTP {status_code}"


def _detail_messages(detail: Any) -> list[str]:
    if isinstance(detail, str):
        text = detail.strip()
        return [text] if text else []
    if isinstance(detail, Mapping):
        validation_message = _validation_issue_message(detail)
        if validation_message:
            return [validation_message]
        for key in _MESSAGE_KEYS:
            if key in detail:
                messages = _detail_messages(detail[key])
                if messages:
                    return messages
        if "errors" in detail:
            return _detail_messages(detail["errors"])
        return []
    if isinstance(detail, Sequence) and not isinstance(detail, (str, bytes, bytearray)):
        return [message for item in detail for message in _detail_messages(item)]
    return []


def _validation_issue_message(issue: Mapping[str, Any]) -> str | None:
    message = issue.get("msg")
    if not isinstance(message, str) or not message.strip():
        return None
    location = _location_text(issue.get("loc"))
    return f"{location}: {message.strip()}" if location else message.strip()


def _location_text(location: Any) -> str:
    if not isinstance(location, Sequence) or isinstance(location, (str, bytes, bytearray)):
        return ""
    parts = [str(part) for part in location]
    if parts and parts[0] in _LOCATION_PREFIXES:
        parts.pop(0)
    return ".".join(part.replace("_", " ") for part in parts)


def _sanitized_validation_issue(issue: Mapping[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    if "type" in issue:
        sanitized["type"] = str(issue["type"])
    location = issue.get("loc")
    if isinstance(location, Sequence) and not isinstance(location, (str, bytes, bytearray)):
        sanitized["loc"] = [str(part) if not isinstance(part, int) else part for part in location]
    if "msg" in issue:
        sanitized["msg"] = str(issue["msg"])
    return sanitized


def _error_identity(detail: Any, message: str, status_code: int) -> tuple[str, dict[str, Any]]:
    if isinstance(detail, Mapping):
        explicit_code = detail.get("code")
        if isinstance(explicit_code, str) and explicit_code:
            explicit_params = detail.get("params")
            params = dict(explicit_params) if isinstance(explicit_params, Mapping) else {}
            params.update(
                {
                    key: value
                    for key, value in detail.items()
                    if key not in {"code", "detail", "errors", "message", "params", "reason", "title"}
                }
            )
            return explicit_code, params
    if code := _EXACT_CODES.get(message):
        return code, {}
    lowered = message.casefold()
    if "changed since it was loaded" in lowered:
        return "config_conflict", {}
    if "configuration validation failed" in lowered or "invalid dotenv" in lowered:
        return "config_invalid", {}
    if "invalid environment key" in lowered or "unknown dotenv document" in lowered:
        return "config_invalid", {}
    if "identical active task" in lowered:
        return "task_duplicate", _mapping_params(detail)
    if "task cannot" in lowered or "stop the task" in lowered or "pause or stop" in lowered:
        return "task_state_conflict", {}
    if isinstance(detail, Sequence) and not isinstance(detail, (str, bytes, bytearray)):
        return "validation_failed", {"count": len(detail)}
    if status_code == 401:
        return "auth_required", {}
    if status_code == 403:
        return "permission_denied", {}
    if status_code == 404:
        return "resource_not_found", {}
    if status_code == 409:
        return "conflict", {}
    if status_code == 422:
        return "validation_failed", {}
    if status_code == 429:
        return "rate_limited", {}
    if status_code >= 500:
        return "server_error", {}
    return "request_failed", {}


def _mapping_params(detail: Any) -> dict[str, Any]:
    if not isinstance(detail, Mapping):
        return {}
    return {
        key: value
        for key, value in detail.items()
        if key not in {"code", "detail", "errors", "message", "params", "reason", "title"}
    }
