from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from ktoolbox.api.generated import Post


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
