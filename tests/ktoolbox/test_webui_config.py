from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest

from ktoolbox.configuration import Configuration, RuntimeContext
from ktoolbox.webui.app import create_app
from ktoolbox.webui.auth import CSRF_HEADER
from ktoolbox.webui.config_schema import build_config_schema, missing_config_metadata
from ktoolbox.webui.config_store import ConfigurationConflictError, ConfigurationFileError, DotenvFileStore


@asynccontextmanager
async def configured_client(tmp_path: Path) -> AsyncIterator[tuple[httpx.AsyncClient, str]]:
    (tmp_path / "ktoolbox.toml").write_text(
        "# project comment\nschema_version = 1\ncreators = []\nblockers = []\n",
        encoding="utf-8",
    )
    configuration = Configuration(
        _env_file=None,
        webui={"username": "owner", "password": "secret"},
        downloader={"session_key": "file-cookie"},
    )
    app = create_app(RuntimeContext(tmp_path, configuration))
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 1234))
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            login = await client.post(
                "/api/v1/session/login",
                json={"username": "owner", "password": "secret"},
            )
            yield client, login.json()["csrf_token"]


def test_config_metadata_is_complete_bilingual_and_redacts_secrets(tmp_path: Path) -> None:
    assert missing_config_metadata() == {
        "labels": [],
        "english_descriptions": [],
        "chinese_descriptions": [],
    }
    configuration = Configuration(
        _env_file=None,
        downloader={"session_key": "cookie"},
        webui={"username": "owner", "password": "secret"},
    )
    english = build_config_schema(configuration, tmp_path, "en")
    chinese = build_config_schema(configuration, tmp_path, "zh-CN")
    assert len(english.fields) == len(chinese.fields) >= 60
    assert all(field.label and "_" not in field.label for field in english.fields)
    assert all(field.description for field in english.fields + chinese.fields)
    secret = next(field for field in english.fields if field.path == "downloader.session_key")
    assert secret.secret is True
    assert secret.value is None
    assert secret.default is None
    assert secret.is_set is True
    count = next(field for field in english.fields if field.path == "job.count")
    assert count.label == "Concurrent downloads"
    assert count.json_schema["minimum"] == 1
    assert next(field for field in chinese.fields if field.path == "job.count").label == "并发下载数"


