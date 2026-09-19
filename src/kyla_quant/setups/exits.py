"""Stop, target, and mandatory 43–45 minute time exit."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum


class ExitReason(str, Enum):
    STOP = "STOP"
    TARGET = "TARGET"
    TIME_EXIT = "TIME_EXIT"


@dataclass(frozen=True)
class ExitDecision:
    reason: ExitReason | None
    price: float | None
    flat_required: bool


def evaluate_exit(*, entry_price: float, stop_price: float, target_price: float,
                  current_price: float, opened_at: datetime, now: datetime,
                  side: str, time_exit_minutes: int = 45) -> ExitDecision:
    """Evaluate exits; callers must apply venue-specific intrabar ordering policy."""
    elapsed = now.astimezone(timezone.utc) - opened_at.astimezone(timezone.utc)
    if elapsed >= timedelta(minutes=time_exit_minutes):
        return ExitDecision(ExitReason.TIME_EXIT, current_price, True)
    if side.lower() == "long":
        if current_price <= stop_price:
            return ExitDecision(ExitReason.STOP, stop_price, True)
        if current_price >= target_price:
            return ExitDecision(ExitReason.TARGET, target_price, True)
    elif side.lower() == "short":
        if current_price >= stop_price:
            return ExitDecision(ExitReason.STOP, stop_price, True)
        if current_price <= target_price:
            return ExitDecision(ExitReason.TARGET, target_price, True)
    else:
        raise ValueError("side must be long or short")
    return ExitDecision(None, None, False)
