from __future__ import annotations

import signal
import subprocess
from typing import Any

import pytest

from scripts import smoke_test_executable


class ProcessStub:
    def __init__(self, *, timeout_once: bool = False) -> None:
        self.pid = 1234
        self.timeout_once = timeout_once
        self.communicate_calls = 0
        self.signals: list[int] = []

    def poll(self) -> None:
        return None

    def communicate(self, timeout: float | None = None) -> tuple[str, None]:
        self.communicate_calls += 1
        if self.timeout_once and self.communicate_calls == 1:
            raise subprocess.TimeoutExpired("ktoolbox", timeout)
        return "", None

    def send_signal(self, value: int) -> None:
        self.signals.append(value)


def test_stop_process_tree_gracefully_stops_posix_group(monkeypatch: pytest.MonkeyPatch) -> None:
    process = ProcessStub()
    signals: list[tuple[int, signal.Signals]] = []
    monkeypatch.setattr(smoke_test_executable.os, "killpg", lambda pid, value: signals.append((pid, value)))

    smoke_test_executable._stop_process_tree(process, windows=False)  # type: ignore[arg-type]

    assert signals == [(1234, signal.SIGTERM)]
    assert process.communicate_calls == 1


def test_stop_process_tree_forces_windows_children_after_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    process = ProcessStub(timeout_once=True)
    taskkill_calls: list[tuple[list[str], dict[str, Any]]] = []
    monkeypatch.setattr(signal, "CTRL_BREAK_EVENT", 1, raising=False)
    monkeypatch.setattr(
        smoke_test_executable.subprocess,
        "run",
        lambda command, **kwargs: taskkill_calls.append((command, kwargs)),
    )

    smoke_test_executable._stop_process_tree(process, windows=True)  # type: ignore[arg-type]

    assert process.signals == [1]
    assert taskkill_calls[0][0] == ["taskkill", "/PID", "1234", "/T", "/F"]
    assert taskkill_calls[0][1]["timeout"] == 20
    assert process.communicate_calls == 2
