from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from croniter import croniter

from ktoolbox.api.generated import Post
from ktoolbox.project_config import (
    AutomaticSyncSchedule,
    CronAutomaticSyncSchedule,
    IntervalAutomaticSyncSchedule,
)


@dataclass(frozen=True, slots=True)
class AutomaticSyncWindow:
    """A fixed automatic-sync inspection window for one creator."""

    start_at: datetime | None
    end_at: datetime
    fallback_timezone: str

    def __post_init__(self) -> None:
        if self.start_at is not None and self.start_at.tzinfo is None:
            raise ValueError("automatic sync window start must include a timezone")
        if self.end_at.tzinfo is None:
            raise ValueError("automatic sync window end must include a timezone")
        if self.start_at is not None and self.start_at > self.end_at:
            raise ValueError("automatic sync window start must not be later than its end")
        ZoneInfo(self.fallback_timezone)

    def includes(self, post: Post) -> bool:
        timestamp = automatic_post_timestamp(post, self.fallback_timezone)
        if timestamp is None or timestamp > self.end_at.astimezone(timezone.utc):
            return False
        return self.start_at is None or timestamp >= self.start_at.astimezone(timezone.utc)


def automatic_post_timestamp(post: Post, fallback_timezone: str) -> datetime | None:
    """Resolve the best observed timestamp without changing manual date filtering."""

    if post.added is not None:
        return _as_utc(post.added, timezone.utc)
    if post.published is not None:
        return _as_utc(post.published, ZoneInfo(fallback_timezone))
    return None


def _as_utc(value: datetime, default_timezone: ZoneInfo | timezone) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=default_timezone)
    return value.astimezone(timezone.utc)


def next_automatic_sync_time(schedule: AutomaticSyncSchedule, after: datetime) -> datetime:
    """Return the first scheduled UTC instant strictly after ``after``."""

    if after.tzinfo is None:
        raise ValueError("automatic sync schedule boundaries must include a timezone")
    if isinstance(schedule, IntervalAutomaticSyncSchedule):
        return _next_interval_time(schedule, after)
    return _next_cron_time(schedule, after)


def _next_interval_time(schedule: IntervalAutomaticSyncSchedule, after: datetime) -> datetime:
    duration = timedelta(**{schedule.unit: schedule.every})
    anchor = schedule.anchor_at or datetime(1970, 1, 1, tzinfo=timezone.utc)
    anchor = anchor.astimezone(timezone.utc)
    after_utc = after.astimezone(timezone.utc)
    if after_utc < anchor:
        return anchor
    elapsed = after_utc - anchor
    intervals = elapsed // duration + 1
    return anchor + intervals * duration


def _next_cron_time(schedule: CronAutomaticSyncSchedule, after: datetime) -> datetime:
    zone = ZoneInfo(schedule.timezone)
    iterator = croniter(schedule.expression, after.astimezone(zone))
    for _ in range(8):
        candidate = iterator.get_next(datetime)
        if candidate.tzinfo is None:
            candidate = candidate.replace(tzinfo=zone)
        # Ambiguous local times execute only at the first occurrence.
        if candidate.fold == 1:
            continue
        return candidate.astimezone(timezone.utc)
    raise RuntimeError("unable to resolve the next automatic sync Cron occurrence")
