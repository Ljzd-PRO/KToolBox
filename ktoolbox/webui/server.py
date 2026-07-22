from __future__ import annotations

import getpass
import secrets
import sys
import threading
import webbrowser
from dataclasses import dataclass
from pathlib import Path

import anyio
from argon2 import PasswordHasher
from pydantic import SecretStr

from ktoolbox.configuration import RuntimeContext, WebUIConfiguration, load_configuration
from ktoolbox.project_config import ProjectConfigStore, ProjectConfiguration

DEFAULT_WEBUI_USERNAME = "admin"


@dataclass(frozen=True, slots=True)
class GeneratedWebUICredentials:
    username: str
    password: str | None


def generate_password_hash() -> str:
    password = getpass.getpass("WebUI password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if not password:
        raise ValueError("password cannot be empty")
    if password != confirmation:
        raise ValueError("passwords do not match")
    return PasswordHasher().hash(password)


async def run_webui(
    project_dir: Path,
    *,
    host: str | None = None,
    port: int | None = None,
    open_browser: bool | None = None,
) -> None:
    try:
        import uvicorn
    except ModuleNotFoundError as error:
        raise RuntimeError("install the WebUI dependencies with `pip install ktoolbox[webui]`") from error

    root = await anyio.to_thread.run_sync(_project_root, project_dir)
    configuration = await anyio.to_thread.run_sync(load_configuration, root)
    updates: dict[str, object] = {}
    if host is not None:
        updates["host"] = host
    if port is not None:
        updates["port"] = port
    if open_browser is not None:
        updates["open_browser"] = open_browser
    webui = WebUIConfiguration.model_validate(
        {**configuration.webui.model_dump(), **updates},
    )
    webui, generated_credentials = _prepare_webui_credentials(webui)
    configuration = configuration.model_copy(update={"webui": webui})
    context = RuntimeContext(project_root=root, configuration=configuration)

    local_host = "127.0.0.1" if webui.host in {"0.0.0.0", "::"} else webui.host
    url = f"http://{local_host}:{webui.port}"
    if generated_credentials is not None:
        _print_generated_credentials(generated_credentials)
    print(f"KToolBox WebUI: {url}")
    print("Security warning: HTTP traffic is unencrypted. Use only on a trusted network.")
    if webui.open_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()

    from ktoolbox.webui.app import create_app

    server = uvicorn.Server(
        uvicorn.Config(
            create_app(context),
            host=webui.host,
            port=webui.port,
            access_log=False,
        )
    )
    await server.serve()


def _prepare_webui_credentials(
    configuration: WebUIConfiguration,
) -> tuple[WebUIConfiguration, GeneratedWebUICredentials | None]:
    updates: dict[str, object] = {}
    username_was_defaulted = not configuration.username.strip()
    if username_was_defaulted:
        updates["username"] = DEFAULT_WEBUI_USERNAME

    password_hash = configuration.password_hash.get_secret_value()
    plaintext_password = configuration.password.get_secret_value()
    generated_password: str | None = None
    if not password_hash and not plaintext_password:
        generated_password = secrets.token_urlsafe(24)
        updates["password"] = SecretStr(generated_password)

    if not updates:
        return configuration, None

    resolved = configuration.model_copy(update=updates)
    return resolved, GeneratedWebUICredentials(
        username=resolved.username,
        password=generated_password,
    )


def _print_generated_credentials(credentials: GeneratedWebUICredentials) -> None:
    if credentials.password is not None:
        print("Generated WebUI credentials for this run:")
        print(f"  Username: {credentials.username}")
        print(f"  Password: {credentials.password}")
    else:
        print(f"WebUI username defaulted to {credentials.username!r} for this run.")
    print(
        "Configure KTOOLBOX_WEBUI__USERNAME and KTOOLBOX_WEBUI__PASSWORD_HASH "
        "(preferred) or KTOOLBOX_WEBUI__PASSWORD to customize the account."
    )


def _project_root(project_dir: Path) -> Path:
    root = project_dir.expanduser().resolve()
    project_config = root / "ktoolbox.toml"
    if project_config.is_file():
        return root
    if project_config.exists():
        raise ValueError(f"{project_config} is not a regular file")

    ProjectConfigStore(project_config).save(ProjectConfiguration())
    print(
        f"Warning: {project_config} was not found; created a new project configuration.",
        file=sys.stderr,
    )
    return root
