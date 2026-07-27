from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ktoolbox.api.generated import Post
from ktoolbox.automatic_sync import AutomaticSyncWindow, automatic_post_timestamp, next_automatic_sync_time
from ktoolbox.project_config import CronAutomaticSyncSchedule, IntervalAutomaticSyncSchedule


def work(
    *,
    added: datetime | None = None,
    published: datetime | None = None,
) -> Post:
    return Post(
        id="work",
        user="creator",
        service="fanbox",
        added=added,
        published=published,
    )


def test_automatic_timestamp_treats_added_as_utc_and_prefers_it() -> None:
    item = work(
        added=datetime(2026, 7, 20, 2, 30),
        published=datetime(2026, 7, 20, 11, 30),
    )

    assert automatic_post_timestamp(item, "Asia/Tokyo") == datetime(2026, 7, 20, 2, 30, tzinfo=UTC)


def test_automatic_timestamp_uses_plan_timezone_for_naive_published_fallback() -> None:
    item = work(published=datetime(2026, 7, 20, 11, 30))

    assert automatic_post_timestamp(item, "Asia/Tokyo") == datetime(2026, 7, 20, 2, 30, tzinfo=UTC)


def test_automatic_window_supports_open_start_and_inclusive_boundaries() -> None:
    end = datetime(2026, 7, 20, 3, tzinfo=UTC)
    window = AutomaticSyncWindow(
        start_at=datetime(2026, 7, 20, 2, tzinfo=UTC),
        end_at=end,
        fallback_timezone="Asia/Tokyo",
    )

    assert window.includes(work(added=datetime(2026, 7, 20, 2)))
    assert window.includes(work(added=datetime(2026, 7, 20, 3)))
    assert not window.includes(work(added=datetime(2026, 7, 20, 1, 59, 59)))
    assert not window.includes(work(added=datetime(2026, 7, 20, 3, 0, 1)))
    assert AutomaticSyncWindow(None, end, "UTC").includes(work(added=datetime(2000, 1, 1)))
    assert not window.includes(work())


def test_automatic_window_rejects_invalid_ranges_and_naive_boundaries() -> None:
    aware = datetime(2026, 7, 20, tzinfo=UTC)
    with pytest.raises(ValueError, match="start must include"):
        AutomaticSyncWindow(datetime(2026, 7, 19), aware, "UTC")
    with pytest.raises(ValueError, match="end must include"):
        AutomaticSyncWindow(None, datetime(2026, 7, 20), "UTC")
    with pytest.raises(ValueError, match="later"):
        AutomaticSyncWindow(aware, datetime(2026, 7, 19, tzinfo=UTC), "UTC")


def test_next_interval_time_preserves_anchor_and_is_strictly_future() -> None:
    schedule = IntervalAutomaticSyncSchedule(
        every=6,
        unit="hours",
        anchor_at=datetime(2026, 7, 1, tzinfo=UTC),
    )

    assert next_automatic_sync_time(schedule, datetime(2026, 7, 1, tzinfo=UTC)) == datetime(2026, 7, 1, 6, tzinfo=UTC)
    assert next_automatic_sync_time(schedule, datetime(2026, 7, 1, 7, tzinfo=UTC)) == datetime(
        2026, 7, 1, 12, tzinfo=UTC
    )


def test_next_cron_time_handles_dst_gaps_and_uses_first_repeated_time() -> None:
    spring = CronAutomaticSyncSchedule(expression="30 2 * * *", timezone="America/New_York")
    assert next_automatic_sync_time(spring, datetime(2026, 3, 7, 8, tzinfo=UTC)) == datetime(2026, 3, 8, 7, tzinfo=UTC)

    autumn = CronAutomaticSyncSchedule(expression="30 1 * * *", timezone="America/New_York")
    assert next_automatic_sync_time(autumn, datetime(2026, 11, 1, 4, tzinfo=UTC)) == datetime(
        2026, 11, 1, 5, 30, tzinfo=UTC
    )
    assert next_automatic_sync_time(autumn, datetime(2026, 11, 1, 5, 31, tzinfo=UTC)) == datetime(
        2026, 11, 2, 6, 30, tzinfo=UTC
    )
