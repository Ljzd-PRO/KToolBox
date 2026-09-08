from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ktoolbox.api.generated import Post
from ktoolbox.publication_time import (
    PublishedTimeError,
    PublishedTimePolicy,
    automatic_post_timestamp,
    effective_post_timestamp,
    effective_published,
    localize_wall_time,
    published_service_timezone,
)


def post(service: str, published: datetime | None = None, added: datetime | None = None) -> Post:
    return Post(id="work", user="creator", service=service, published=published, added=added)


def test_fanbox_naive_publication_crosses_utc_date_boundary() -> None:
    policy = PublishedTimePolicy()
    value = effective_published(post("fanbox", datetime(2025, 12, 21, 0, 35, 43)), policy)

    assert value == datetime(2025, 12, 20, 15, 35, 43, tzinfo=timezone.utc)


def test_aware_publication_respects_its_offset() -> None:
    policy = PublishedTimePolicy()
    value = effective_published(
        post("fanbox", datetime.fromisoformat("2025-12-21T00:35:43+09:00")),
        policy,
    )

    assert value == datetime(2025, 12, 20, 15, 35, 43, tzinfo=timezone.utc)


def test_publication_timezone_label_reports_the_interpretation_actually_used() -> None:
    policy = PublishedTimePolicy()

    assert published_service_timezone(post("fanbox", datetime(2025, 12, 21)), policy) == "Asia/Tokyo"
    assert (
        published_service_timezone(
            post("fanbox", datetime.fromisoformat("2025-12-21T00:35:43+09:00")),
            policy,
        )
        == "UTC+09:00"
    )
    assert (
        published_service_timezone(
            post("fanbox", datetime(2025, 12, 21, tzinfo=timezone.utc)),
            policy,
        )
        == "UTC"
    )


def test_custom_service_and_target_timezones() -> None:
    policy = PublishedTimePolicy.from_values(
        target_timezone="Asia/Shanghai",
        fallback_service_timezone="Europe/Paris",
        service_timezones={"custom": "America/New_York"},
    )

    custom = effective_published(post("custom", datetime(2026, 1, 1, 10)), policy)
    fallback = effective_published(post("other", datetime(2026, 1, 1, 10)), policy)
    assert custom == datetime.fromisoformat("2026-01-01T23:00:00+08:00")
    assert fallback == datetime.fromisoformat("2026-01-01T17:00:00+08:00")


def test_added_is_utc_and_only_used_when_published_is_missing() -> None:
    policy = PublishedTimePolicy.from_values(
        target_timezone="Asia/Tokyo",
        fallback_service_timezone="UTC",
        service_timezones={"fanbox": "Asia/Tokyo"},
    )
    item = post("fanbox", added=datetime(2026, 7, 20, 2, 30))

    assert effective_post_timestamp(item, policy) == datetime.fromisoformat("2026-07-20T11:30:00+09:00")
    assert automatic_post_timestamp(item, policy) == datetime(2026, 7, 20, 2, 30, tzinfo=timezone.utc)


def test_ambiguous_time_uses_first_occurrence_and_gap_is_rejected() -> None:
    ambiguous = localize_wall_time(datetime(2026, 11, 1, 1, 30), "America/New_York")
    assert ambiguous.fold == 0
    assert ambiguous.utcoffset() is not None
    assert ambiguous.utcoffset().total_seconds() == -4 * 3600

    with pytest.raises(PublishedTimeError, match="does not exist"):
        localize_wall_time(datetime(2026, 3, 8, 2, 30), "America/New_York", service="custom")
