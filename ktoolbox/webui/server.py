from __future__ import annotations

import getpass
import sys
import threading
import webbrowser
from pathlib import Path

import anyio
from argon2 import PasswordHasher

from ktoolbox.configuration import RuntimeContext, WebUIConfiguration, load_configuration
from ktoolbox.project_config import ProjectConfigStore, ProjectConfiguration


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
    configuration = configuration.model_copy(update={"webui": webui})
    context = RuntimeContext(project_root=root, configuration=configuration)

    local_host = "127.0.0.1" if webui.host in {"0.0.0.0", "::"} else webui.host
    url = f"http://{local_host}:{webui.port}"
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
