from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Callable
from pathlib import Path

from ktoolbox.configuration import RuntimeContext
from ktoolbox.webui.event_store import WebUIEventStore

_DOCUMENTS = {
    "dotenv": ".env",
    "production": "prod.env",
    "project": "ktoolbox.toml",
}


class ConfigurationChangeMonitor:
    """Watch project configuration files for edits made outside the WebUI."""

    def __init__(
        self,
        project_root: Path,
        events: WebUIEventStore,
        update_context: Callable[[RuntimeContext], None],
        *,
        interval: float = 2.0,
    ) -> None:
        self.project_root = project_root
        self.events = events
        self.update_context = update_context
        self.interval = interval
        self._revisions: dict[str, str] = {}
        self._task: asyncio.Task[None] | None = None
        self._stopping = asyncio.Event()

    async def start(self) -> None:
        if self._task is not None:
            return
        self._revisions = {name: _file_revision(self.project_root / filename) for name, filename in _DOCUMENTS.items()}
        self._stopping.clear()
        self._task = asyncio.create_task(self._run(), name="ktoolbox-webui-config-monitor")

    async def stop(self) -> None:
        task = self._task
        if task is None:
            return
        self._stopping.set()
        await task
        self._task = None

    def acknowledge(self, name: str, revision: str) -> None:
        if name not in _DOCUMENTS:
            raise ValueError(f"unknown configuration document: {name}")
        self._revisions[name] = revision

    async def publish_change(
        self,
        name: str,
        revision: str,
        *,
        source: str,
        event_type: str = "configuration.changed",
    ) -> None:
        self.acknowledge(name, revision)
        await self.events.publish(
            event_type,
            {"name": name, "revision": revision, "source": source},
            resource="configuration",
            resource_id=name,
        )

    async def check_once(self) -> None:
        for name, filename in _DOCUMENTS.items():
            revision = _file_revision(self.project_root / filename)
            if self._revisions.get(name) == revision:
                continue
            self._revisions[name] = revision
            valid = True
            if name != "project":
                try:
                    self.update_context(RuntimeContext.from_project(self.project_root))
                except (OSError, ValueError):
                    valid = False
            await self.events.publish(
                "configuration.changed",
                {
                    "name": name,
                    "revision": revision,
                    "source": "external",
                    "valid": valid,
                },
                resource="configuration",
                resource_id=name,
            )

    async def _run(self) -> None:
        while not self._stopping.is_set():
            try:
                await asyncio.wait_for(self._stopping.wait(), timeout=self.interval)
            except TimeoutError:
                await self.check_once()


def _file_revision(path: Path) -> str:
    try:
        content = path.read_bytes() if path.exists() else b""
    except OSError:
        content = b""
    return hashlib.sha256(content).hexdigest()
