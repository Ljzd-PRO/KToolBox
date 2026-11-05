from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ktoolbox.api.rate_limit import MAX_RATE_LIMIT_DELAY, parse_retry_after, rate_limit_delay

NOW = datetime(2015, 10, 21, 7, 28, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("120", 120.0),
        (" 5 ", 5.0),
        ("0", 0.0),
        ("Wed, 21 Oct 2015 07:30:00 GMT", 120.0),
        ("Wed, 21 Oct 2015 07:28:30 -0000", 30.0),
        ("Wed, 21 Oct 2015 07:00:00 GMT", 0.0),
    ],
)
def test_parse_retry_after_accepts_seconds_and_http_dates(value: str, expected: float) -> None:
    assert parse_retry_after(value, now=NOW) == expected


@pytest.mark.parametrize("value", [None, "", "soon", "-5", "1.5", "²"])
def test_parse_retry_after_ignores_missing_or_malformed_values(value: str | None) -> None:
    assert parse_retry_after(value, now=NOW) is None


def test_parse_retry_after_defaults_to_the_current_time() -> None:
    delay = parse_retry_after("Fri, 01 Jan 9999 00:00:00 GMT")
    assert delay is not None and delay > 0


@pytest.mark.parametrize(
    ("retry_after", "attempt", "interval", "expected"),
    [
        (10.0, 1, 2.0, 10.0),  # the server's value wins
        (0.0, 1, 2.0, 2.0),  # but never below the interval
        (10_000.0, 1, 2.0, MAX_RATE_LIMIT_DELAY),  # and never above the cap
        (None, 1, 2.0, 2.0),  # without Retry-After, double per attempt
        (None, 2, 2.0, 4.0),
        (None, 5, 2.0, 32.0),
        (None, 10_000, 2.0, MAX_RATE_LIMIT_DELAY),  # endless retries don't overflow
        (None, 1, 600.0, 600.0),  # an interval above the cap wins
        (5.0, 1, 600.0, 600.0),
    ],
)
def test_rate_limit_delay(retry_after: float | None, attempt: int, interval: float, expected: float) -> None:
    assert rate_limit_delay(retry_after, attempt, interval) == expected
