"""Deterministic order-block detection based on ATR displacement."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .fvg import Bar


@dataclass(frozen=True)
class OrderBlock:
    direction: str
    formed_index: int
    formed_at: object | None
    lower: float
    upper: float
    entry: float
    stop: float
    target: float
    displacement_atr: float

    @property
    def width(self) -> float:
        return self.upper - self.lower


def true_ranges(bars: Sequence[Bar]) -> list[float]:
    if not bars:
        return []
    out = [bars[0].high - bars[0].low]
    for prev, bar in zip(bars, bars[1:]):
        out.append(max(bar.high - bar.low, abs(bar.high - prev.close),
                       abs(bar.low - prev.close)))
    return out


def atrs(bars: Sequence[Bar], period: int = 14) -> list[float | None]:
    if period < 1:
        raise ValueError("period must be positive")
    tr = true_ranges(bars)
    values: list[float | None] = [None] * len(tr)
    for i in range(period - 1, len(tr)):
        values[i] = sum(tr[i - period + 1:i + 1]) / period
    return values


def _opposite(bar: Bar, direction: str) -> bool:
    return bar.close < bar.open if direction == "long" else bar.close > bar.open


def detect_order_blocks(bars: Sequence[Bar], *, atr_period: int = 14,
                        displacement_atr: float = 1.5,
                        displacement_bars: int = 3,
                        search_back: int = 20,
                        entry_ratio: float = 0.5,
                        stop_buffer: float = 0.0,
                        target_rr: float = 1.0) -> list[OrderBlock]:
    """Find the last opposite candle before a > X*ATR move in Y bars.

    The displacement is measured from ``close[i-Y]`` to ``close[i]`` and the
    order block is the last opposite-direction candle before the displacement
    window.  No candle after ``i`` is consulted.
    """
    if displacement_bars < 1 or displacement_atr <= 0 or search_back < 1:
        raise ValueError("displacement parameters must be positive")
    if not 0 <= entry_ratio <= 1:
        raise ValueError("entry_ratio must be between 0 and 1")
    values = atrs(bars, atr_period)
    found: list[OrderBlock] = []
    for i in range(atr_period - 1 + displacement_bars, len(bars)):
        atr = values[i]
        if atr is None or atr <= 0:
            continue
        delta = bars[i].close - bars[i - displacement_bars].close
        direction = "long" if delta > 0 else "short" if delta < 0 else None
        if direction is None or abs(delta) <= displacement_atr * atr:
            continue
        start = i - displacement_bars
        candidates = range(max(0, start - search_back), start)
        opposite = [j for j in candidates if _opposite(bars[j], direction)]
        if not opposite:
            continue
        block_index = opposite[-1]
        block = bars[block_index]
        lower, upper = block.low, block.high
        if upper <= lower:
            continue
        entry = lower + (upper - lower) * entry_ratio
        risk = (entry - lower) if direction == "long" else (upper - entry)
        if risk <= 0:
            continue
        stop = lower - stop_buffer if direction == "long" else upper + stop_buffer
        target = entry + target_rr * (entry - stop) if direction == "long" else entry - target_rr * (stop - entry)
        found.append(OrderBlock(direction, i, bars[i].timestamp, lower, upper, entry,
                                stop, target, abs(delta) / atr))
    return found
