from __future__ import annotations

import io
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

import ktoolbox.progress as progress_module
from ktoolbox.progress import (
    ColorTheme,
    ManagedTqdm,
    ProgressAwareHandler,
    ProgressManager,
    ProgressState,
    create_managed_tqdm_class,
    setup_logger_for_progress,
)


class TerminalBuffer(io.StringIO):
    def __init__(self, terminal: bool = True) -> None:
        super().__init__()
        self.terminal = terminal

    def isatty(self) -> bool:
        return self.terminal


def manager(*, colors: bool = False, emojis: bool = False, workers: int = 3) -> ProgressManager:
    return ProgressManager(
        max_workers=workers,
        file=TerminalBuffer(),
        use_colors=colors,
        use_emojis=emojis,
        update_interval=0,
    )


def test_progress_aware_handler_integrates_with_active_display() -> None:
    sink = TerminalBuffer()
    active = SimpleNamespace(
        _running=True,
        temporary_clear_for_log=Mock(),
        restore_display=Mock(),
    )
    setup_logger_for_progress(active)
    with patch("ktoolbox.progress.time.sleep") as sleep:
        handler = ProgressAwareHandler(sink)
        handler.write("message")
        handler.flush()
    assert sink.getvalue() == "message"
    active.temporary_clear_for_log.assert_called_once_with()
    active.restore_display.assert_called_once_with()
    sleep.assert_called_once_with(0.05)

    setup_logger_for_progress(None)
    handler.write(" plain")
    assert sink.getvalue().endswith(" plain")
    no_flush = SimpleNamespace(write=Mock())
    ProgressAwareHandler(no_flush).flush()


def test_color_support_and_colorization_branches(monkeypatch) -> None:
    with patch.object(ColorTheme, "supports_color", return_value=False):
        assert ColorTheme.colorize("text", "red") == "text"
    with patch.object(ColorTheme, "supports_color", return_value=True):
        assert ColorTheme.colorize("text", "red").endswith(ColorTheme.RESET)
        assert ColorTheme.colorize("text", ColorTheme.BLUE, bold=True).startswith(ColorTheme.BOLD)
        assert ColorTheme.colorize("text", "unknown") == "text"

    monkeypatch.setattr(progress_module, "RICH_AVAILABLE", True)
    monkeypatch.setattr(
        ColorTheme,
        "_console",
        SimpleNamespace(is_terminal=True, options=SimpleNamespace(legacy_windows=False)),
    )
    assert ColorTheme.supports_color() is True
    ColorTheme._console.options.legacy_windows = True
    assert ColorTheme.supports_color() is False

    monkeypatch.setattr(progress_module, "RICH_AVAILABLE", False)
    stdout = SimpleNamespace(isatty=lambda: True)
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "platform", "darwin")
    assert ColorTheme.supports_color() is True
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delenv("ANSICON", raising=False)
    assert ColorTheme.supports_color() is False
    monkeypatch.setenv("ANSICON", "1")
    assert ColorTheme.supports_color() is True


def test_manager_state_updates_rate_and_sync_finish() -> None:
    progress = manager()
    progress.set_job_totals(10, completed=2, failed=1, existed=3)
    progress.update_job_progress(completed=4, failed=2, existed=5)
    assert progress.increment_existed(2) == 7

    bar = progress.create_progress_bar("file", total=100, unit="B", unit_scale=True)
    progress_id = bar.progress_id
    assert progress_id in progress._progress_bars
    progress.update_progress("missing", 1)
    with patch("ktoolbox.progress.time.time", side_effect=[10.0, 12.0]):
        progress.update_progress(progress_id, 10, desc="renamed")
        progress.update_progress(progress_id, 30, failed=True)
    state = progress._progress_bars[progress_id]
    assert state.desc == "renamed"
    assert state.current == 30
    assert state.failed is True
    assert state.rate == 10

    progress.finish_progress("missing")
    progress.finish_progress(progress_id, failed=True)
    assert progress_id not in progress._progress_bars
    assert progress_id not in progress._display_order


