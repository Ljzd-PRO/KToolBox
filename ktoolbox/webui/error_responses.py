from __future__ import annotations

from collections.abc import Mapping, Sequence
from http import HTTPStatus
from typing import Any

_LOCATION_PREFIXES = {"body", "cookie", "header", "path", "query"}
_MESSAGE_KEYS = ("message", "detail", "error", "reason", "title")


def error_payload(detail: Any, status_code: int) -> dict[str, Any]:
    return {"detail": detail, "message": error_message(detail, status_code)}


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
