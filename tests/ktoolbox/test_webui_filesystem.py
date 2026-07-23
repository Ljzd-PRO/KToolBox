from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest

from ktoolbox.configuration import Configuration, RuntimeContext
from ktoolbox.webui.app import create_app
from ktoolbox.webui.auth import CSRF_HEADER
from ktoolbox.webui.filesystem import FilesystemBrowser, path_breadcrumbs


@asynccontextmanager
async def filesystem_client(
    project_root: Path,
    host_root: Path,
) -> AsyncIterator[tuple[httpx.AsyncClient, str]]:
    home = host_root / "home"
    home.mkdir(exist_ok=True)
    browser = FilesystemBrowser(
        project_root,
        home=home,
        host_roots=(host_root,),
        restrict_host_to_roots=True,
    )
    configuration = Configuration(_env_file=None, webui={"username": "owner", "password": "secret"})
    app = create_app(RuntimeContext(project_root, configuration), filesystem_browser=browser)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 1234))
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            login = await client.post(
                "/api/v1/session/login",
                json={"username": "owner", "password": "secret"},
            )
            yield client, login.json()["csrf_token"]


@pytest.mark.asyncio
async def test_filesystem_browse_requires_session_and_lists_project_safely(tmp_path: Path) -> None:
    host = tmp_path / "host"
    project = host / "project"
    project.mkdir(parents=True)
    (project / "Zulu.txt").write_text("z", encoding="utf-8")
    (project / "alpha.txt").write_text("a", encoding="utf-8")
    (project / ".secret").write_text("hidden", encoding="utf-8")
    (project / "资料").mkdir()

    async with filesystem_client(project, host) as (client, _csrf):
        client.cookies.clear()
        assert (await client.get("/api/v1/filesystem")).status_code == 401
        login = await client.post(
            "/api/v1/session/login",
            json={"username": "owner", "password": "secret"},
        )
        assert login.status_code == 200

        response = await client.get("/api/v1/filesystem")
        assert response.status_code == 200
        data = response.json()
        assert data["path"] == str(project)
        assert data["project_relative_path"] == "."
        assert data["parent"] is None
        assert data["separator"] in {"/", "\\"}
        assert data["breadcrumbs"] == [{"label": "Project", "path": str(project)}]
        assert [entry["name"] for entry in data["entries"]] == ["资料", "alpha.txt", "Zulu.txt"]
        assert data["entries"][0]["kind"] == "directory"
        assert data["entries"][0]["navigable"] is True
        assert data["entries"][0]["deletable"] is True
        assert all(entry["deletable"] is False for entry in data["entries"] if entry["kind"] != "directory")
        assert all(entry["name"] != ".secret" for entry in data["entries"])

        hidden = await client.get("/api/v1/filesystem", params={"include_hidden": True})
        assert ".secret" in {entry["name"] for entry in hidden.json()["entries"]}


@pytest.mark.asyncio
async def test_filesystem_search_pagination_suggestions_and_host_locations(tmp_path: Path) -> None:
    host = tmp_path / "host"
    project = host / "project"
    project.mkdir(parents=True)
    for name in ("report-a.txt", "report-b.txt", "notes.txt"):
        (project / name).write_text(name, encoding="utf-8")

    async with filesystem_client(project, host) as (client, _csrf):
        page = await client.get(
            "/api/v1/filesystem",
            params={"search": "REPORT", "offset": 0, "limit": 1},
        )
        assert page.status_code == 200
        assert [entry["name"] for entry in page.json()["entries"]] == ["report-a.txt"]
        assert page.json()["has_more"] is True

        existing_file = await client.get(
            "/api/v1/filesystem",
            params={"mode": "file", "path": str(project / "report-a.txt")},
        )
        assert existing_file.json()["path"] == str(project)
        assert existing_file.json()["suggested_name"] == "report-a.txt"

        new_file = await client.get(
            "/api/v1/filesystem",
            params={"mode": "file", "path": str(project / "new report.txt")},
        )
        assert new_file.status_code == 200
        assert new_file.json()["suggested_name"] == "new report.txt"

        new_directory = await client.get(
            "/api/v1/filesystem",
            params={"mode": "directory", "path": str(project / "new folder")},
        )
        assert new_directory.json()["suggested_name"] == "new folder"

        host_view = await client.get("/api/v1/filesystem", params={"scope": "host", "path": str(host)})
        assert host_view.status_code == 200
        assert {location["id"] for location in host_view.json()["locations"]} == {
            "project",
            "home",
            "root-0",
        }
        assert (
            next(location["label"] for location in host_view.json()["locations"] if location["id"] == "root-0")
            == host.name
        )