@pytest.mark.asyncio
async def test_async_finished_bar_removal() -> None:
    progress = manager()
    bar = ManagedTqdm(desc="async", total=1, manager=progress)
    created: list[object] = []

    class Loop:
        def create_task(self, coroutine: object) -> None:
            created.append(coroutine)
            coroutine.close()

    with patch("ktoolbox.progress.asyncio.get_running_loop", return_value=Loop()):
        progress.finish_progress(bar.progress_id)
    assert created
    assert bar.progress_id in progress._progress_bars
    await progress._remove_finished_after_delay(bar.progress_id, delay=0)
    assert bar.progress_id not in progress._progress_bars


def test_terminal_display_lifecycle_clear_restore_and_deduplication() -> None:
    output = TerminalBuffer()
    progress = ProgressManager(file=output, use_colors=False, use_emojis=False, update_interval=0)
    progress.start_display()
    assert progress._running
    assert "\033[?25l" in output.getvalue()

    progress.set_job_totals(2)
    bar = ManagedTqdm(desc="file", total=10, initial=1, manager=progress)
    with patch("ktoolbox.progress.time.time", side_effect=[10.0, 11.0, 12.0, 13.0]):
        progress.update_display()
        first = output.getvalue()
        progress.update_display()
        assert output.getvalue() == first
        bar.update(1)
    assert "Jobs:" in output.getvalue()
    assert progress._lines_written > 0

    progress.temporary_clear_for_log("log line")
    assert "log line" in output.getvalue()
    with patch.object(progress, "update_display") as update:
        progress.restore_display()
    update.assert_called_once_with()
    progress.stop_display()
    assert not progress._running
    assert "\033[?25h" in output.getvalue()

    non_terminal = ProgressManager(file=TerminalBuffer(False))
    non_terminal.start_display()
    non_terminal.update_display()
    non_terminal.stop_display()
    assert not non_terminal._running


def test_size_rate_and_overall_rendering_variants() -> None:
    progress = manager(emojis=True)
    assert progress._format_size(None) == "?"
    assert progress._format_size(12, unit_scale=False) == "12"
    assert progress._format_size(12) == "12B"
    assert progress._format_size(1024) == "1.0KB"
    assert progress._format_size(1024**5) == "1024.0TB"
    assert progress._format_rate(None) == "?/s"
    assert progress._format_rate(2048) == "2.0KB/s"
    assert progress._render_overall_progress() == []

    state = ProgressState(desc="active", total=100, current=25, rate=2048)
    progress._progress_bars["active"] = state
    progress.set_job_totals(4, completed=0)
    assert "running" in progress._render_overall_progress()[0]

    state.finished = True
    progress.set_job_totals(4, completed=2, failed=1, existed=1)
    lines = progress._render_overall_progress()
    assert "50%" in lines[0]
    assert "Failed:" in lines[1]

    progress.use_emojis = False
    progress.set_job_totals(4, completed=3)
    assert "75%" in progress._render_overall_progress()[0]
    progress.set_job_totals(4, completed=4)
    assert "100%" in progress._render_overall_progress()[0]


def test_colored_overall_rendering_thresholds() -> None:
    progress = manager()
    progress.use_colors = True
    progress.use_emojis = True
    with patch.object(ColorTheme, "supports_color", return_value=True):
        for completed in (0, 2, 3, 4):
            progress.set_job_totals(4, completed=completed, failed=1 if completed == 2 else 0)
            lines = progress._render_overall_progress()
            assert lines

        progress._progress_bars["active"] = ProgressState(total=10, rate=100)
        assert "/s" in progress._render_overall_progress()[0]


def test_single_bar_rendering_without_colors_and_order_limit() -> None:
    progress = manager(emojis=True, workers=2)
    states = [
        ProgressState(desc="active", total=100, current=50, rate=10),
        ProgressState(desc="failed", total=100, current=150, failed=True),
        ProgressState(desc="finished", total=100, current=100, finished=True),
        ProgressState(desc="paused", total=None, current=0, paused=True),
        ProgressState(desc="description that is much too long", total=0, current=0),
    ]
    for index, state in enumerate(states):
        rendered = progress._render_single_progress_bar(state)
        assert "|" in rendered
        progress._progress_bars[str(index)] = state
        progress._display_order.append(str(index))
    progress._display_order.append("missing")
    lines = progress._render_progress_bars()
    assert len(lines) == 2
    assert "active" in lines[0]
    assert "failed" in lines[1]


