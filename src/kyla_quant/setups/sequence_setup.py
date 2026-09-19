"""Deterministic SSS/BBB/BBS/SSB sequence detection.

No signal is emitted when a required feature is missing. Thresholds are explicit
arguments so a backtest can version and audit them rather than hiding discretion.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class BarType(str, Enum):
    SELL = "S"
    BUY = "B"
    DOJI = "D"


@dataclass(frozen=True)
class Bar:
    open: float
    high: float
    low: float
    close: float
    ema: float | None = None
    ema_previous: float | None = None
    momentum: float | None = None
    volume: float | None = None
    average_volume: float | None = None

    @property
    def kind(self) -> BarType:
        if self.close > self.open:
            return BarType.BUY
        if self.close < self.open:
            return BarType.SELL
        return BarType.DOJI

    @property
    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low


@dataclass(frozen=True)
class SequenceSignal:
    name: str
    direction: str
    reason: str


def _filters_pass(bars: Sequence[Bar], *, direction: str, min_momentum: float,
                  min_volume_ratio: float, wick_rejection: bool) -> bool:
    if len(bars) != 3 or any(b.ema is None or b.ema_previous is None or b.momentum is None or b.volume is None or b.average_volume in (None, 0) for b in bars):
        return False
    last = bars[-1]
    ema_up = all(b.ema >= b.ema_previous for b in bars)
    ema_down = all(b.ema <= b.ema_previous for b in bars)
    volume_ok = last.volume >= last.average_volume * min_volume_ratio
    if direction == "long":
        rejection = last.lower_wick > last.upper_wick if wick_rejection else True
        return ema_up and last.momentum >= min_momentum and volume_ok and rejection
    rejection = last.upper_wick > last.lower_wick if wick_rejection else True
    return ema_down and last.momentum <= -min_momentum and volume_ok and rejection


def detect_sequence(bars: Sequence[Bar], *, min_momentum: float = 0.0,
                    min_volume_ratio: float = 1.0, wick_rejection: bool = True) -> SequenceSignal | None:
    if len(bars) != 3:
        return None
    pattern = "".join(bar.kind.value for bar in bars)
    direction = "long" if pattern in {"BBB", "SSB"} else "short" if pattern in {"SSS", "BBS"} else None
    if direction is None or not _filters_pass(bars, direction=direction, min_momentum=min_momentum, min_volume_ratio=min_volume_ratio, wick_rejection=wick_rejection):
        return None
    return SequenceSignal(pattern, direction, "bar color, wick rejection, EMA direction, momentum, and volume filters passed")
