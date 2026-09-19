"""Current market-state calculations with explicit unknown states."""
from __future__ import annotations

from datetime import datetime, timezone
from statistics import median
from typing import Iterable

from .schemas import MarketState


def spread_vs_rolling_median(spread: float | None, history: Iterable[float]) -> tuple[float | None, str]:
    values = list(history)
    if spread is None or not values:
        return None, "unknown"
    med = median(values)
    return med, "wide" if spread > med else "normal_or_tight"


def build_now_state(*, spread: float | None = None, spread_history: Iterable[float] = (),
                    volatility_state: str = "unknown", session: str = "unknown",
                    trend_range: str = "unknown", funding_context: str = "unknown",
                    open_interest_context: str = "unknown", news_lock: bool = False,
                    data_ok: bool = False, as_of: datetime | None = None) -> MarketState:
    """Build a state snapshot; callers should supply vendor-derived features."""
    median_spread, spread_state = spread_vs_rolling_median(spread, spread_history)
    notes = [f"spread_state={spread_state}"]
    if not data_ok:
        notes.append("data_not_verified")
    return MarketState(
        as_of=(as_of or datetime.now(timezone.utc)).astimezone(timezone.utc),
        spread=spread,
        rolling_spread_median=median_spread,
        volatility_state=volatility_state,
        session=session,
        trend_range=trend_range,
        funding_context=funding_context,
        open_interest_context=open_interest_context,
        news_lock=news_lock,
        data_ok=data_ok,
        notes=notes,
    )