@pytest.mark.parametrize("rich_available", [True, False])
def test_colored_single_bar_rendering_all_states(monkeypatch, rich_available: bool) -> None:
    progress = manager()
    progress.use_colors = True
    progress.use_emojis = True
    monkeypatch.setattr(progress_module, "RICH_AVAILABLE", rich_available)
    with patch.object(ColorTheme, "supports_color", return_value=True):
        for state in (
            ProgressState(desc="failed-empty", total=100, current=0, failed=True),
            ProgressState(desc="failed-part", total=100, current=50, failed=True),
            ProgressState(desc="failed-full", total=100, current=100, failed=True),
            ProgressState(desc="finished", total=100, current=100, finished=True),
            ProgressState(desc="active-empty", total=100, current=0),
            ProgressState(desc="active-part", total=100, current=80, rate=20),
            ProgressState(desc="active-full", total=100, current=100),
            ProgressState(desc="unknown", total=None, current=1),
        ):
            assert state.desc in progress._render_single_progress_bar(state)


def test_update_display_rate_limit_empty_and_trailing_lines() -> None:
    output = TerminalBuffer()
    progress = ProgressManager(file=output, use_colors=False, use_emojis=False, update_interval=10)
    progress._running = True
    progress._last_display_time = 100
    with patch("ktoolbox.progress.time.time", return_value=105):
        progress.update_display()
    assert output.getvalue() == ""

    progress._update_interval = 0
    with (
        patch.object(progress, "_render_overall_progress", return_value=["line", ""]),
        patch.object(progress, "_render_progress_bars", return_value=[]),
        patch("ktoolbox.progress.time.time", side_effect=[110, 111]),
    ):
        progress.update_display()
        progress.update_display()
    assert output.getvalue().count("line") == 1


class FakeFallback:
    def __init__(self) -> None:
        self.total = 10
        self.n = 1
        self.update = Mock(return_value="updated")
        self.set_description = Mock(return_value="described")
        self.close = Mock(return_value="closed")
        self.__enter__ = Mock(return_value="entered")
        self.__exit__ = Mock(return_value="exited")


def test_managed_tqdm_fallback_interface() -> None:
    fallback = FakeFallback()
    with patch("ktoolbox.progress.std_tqdm", return_value=fallback):
        bar = ManagedTqdm(desc="fallback", total=10, manager=None)
    assert bar.update(2) == "updated"
    assert bar.set_description("new") == "described"
    assert bar.close() == "closed"
    assert bar.__enter__() == "entered"
    assert bar.__exit__(None, None, None) == "exited"
    assert bar.set_failed() is None
    assert bar.set_paused() is None
    assert bar.total == 10
    bar.total = 20
    assert fallback.total == 20
    assert bar.n == 1
    bar.n = 3
    assert fallback.n == 3
    assert bar


def test_managed_tqdm_manager_interface_and_factory() -> None:
    progress = manager()
    bar = ManagedTqdm(desc="managed", total=10, initial=1, manager=progress)
    assert bar.total == 10
    bar.total = 20
    assert bar.total == 20
    assert bar.n == 1
    bar.n = 4
    assert bar.n == 4
    bar.update(2)
    bar.set_description("renamed")
    bar.set_failed()
    bar.set_paused()
    assert progress._progress_bars[bar.progress_id].paused is True
    bar.set_paused(False)
    with bar as entered:
        assert entered is bar
    assert bar.progress_id not in progress._progress_bars

    managed_class = create_managed_tqdm_class(progress)
    generated = managed_class(desc="factory", total=1)
    assert generated.manager is progress
    generated.close()


def test_managed_tqdm_destructor_suppresses_close_errors() -> None:
    bar = object.__new__(ManagedTqdm)
    bar.close = Mock(side_effect=RuntimeError("close failed"))
    bar.__del__()