@pytest.mark.asyncio
async def test_filesystem_create_directory_csrf_conflicts_and_validation(tmp_path: Path) -> None:
    host = tmp_path / "host"
    project = host / "project"
    project.mkdir(parents=True)

    async with filesystem_client(project, host) as (client, csrf):
        payload = {"scope": "project", "parent": str(project), "name": "新目录"}
        assert (await client.post("/api/v1/filesystem/directories", json=payload)).status_code == 403
        created = await client.post(
            "/api/v1/filesystem/directories",
            headers={CSRF_HEADER: csrf},
            json=payload,
        )
        assert created.status_code == 201
        assert created.json()["name"] == "新目录"
        assert created.json()["kind"] == "directory"
        assert created.json()["deletable"] is True
        assert (project / "新目录").is_dir()

        duplicate = await client.post(
            "/api/v1/filesystem/directories",
            headers={CSRF_HEADER: csrf},
            json=payload,
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["detail"]["code"] == "already_exists"

        invalid = await client.post(
            "/api/v1/filesystem/directories",
            headers={CSRF_HEADER: csrf},
            json={**payload, "name": "../escape"},
        )
        assert invalid.status_code == 422
        assert not (host / "escape").exists()
        events = await client._transport.app.state.event_store.events()  # type: ignore[attr-defined]
        filesystem_events = [event for event in events if event.event_type == "filesystem.changed"]
        assert len(filesystem_events) == 1
        assert filesystem_events[0].data["action"] == "created"


@pytest.mark.asyncio
async def test_filesystem_delete_directory_only_removes_empty_unprotected_folders(tmp_path: Path) -> None:
    host = tmp_path / "host"
    project = host / "project"
    empty = project / "empty"
    non_empty = project / "non-empty"
    empty.mkdir(parents=True)
    non_empty.mkdir()
    (non_empty / "keep.txt").write_text("keep", encoding="utf-8")

    async with filesystem_client(project, host) as (client, csrf):
        payload = {"scope": "project", "path": str(empty)}
        assert (await client.request("DELETE", "/api/v1/filesystem/directories", json=payload)).status_code == 403

        deleted = await client.request(
            "DELETE",
            "/api/v1/filesystem/directories",
            headers={CSRF_HEADER: csrf},
            json=payload,
        )
        assert deleted.status_code == 204
        assert not empty.exists()

        missing = await client.request(
            "DELETE",
            "/api/v1/filesystem/directories",
            headers={CSRF_HEADER: csrf},
            json=payload,
        )
        assert missing.status_code == 404
        assert missing.json()["detail"]["code"] == "directory_not_found"

        occupied = await client.request(
            "DELETE",
            "/api/v1/filesystem/directories",
            headers={CSRF_HEADER: csrf},
            json={"scope": "project", "path": str(non_empty)},
        )
        assert occupied.status_code == 409
        assert occupied.json()["detail"]["code"] == "directory_not_empty"
        assert non_empty.is_dir()
        assert (non_empty / "keep.txt").is_file()

        protected = await client.request(
            "DELETE",
            "/api/v1/filesystem/directories",
            headers={CSRF_HEADER: csrf},
            json={"scope": "project", "path": str(project)},
        )
        assert protected.status_code == 403
        assert protected.json()["detail"]["code"] == "protected_directory"
        events = await client._transport.app.state.event_store.events()  # type: ignore[attr-defined]
        filesystem_events = [event for event in events if event.event_type == "filesystem.changed"]
        assert len(filesystem_events) == 1
        assert filesystem_events[0].data["action"] == "deleted"


@pytest.mark.asyncio
async def test_project_scope_rejects_parent_and_symlink_escape(tmp_path: Path) -> None:
    host = tmp_path / "host"
    project = host / "project"
    outside = host / "outside"
    project.mkdir(parents=True)
    outside.mkdir()
    symlink = project / "outside-link"
    try:
        symlink.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")

    async with filesystem_client(project, host) as (client, _csrf):
        parent = await client.get("/api/v1/filesystem", params={"path": ".."})
        assert parent.status_code == 403
        escaped = await client.get("/api/v1/filesystem", params={"path": str(symlink)})
        assert escaped.status_code == 403
        listing = await client.get("/api/v1/filesystem")
        link_entry = next(entry for entry in listing.json()["entries"] if entry["name"] == "outside-link")
        assert link_entry["is_symlink"] is True
        assert link_entry["navigable"] is False
        assert link_entry["deletable"] is False
        assert link_entry["project_relative_path"] is None


@pytest.mark.asyncio
async def test_filesystem_missing_parent_and_wrong_mode_are_sanitized(tmp_path: Path) -> None:
    host = tmp_path / "host"
    project = host / "project"
    project.mkdir(parents=True)
    file_path = project / "item.txt"
    file_path.write_text("item", encoding="utf-8")

    async with filesystem_client(project, host) as (client, _csrf):
        missing = await client.get(
            "/api/v1/filesystem",
            params={"path": str(project / "missing" / "child")},
        )
        assert missing.status_code == 404
        assert missing.json()["detail"] == {
            "code": "parent_not_found",
            "message": "Parent directory was not found",
        }
        wrong_mode = await client.get(
            "/api/v1/filesystem",
            params={"path": str(file_path), "mode": "directory"},
        )
        assert wrong_mode.status_code == 422
        assert wrong_mode.json()["detail"] == {
            "code": "not_directory",
            "message": "Path is not a directory",
        }


def test_breadcrumb_helpers_cover_posix_windows_drives_and_unc() -> None:
    assert path_breadcrumbs("/srv/data/posts", separator="/") == [
        ("/", "/"),
        ("srv", "/srv"),
        ("data", "/srv/data"),
        ("posts", "/srv/data/posts"),
    ]
    assert path_breadcrumbs(r"C:\\Users\\Owner", separator="\\") == [
        ("C:", "C:\\"),
        ("Users", "C:\\Users"),
        ("Owner", "C:\\Users\\Owner"),
    ]
    assert path_breadcrumbs(r"\\server\share\folder", separator="\\") == [
        (r"\\server\share", "\\\\server\\share\\"),
        ("folder", "\\\\server\\share\\folder"),
    ]
