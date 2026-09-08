from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_SERVICE_TIMEZONES: dict[str, str] = {
    "fanbox": "Asia/Tokyo",
    "patreon": "UTC",
}


class PublishedPost(Protocol):
    service: str
    published: datetime | None
    added: datetime | None


class PublishedTimeError(ValueError):
    """Raised when an upstream local timestamp cannot identify a real instant."""

    code = "published_time_invalid"

    def __init__(self, message: str, *, service: str, timezone_name: str) -> None:
        super().__init__(message)
        self.service = service
        self.timezone_name = timezone_name


def normalize_service_name(value: str) -> str:
    """Normalize a Pawchive service key used by timezone mappings."""

    normalized = value.strip().lower()
    if not normalized:
        raise ValueError("service names cannot be empty")
    return normalized


def validate_iana_timezone(value: str) -> str:
    """Validate and normalize one IANA timezone name."""

    normalized = value.strip()
    if not normalized:
        raise ValueError("timezone cannot be empty")
    try:
        ZoneInfo(normalized)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError(f"unknown IANA timezone: {normalized}") from error
    return normalized


@dataclass(frozen=True, slots=True)
class PublishedTimePolicy:
    """Immutable interpretation policy frozen into one task or naming layout."""

    target_timezone: str = "UTC"
    fallback_service_timezone: str = "UTC"
    service_timezones: tuple[tuple[str, str], ...] = tuple(DEFAULT_SERVICE_TIMEZONES.items())

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_timezone", validate_iana_timezone(self.target_timezone))
        object.__setattr__(
            self,
            "fallback_service_timezone",
            validate_iana_timezone(self.fallback_service_timezone),
        )
        normalized: dict[str, str] = {}
        for service, timezone_name in self.service_timezones:
            normalized[normalize_service_name(service)] = validate_iana_timezone(timezone_name)
        object.__setattr__(self, "service_timezones", tuple(sorted(normalized.items())))

    @classmethod
    def from_values(
        cls,
        *,
        target_timezone: str,
        fallback_service_timezone: str,
        service_timezones: dict[str, str],
    ) -> PublishedTimePolicy:
        return cls(
            target_timezone=target_timezone,
            fallback_service_timezone=fallback_service_timezone,
            service_timezones=tuple(service_timezones.items()),
        )

    @classmethod
    def legacy_raw(cls) -> PublishedTimePolicy:
        """Represent the pre-fix behavior that treated naive values as UTC."""

        return cls(target_timezone="UTC", fallback_service_timezone="UTC", service_timezones=())

    def service_timezone(self, service: str) -> str:
        normalized = normalize_service_name(service)
        return dict(self.service_timezones).get(normalized, self.fallback_service_timezone)

    def model_dump(self) -> dict[str, object]:
        return {
            "target_timezone": self.target_timezone,
            "fallback_service_timezone": self.fallback_service_timezone,
            "service_timezones": dict(self.service_timezones),
        }


def localize_wall_time(value: datetime, timezone_name: str, *, service: str = "") -> datetime:
    """Attach an IANA timezone and reject nonexistent daylight-saving wall times."""

    zone = ZoneInfo(validate_iana_timezone(timezone_name))
    if value.tzinfo is not None:
        return value.astimezone(zone)

    # fold=0 is the first occurrence of an ambiguous wall time. A round trip
    # through UTC distinguishes real wall times from daylight-saving gaps.
    candidate = value.replace(tzinfo=zone, fold=0)
    round_trip = candidate.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
    if round_trip != value:
        raise PublishedTimeError(
            f"published time {value.isoformat()} does not exist in {timezone_name}",
            service=service or "unknown",
            timezone_name=timezone_name,
        )
    return candidate


def as_utc(value: datetime, assumed_timezone: str) -> datetime:
    """Interpret a naive datetime in ``assumed_timezone`` and return its UTC instant."""

    if value.tzinfo is None:
        value = localize_wall_time(value, assumed_timezone)
    return value.astimezone(timezone.utc)


def effective_published(post: PublishedPost, policy: PublishedTimePolicy) -> datetime | None:
    """Return ``published`` as the same instant in the configured target timezone."""

    if post.published is None:
        return None
    service_timezone = policy.service_timezone(post.service)
    if post.published.tzinfo is None:
        localized = localize_wall_time(post.published, service_timezone, service=post.service)
    else:
        localized = post.published
    return localized.astimezone(ZoneInfo(policy.target_timezone))


def effective_post_timestamp(post: PublishedPost, policy: PublishedTimePolicy) -> datetime | None:
    """Resolve the timestamp used by naming, display, and manual date filters."""

    if post.published is not None:
        return effective_published(post, policy)
    if post.added is None:
        return None
    added_utc = as_utc(post.added, "UTC")
    return added_utc.astimezone(ZoneInfo(policy.target_timezone))


def automatic_post_timestamp(post: PublishedPost, policy: PublishedTimePolicy) -> datetime | None:
    """Resolve the automatic-sync inspection instant in UTC."""

    if post.added is not None:
        return as_utc(post.added, "UTC")
    published = effective_published(post, policy)
    return published.astimezone(timezone.utc) if published is not None else None


def target_boundary(value: datetime, policy: PublishedTimePolicy) -> datetime:
    """Interpret a manual date boundary in the configured target timezone."""

    if value.tzinfo is None:
        return localize_wall_time(value, policy.target_timezone)
    return value.astimezone(ZoneInfo(policy.target_timezone))
