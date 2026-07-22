from pathlib import Path

import pytest
import uvicorn
from pydantic import SecretStr

import ktoolbox.webui.server as server_module
from ktoolbox.configuration import Configuration, WebUIConfiguration
from ktoolbox.project_config import ProjectConfigStore, ProjectConfiguration
from ktoolbox.webui.server import DEFAULT_WEBUI_USERNAME, _prepare_webui_credentials, _project_root, run_webui


def test_prepare_webui_credentials_fills_only_missing_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(server_module.secrets, "token_urlsafe", lambda length: f"random-{length}")

    resolved, generated = _prepare_webui_credentials(WebUIConfiguration())

    assert resolved.username == DEFAULT_WEBUI_USERNAME
    assert resolved.password == SecretStr("random-24")
    assert generated is not None
    assert generated.username == DEFAULT_WEBUI_USERNAME
    assert generated.password == "random-24"

    configured = WebUIConfiguration(username="owner", password=SecretStr("configured"))
    assert _prepare_webui_credentials(configured) == (configured, None)

    default_username, generated = _prepare_webui_credentials(
        WebUIConfiguration(password=SecretStr("configured")),
    )
    assert default_username.username == DEFAULT_WEBUI_USERNAME
    assert default_username.password == SecretStr("configured")
    assert generated is not None
    assert generated.password is None


@pytest.mark.asyncio
async def test_run_webui_prints_generated_credentials_and_configuration_hint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, object] = {}

    class FakeConfig:
        def __init__(self, app, **kwargs) -> None:
            self.app = app
            self.kwargs = kwargs

    class FakeServer:
        def __init__(self, configuration: FakeConfig) -> None:
            captured["configuration"] = configuration

        async def serve(self) -> None:
            captured["served"] = True

    monkeypatch.setattr(server_module.secrets, "token_urlsafe", lambda length: "generated-password")
    monkeypatch.setattr(server_module, "load_configuration", lambda root: Configuration(_env_file=None))
    monkeypatch.setattr(uvicorn, "Config", FakeConfig)
    monkeypatch.setattr(uvicorn, "Server", FakeServer)

    await run_webui(tmp_path, host="127.0.0.1", port=9876, open_browser=False)

    assert captured["served"] is True
    uvicorn_configuration = captured["configuration"]
    assert isinstance(uvicorn_configuration, FakeConfig)
    auth_configuration = uvicorn_configuration.app.state.auth.configuration
    assert auth_configuration.username == DEFAULT_WEBUI_USERNAME
    assert auth_configuration.password == SecretStr("generated-password")
    output = capsys.readouterr().out
    assert "Generated WebUI credentials for this run:" in output
    assert "Username: admin" in output
    assert "Password: generated-password" in output
    assert "KTOOLBOX_WEBUI__USERNAME" in output
    assert "KTOOLBOX_WEBUI__PASSWORD_HASH" in output
    assert "KTOOLBOX_WEBUI__PASSWORD" in output
    assert "KToolBox WebUI: http://127.0.0.1:9876" in output


def test_project_root_creates_missing_configuration(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project_root = tmp_path / "new-project"

    assert _project_root(project_root) == project_root.resolve()

    project_config = project_root / "ktoolbox.toml"
    assert project_config.read_text(encoding="utf-8") == "schema_version = 1\n"
    assert ProjectConfigStore(project_config).load() == ProjectConfiguration()
    assert capsys.readouterr().err == f"Warning: {project_config} was not found; created a new project configuration.\n"


def test_project_root_preserves_existing_configuration(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project_config = tmp_path / "ktoolbox.toml"
    original = "# Keep this comment.\nschema_version = 1\n"
    project_config.write_text(original, encoding="utf-8")

    assert _project_root(tmp_path) == tmp_path.resolve()
    assert project_config.read_text(encoding="utf-8") == original
    assert capsys.readouterr().err == ""


def test_project_root_rejects_non_file_configuration(tmp_path: Path) -> None:
    (tmp_path / "ktoolbox.toml").mkdir()

    with pytest.raises(ValueError, match="is not a regular file"):
        _project_root(tmp_path)
