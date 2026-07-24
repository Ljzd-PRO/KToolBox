from __future__ import annotations

import asyncio
import getpass
import secrets
import signal
import socket
import sys
import threading
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from types import FrameType

import anyio
from argon2 import PasswordHasher
from pydantic import SecretStr

from ktoolbox.configuration import RuntimeContext, WebUIConfiguration, load_configuration
from ktoolbox.exceptions import KToolBoxUserError
from ktoolbox.project_config import ProjectConfigStore, ProjectConfiguration

DEFAULT_WEBUI_USERNAME = "admin"


@dataclass(frozen=True, slots=True)
class GeneratedWebUICredentials:
    username: str
    password: str | None


def generate_password_hash() -> str:
    try:
        password = getpass.getpass("WebUI password: ")
        confirmation = getpass.getpass("Confirm password: ")
    except EOFError as error:
        raise KToolBoxUserError("password input was cancelled", label="Password error") from error
    if not password:
        raise KToolBoxUserError("password cannot be empty", label="Password error")
    if password != confirmation:
        raise KToolBoxUserError("passwords do not match", label="Password error")
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
        raise KToolBoxUserError(
            "install the WebUI dependencies with `pip install ktoolbox[webui]`",
            label="WebUI error",
        ) from error

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

    from ktoolbox.webui.app import create_app

    application = create_app(context)
    application.state.auth.validate_configuration()
    local_host = "127.0.0.1" if webui.host in {"0.0.0.0", "::"} else webui.host
    url = f"http://{local_host}:{webui.port}"
    if generated_credentials is not None:
        _print_generated_credentials(generated_credentials)
    print(f"KToolBox WebUI: {url}")
    print("Security warning: HTTP traffic is unencrypted. Use only on a trusted network.")
    if webui.open_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()

    class WebUIServer(uvicorn.Server):
        interrupt_count = 0
        _serve_task: asyncio.Task[None] | None = None

        async def serve(self, sockets: list[socket.socket] | None = None) -> None:
            self._serve_task = asyncio.current_task()
            try:
                if sockets is None:
                    await super().serve()
                else:
                    await super().serve(sockets=sockets)
            except asyncio.CancelledError:
                if self.interrupt_count < 2:
                    raise
                task = asyncio.current_task()
                uncancel = getattr(task, "uncancel", None)
                if callable(uncancel):
                    uncancel()
            finally:
                self._serve_task = None

        def handle_exit(self, sig: int, frame: FrameType | None) -> None:
            if sig != signal.SIGINT:
                super().handle_exit(sig, frame)
                return
            self.interrupt_count += 1
            if self.should_exit:
                self.force_exit = True
                if self._serve_task is not None and not self._serve_task.done():
                    self._serve_task.cancel()
            else:
                self.should_exit = True

    server = WebUIServer(
        uvicorn.Config(
            application,
            host=webui.host,
            port=webui.port,
            access_log=False,
        )
    )
    await server.serve()
    if server.interrupt_count > 1:
        lifespan = getattr(server, "lifespan", None)
        if lifespan is not None:
            try:
                await asyncio.wait_for(lifespan.shutdown(), timeout=0.5)
            except (TimeoutError, asyncio.CancelledError):
                lifespan.logger.disabled = True
        raise KeyboardInterrupt


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
        raise KToolBoxUserError(
            f"{project_config} is not a regular file",
            label="Configuration error",
        )

    ProjectConfigStore(project_config).save(ProjectConfiguration())
    print(
        f"Warning: {project_config} was not found; created a new project configuration.",
        file=sys.stderr,
    )
    return root
