"""Typed schemas shared by market intelligence modules."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Stance(str, Enum):
    TRADE_ALLOWED = "TRADE_ALLOWED"
    REDUCED = "REDUCED"
    BLOCKED = "BLOCKED"
    FLAT_ONLY = "FLAT_ONLY"
    DATA_FAILURE = "DATA_FAILURE"
    MANUAL_KILL = "MANUAL_KILL"


@dataclass(frozen=True)
class Event:
    name: str
    starts_at: datetime
    impact: str = "unknown"
    source: str = "placeholder"


@dataclass
class MarketState:
    as_of: datetime
    spread: float | None = None
    rolling_spread_median: float | None = None
    volatility_state: str = "unknown"
    session: str = "unknown"
    trend_range: str = "unknown"
    funding_context: str = "unknown"
    open_interest_context: str = "unknown"
    news_lock: bool = False
    data_ok: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class StanceDecision:
    stance: Stance
    reasons: tuple[str, ...]
    as_of: datetime
    hard_gates: tuple[str, ...] = ()


@dataclass(frozen=True)
class Brief:
    date: str
    headline: str
    sections: dict[str, Any]
    disclaimer: str = "Context is not a trade recommendation."
