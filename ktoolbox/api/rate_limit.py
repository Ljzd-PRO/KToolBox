"""Back-off helpers for HTTP 429 (Too Many Requests) responses."""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

__all__ = ["MAX_RATE_LIMIT_DELAY", "parse_retry_after", "rate_limit_delay"]

MAX_RATE_LIMIT_DELAY = 300.0
"""Longest single wait, in seconds, after a rate-limited response."""

_MAX_BACKOFF_EXPONENT = 16
"""Keeps ``2 ** exponent`` small when retries never stop; the delay is capped long before this."""


def parse_retry_after(value: str | None, *, now: datetime | None = None) -> float | None:
    """
    Read the delay requested by a ``Retry-After`` header.

    Both RFC 9110 forms are accepted: a number of seconds (``120``) and an HTTP date
    (``Wed, 21 Oct 2015 07:28:00 GMT``). A date in the past means "retry now".

    :param value: Raw header value, or ``None`` when the header is absent
    :param now: Current time, for tests; defaults to the system clock
    :return: Seconds to wait, or ``None`` when the header is missing or malformed
    """
    if value is None:
        return None
    value = value.strip()
    if value.isascii() and value.isdigit():
        return float(value)
    try:
        retry_at = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    return max((retry_at - current).total_seconds(), 0.0)


def rate_limit_delay(retry_after: float | None, attempt: int, interval: float) -> float:
    """
    Seconds to wait before retrying after HTTP 429.

    The server's ``Retry-After`` wins; without it the wait doubles from ``interval`` on each
    attempt (``attempt`` counts from 1). The result stays between ``interval`` and
    ``MAX_RATE_LIMIT_DELAY``.
    """
    delay = interval * 2.0 ** min(attempt - 1, _MAX_BACKOFF_EXPONENT) if retry_after is None else retry_after
    return max(interval, min(delay, MAX_RATE_LIMIT_DELAY))
