"""Month-to-date context; calculations are intentionally transparent."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Sequence


@dataclass(frozen=True)
class MonthlyContext:
    mtd_return: float | None
    mtd_range: float | None
    realized_volatility: float | None
    macro_regime: str
    expiries: tuple[str, ...]
    notes: tuple[str, ...] = ()


def summarize_month(*, prices: Sequence[float], macro_regime: str = "unknown",
                    expiries: Sequence[str] = ()) -> MonthlyContext:
    if len(prices) < 2 or prices[0] == 0:
        return MonthlyContext(None, None, None, macro_regime, tuple(expiries), ("insufficient_prices",))
    returns = [(b / a) - 1 for a, b in zip(prices, prices[1:]) if a]
    return MonthlyContext(
        mtd_return=(prices[-1] / prices[0]) - 1,
        mtd_range=max(prices) - min(prices),
        realized_volatility=pstdev(returns) if len(returns) > 1 else (abs(returns[0]) if returns else None),
        macro_regime=macro_regime,
        expiries=tuple(expiries),
    )
