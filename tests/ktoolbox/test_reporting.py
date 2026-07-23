from __future__ import annotations

from io import StringIO
from pathlib import Path

from rich.console import Console

from ktoolbox.failures import FailureCode, FailureItem, FailureStage
from ktoolbox.reporting import (
    NullProgressReporter,
    PlainProgressReporter,
    ReporterDownloadObserver,
    RichProgressReporter,
    create_progress_reporter,
)


def failure_item(*, file_name: str | None = None) -> FailureItem:
    return FailureItem(
        code=FailureCode.download_failed,
        stage=FailureStage.file_request,
        message="The file request failed",
        retryable=True,
        file_name=file_name,
    )


def test_plain_reporter_emits_stable_summary_and_failures() -> None:
    output = StringIO()
    reporter = PlainProgressReporter(Console(file=output, color_system=None))
    reporter.start()
    reporter.creator_started("fanbox:1")
    reporter.creator_finished("fanbox:1", "API failed")
    for _ in range(4):
        reporter.job_queued("fanbox:1")
    reporter.download_finished("one", "completed")
    reporter.download_finished("two", "existed")
    reporter.download_finished("three", "failed", failure_item())
    reporter.download_finished("four", "failed")
    reporter.stop()

    rendered = output.getvalue()
    assert "Creator fanbox:1 failed: API failed" in rendered
    assert "1 downloaded, 1 existing, 2 failed" in rendered


def test_null_and_empty_plain_reporters_are_silent() -> None:
    null = NullProgressReporter()
    null.start()
    null.creator_started("fanbox:1")
    null.job_queued("fanbox:1")
    null.download_started("one", "fanbox:1", "one.bin", None, 0)
    null.download_advanced("one", 1)
    null.download_finished("one", "completed")
    null.creator_finished("fanbox:1")
    null.artifact_created(Path("artifact.bin"))
    null.stop()

    output = StringIO()
    plain = PlainProgressReporter(Console(file=output, color_system=None))
    plain.creator_finished("fanbox:1")
    plain.stop()
    assert output.getvalue() == ""


def test_rich_reporter_tracks_dynamic_tasks_and_log_output() -> None:
    output = StringIO()
    console = Console(file=output, force_terminal=True, color_system=None, width=72)
    reporter = RichProgressReporter(console)
    reporter.start()
    reporter.creator_started("fanbox:1")
    reporter.job_queued("fanbox:1")
    observer = ReporterDownloadObserver(reporter, "download-1", "fanbox:1")
    observer.start("a-very-long-filename-that-must-be-truncated-cleanly.bin", 10, 2)
    observer.advance(8)
    console.print("log line above progress")
    reporter.download_finished("download-1", "completed")
    reporter.creator_finished("fanbox:1")
    reporter.stop()

    rendered = output.getvalue()
    assert "log line above progress" in rendered
    assert "Files" in rendered
    assert reporter.overall.tasks[0].completed == 1


def test_rich_reporter_keeps_long_download_descriptions_on_one_line() -> None:
    output = StringIO()
    console = Console(file=output, force_terminal=True, color_system=None, width=72)
    reporter = RichProgressReporter(console)
    reporter.download_started(
        "download-1",
        "fanbox:1",
        "a-very-long-filename-that-must-be-truncated-cleanly.bin",
        10,
        2,
    )

    console.print(reporter.downloads)

    rendered_lines = [line for line in output.getvalue().splitlines() if line]
    assert len(rendered_lines) == 1
    assert "…" in rendered_lines[0]


def test_rich_reporter_sums_active_download_speeds() -> None:
    reporter = RichProgressReporter(Console(file=StringIO(), force_terminal=True, color_system=None))
    current_time = 0.0
    reporter.downloads.get_time = lambda: current_time
    reporter.download_started("download-1", "fanbox:1", "one.bin", 1_000, 0)
    reporter.download_started("download-2", "patreon:2", "two.bin", 2_000, 0)

    current_time = 1.0
    reporter.download_advanced("download-1", 100)
    reporter.download_advanced("download-2", 200)
    current_time = 2.0
    reporter.download_advanced("download-1", 100)
    reporter.download_advanced("download-2", 200)

    overall_task = reporter.overall.tasks[0]
    assert overall_task.fields["transfer_speed"] == "300 bytes/s"
    reporter.download_finished("download-1", "completed")
    assert overall_task.fields["transfer_speed"] == "200 bytes/s"
    reporter.download_finished("download-2", "completed")
    assert overall_task.fields["transfer_speed"] == "?"


def test_rich_reporter_handles_idempotence_failures_and_missing_tasks() -> None:
    output = StringIO()
    reporter = RichProgressReporter(Console(file=output, force_terminal=True, color_system=None))

    reporter.start()
    reporter.start()
    reporter.creator_started("fanbox:1")
    reporter.creator_started("fanbox:1")
    reporter.creator_finished("fanbox:1", "API failed")
    reporter.creator_finished("fanbox:missing")
    reporter.download_advanced("missing", 1)
    reporter.download_finished("missing-failed", "failed", failure_item(file_name="failed.bin"))
    reporter.download_finished("missing-failed-without-detail", "failed")
    reporter.download_finished("missing-existing", "existed")
    reporter.stop()
    reporter.stop()

    assert "Creator fanbox:1 failed: API failed" in output.getvalue()
    assert "Download failed (failed.bin):" in output.getvalue()
    assert reporter.overall.tasks[0].completed == 3


def test_reporter_factory_selects_quiet_plain_and_rich(monkeypatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    terminal = Console(file=StringIO(), force_terminal=True)
    redirected = Console(file=StringIO(), force_terminal=False)
    assert isinstance(create_progress_reporter(terminal, quiet=True), NullProgressReporter)
    assert isinstance(create_progress_reporter(terminal, plain=True), PlainProgressReporter)
    assert isinstance(create_progress_reporter(redirected), PlainProgressReporter)
    assert isinstance(create_progress_reporter(terminal), RichProgressReporter)
    monkeypatch.setenv("NO_COLOR", "1")
    assert isinstance(create_progress_reporter(terminal), PlainProgressReporter)