def test_dotenv_store_preserves_comments_validates_and_detects_conflicts(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text("# keep me\nKTOOLBOX_JOB__COUNT=4\n", encoding="utf-8")
    store = DotenvFileStore(tmp_path)
    before = store.read("dotenv")

    context = store.patch(
        "dotenv",
        {"KTOOLBOX_JOB__COUNT": "7", "KTOOLBOX_JOB__MIX_POSTS": "true"},
        before.revision,
    )
    assert "# keep me" in path.read_text(encoding="utf-8")
    assert context.configuration.job.count == 7
    assert context.configuration.job.mix_posts is True
    assert path.stat().st_mode & 0o777 == 0o600

    with pytest.raises(ConfigurationConflictError):
        store.patch("dotenv", {"KTOOLBOX_JOB__COUNT": "8"}, before.revision)
    with pytest.raises(ConfigurationFileError, match="invalid environment key"):
        store.patch("dotenv", {"BAD KEY": "value"}, store.read("dotenv").revision)
    with pytest.raises(ConfigurationFileError, match="validation failed"):
        store.replace("dotenv", "KTOOLBOX_JOB__COUNT=invalid\n", store.read("dotenv").revision)
    with pytest.raises(ConfigurationFileError, match="1 MiB"):
        store.replace("dotenv", "X=" + "x" * (1024 * 1024), store.read("dotenv").revision)
    with pytest.raises(ConfigurationFileError, match="unknown dotenv"):
        store.read("outside")
    before_validation = path.read_text(encoding="utf-8")
    store.validate("dotenv", "KTOOLBOX_JOB__COUNT=9\n")
    assert path.read_text(encoding="utf-8") == before_validation


@pytest.mark.asyncio
async def test_config_schema_and_dotenv_endpoints(tmp_path: Path) -> None:
    async with configured_client(tmp_path) as (client, csrf):
        english = await client.get("/api/v1/config/schema?locale=en")
        chinese = await client.get("/api/v1/config/schema?locale=zh-CN")
        assert english.status_code == chinese.status_code == 200
        assert english.json()["fields"][0]["label"] != chinese.json()["fields"][0]["label"]

        document = await client.get("/api/v1/config/dotenv/dotenv")
        assert document.status_code == 200
        revision = document.json()["revision"]
        assert document.headers["etag"] == f'"{revision}"'

        missing_precondition = await client.patch(
            "/api/v1/config/dotenv/dotenv",
            headers={CSRF_HEADER: csrf},
            json={"values": {"KTOOLBOX_JOB__COUNT": "7"}},
        )
        assert missing_precondition.status_code == 428

        updated = await client.patch(
            "/api/v1/config/dotenv/dotenv",
            headers={CSRF_HEADER: csrf, "If-Match": document.headers["etag"]},
            json={"values": {"KTOOLBOX_JOB__COUNT": "7"}},
        )
        assert updated.status_code == 200
        assert "KTOOLBOX_JOB__COUNT=7" in updated.json()["content"]

        stale = await client.put(
            "/api/v1/config/dotenv/dotenv",
            headers={CSRF_HEADER: csrf, "If-Match": document.headers["etag"]},
            json={"content": "KTOOLBOX_JOB__COUNT=8\n"},
        )
        assert stale.status_code == 409

        refreshed_schema = await client.get("/api/v1/config/schema")
        count = next(field for field in refreshed_schema.json()["fields"] if field["path"] == "job.count")
        assert count["value"] == 7
        assert count["source"] == ".env"

        valid = await client.post(
            "/api/v1/config/dotenv/dotenv/validate",
            json={"content": "KTOOLBOX_JOB__COUNT=8\n"},
        )
        assert valid.json() == {"valid": True}
        invalid = await client.post(
            "/api/v1/config/dotenv/dotenv/validate",
            json={"content": "KTOOLBOX_JOB__COUNT=nope\n"},
        )
        assert invalid.status_code == 422

        example = await client.get("/api/v1/config/example")
        assert example.status_code == 200
        assert "attachment; filename=\"example.env\"" == example.headers["content-disposition"]
        assert "KTOOLBOX" in example.text


@pytest.mark.asyncio
async def test_project_creator_and_blocker_endpoints(tmp_path: Path) -> None:
    async with configured_client(tmp_path) as (client, csrf):
        project = await client.get("/api/v1/config/project")
        assert project.status_code == 200
        assert "# project comment" in project.json()["content"]

        creator = {"service": "fanbox", "creator_id": "42", "alias": "sample", "enabled": True}
        added = await client.post("/api/v1/creators", headers={CSRF_HEADER: csrf}, json=creator)
        assert added.status_code == 201
        duplicate = await client.post("/api/v1/creators", headers={CSRF_HEADER: csrf}, json=creator)
        assert duplicate.status_code == 422
        listed = await client.get("/api/v1/creators")
        assert listed.json() == [creator]

        updated = await client.put(
            "/api/v1/creators/fanbox/42",
            headers={CSRF_HEADER: csrf},
            json={"alias": "renamed", "enabled": False},
        )
        assert updated.json()["alias"] == "renamed"
        assert updated.json()["enabled"] is False

        blocker = {
            "id": "daily-sharing",
            "type": "field-match",
            "enabled": True,
            "scope": {"mode": "creators", "creators": ["fanbox:42"]},
            "options": {
                "rule": {
                    "kind": "group",
                    "mode": "any",
                    "conditions": [
                        {
                            "kind": "field",
                            "field": "title",
                            "operator": "contains",
                            "values": ["daily"],
                        }
                    ],
                }
            },
        }
        replaced = await client.put("/api/v1/blockers", headers={CSRF_HEADER: csrf}, json=[blocker])
        assert replaced.status_code == 200
        assert (await client.get("/api/v1/blockers")).json()["blockers"][0]["id"] == "daily-sharing"

        invalid = blocker | {"options": {"rule": {"kind": "group", "mode": "any", "conditions": []}}}
        assert (await client.put("/api/v1/blockers", headers={CSRF_HEADER: csrf}, json=[invalid])).status_code == 422

        deleted = await client.delete("/api/v1/creators/fanbox/42", headers={CSRF_HEADER: csrf})
        assert deleted.status_code == 200
        assert (await client.delete("/api/v1/creators/fanbox/42", headers={CSRF_HEADER: csrf})).status_code == 404


@pytest.mark.asyncio
async def test_raw_project_update_requires_current_revision_and_valid_toml(tmp_path: Path) -> None:
    async with configured_client(tmp_path) as (client, csrf):
        project = await client.get("/api/v1/config/project")
        etag = project.headers["etag"]
        content = project.json()["content"] + "\n# retained\n"
        updated = await client.put(
            "/api/v1/config/project",
            headers={CSRF_HEADER: csrf, "If-Match": etag},
            json={"content": content},
        )
        assert updated.status_code == 200
        assert "# retained" in updated.json()["content"]
        assert (
            await client.put(
                "/api/v1/config/project",
                headers={CSRF_HEADER: csrf, "If-Match": etag},
                json={"content": content},
            )
        ).status_code == 409

        current = await client.get("/api/v1/config/project")
        invalid = await client.put(
            "/api/v1/config/project",
            headers={CSRF_HEADER: csrf, "If-Match": current.headers["etag"]},
            json={"content": "not = [valid"},
        )
        assert invalid.status_code == 422

        valid = await client.post("/api/v1/config/project/validate", json={"content": current.json()["content"]})
        assert valid.json() == {"valid": True}
        invalid_validation = await client.post(
            "/api/v1/config/project/validate", json={"content": "not = [valid"}
        )
        assert invalid_validation.status_code == 422
