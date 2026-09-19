"""Event cache and 30-minute risk-lock helpers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from .schemas import Event


@dataclass
class EventCache:
    """Cache boundary for FRED/BLS/FOMC events; persistence is a TODO."""

    events: list[Event]
    source_status: dict[str, str]

    @classmethod
    def placeholder(cls) -> "EventCache":
        return cls([], {"fred": "TODO", "bls": "TODO", "fomc": "TODO"})


def event_lock_state(now: datetime, events: Iterable[Event], lock_minutes: int = 30) -> tuple[bool, list[str]]:
    now = now.astimezone(timezone.utc)
    reasons: list[str] = []
    window = timedelta(minutes=lock_minutes)
    for event in events:
        starts = event.starts_at.astimezone(timezone.utc)
        if abs(starts - now) <= window and event.impact.lower() in {"high", "critical"}:
            reasons.append(f"{event.source}:{event.name} within {lock_minutes}m")
    return bool(reasons), reasons
