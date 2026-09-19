"""Daily market brief template; no narrative claims are fabricated."""
from __future__ import annotations

from datetime import date
from typing import Any

from .schemas import Brief, MarketState


def daily_brief(*, day: date, state: MarketState, context: Any = None,
                events: Any = None, stance: str = "DATA_FAILURE") -> Brief:
    return Brief(
        date=day.isoformat(),
        headline="TODO: populate from verified data only",
        sections={
            "now_state": state,
            "monthly_context": context,
            "upcoming_events": events,
            "stance": stance,
            "no_trade_conditions": ["stale data", "high-impact event lock", "risk limit", "manual kill"],
        },
    )
