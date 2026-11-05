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


def rate_limit_delay(
    retry_after: float | None,
    attempt: int,
    interval: float,
    *,
    maximum: float = MAX_RATE_LIMIT_DELAY,
) -> float:
    """
    Choose how long to wait before retrying a rate-limited request.

    The server's ``Retry-After`` wins when present. Without it the wait doubles with every
    attempt, starting from ``interval``. The result is never shorter than ``interval`` and
    never longer than ``maximum`` (unless ``interval`` itself is longer).

    :param retry_after: Seconds from ``parse_retry_after``, or ``None``
    :param attempt: Number of the attempt that was rate-limited, starting at 1
    :param interval: Configured retry interval in seconds
    :param maximum: Upper bound for a single wait in seconds
    :return: Seconds to wait
    """
    if retry_after is None:
        exponent = min(max(attempt - 1, 0), _MAX_BACKOFF_EXPONENT)
        delay = interval * 2.0**exponent
    else:
        delay = retry_after
    return max(interval, min(delay, maximum))
