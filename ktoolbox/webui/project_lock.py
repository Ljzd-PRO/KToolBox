from __future__ import annotations

from functools import partial
from pathlib import Path

import anyio
from filelock import AsyncFileLock, Timeout


class ProjectAlreadyRunningError(RuntimeError):
    pass


class ProjectProcessLock:
    """Prevent two WebUI schedulers from mutating one project database."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = AsyncFileLock(path, fallback_to_soft=False)

    async def acquire(self) -> None:
        await anyio.to_thread.run_sync(partial(self._path.parent.mkdir, parents=True, exist_ok=True))
        try:
            await self._lock.acquire(timeout=0)
        except Timeout as error:
            raise ProjectAlreadyRunningError("another KToolBox WebUI process is already using this project") from error

    async def release(self) -> None:
        if self._lock.is_locked:
            await self._lock.release()
