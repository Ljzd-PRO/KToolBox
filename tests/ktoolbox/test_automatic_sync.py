from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ktoolbox.api.generated import Post
from ktoolbox.automatic_sync import AutomaticSyncWindow, automatic_post_timestamp


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
