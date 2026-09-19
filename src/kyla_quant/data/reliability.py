"""Stubs for rate limiting, reconnection, and gap detection."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable


@dataclass(frozen=True)
class RateLimitPolicy:
    requests_per_minute: int = 60
    backoff_seconds: float = 1.0


class ReconnectionPolicy:
    """Documented placeholder for exponential backoff and circuit breaking."""

    def next_delay(self, attempt: int) -> float:
        return min(60.0, 2.0 ** max(0, attempt))


@dataclass(frozen=True)
class Gap:
    start: datetime
    end: datetime
    expected_seconds: int


def detect_gaps(timestamps: Iterable[datetime], expected_seconds: int) -> list[Gap]:
    """Identify missing bars; timestamps must be timezone-aware and sorted or will be sorted."""
    values = sorted(timestamps)
    gaps: list[Gap] = []
    for previous, current in zip(values, values[1:]):
        delta = current - previous
        if delta > timedelta(seconds=expected_seconds):
            gaps.append(Gap(previous, current, expected_seconds))
    return gaps


def retryable_request(*_: Any, **__: Any) -> None:
    """TODO: wrap vendor requests with policy, jitter, reconnect, and observability."""
    raise NotImplementedError("Live request wrapper is intentionally not implemented")
