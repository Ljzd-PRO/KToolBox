from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from ktoolbox.configuration import Configuration, RuntimeContext
from ktoolbox.webui.app import create_app
from ktoolbox.webui.error_responses import error_message, error_payload, validation_error_payload


def test_error_message_extracts_supported_backend_shapes() -> None:
    assert error_message(" Plain failure ", 400) == "Plain failure"
    assert error_message({"message": "Readable failure", "code": "failed"}, 400) == "Readable failure"
    assert error_message({"detail": {"reason": "Nested failure"}}, 400) == "Nested failure"
    assert error_message({"errors": ["First", "First", {"error": "Second"}]}, 400) == "First; Second"
    assert (
        error_message(
            [{"loc": ["body", "creator_id"], "msg": "Field required"}],
            422,
        )
        == "creator id: Field required"
    )
    assert error_message({"code": "unknown_shape"}, 409) == "Conflict"
    assert error_message(None, 799) == "HTTP 799"


def test_validation_payload_omits_submitted_input() -> None:
    payload = validation_error_payload(
        [
            {
                "type": "missing",
                "loc": ("body", "password", 0),
                "msg": "Field required",
                "input": {"password": "must-not-leak"},
                "ctx": {"secret": "must-not-leak"},
            }
        ],
        422,
    )

    assert payload == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "password", 0],
                "msg": "Field required",
            }
        ],
        "code": "validation_failed",
        "params": {"count": 1},
        "message": "password.0: Field required",
    }
    assert error_payload({"title": "Named failure"}, 400)["message"] == "Named failure"


@pytest.mark.asyncio
async def test_app_errors_always_include_a_readable_message(tmp_path: Path) -> None:
    app = create_app(
        RuntimeContext(
            tmp_path,
            Configuration(_env_file=None, webui={"username": "owner", "password": "secret"}),
        )
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 1234))
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            unauthorized = await client.get("/api/v1/project")
            assert unauthorized.json() == {
                "detail": "Authentication required",
                "code": "auth_required",
                "params": {},
                "message": "Authentication required",
            }

            invalid = await client.post("/api/v1/session/login", json={})
            body = invalid.json()
            assert invalid.status_code == 422
            assert "username: Field required" in body["message"]
            assert "password: Field required" in body["message"]
            assert body["code"] == "validation_failed"
            assert body["params"] == {"count": 2}
            assert all(set(issue) <= {"type", "loc", "msg"} for issue in body["detail"])
            assert "input" not in invalid.text
