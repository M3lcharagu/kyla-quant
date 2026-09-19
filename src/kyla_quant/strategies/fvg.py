"""Deterministic fair-value-gap (FVG) and inverted-FVG detectors.

Definitions are deliberately price-only and auditable:
* bullish FVG: candle1.high < candle3.low;
* bearish FVG: candle1.low > candle3.high;
* entry: configurable point inside the gap (midpoint by default);
* stop: beyond the far edge of the gap;
* IFVG: a formed gap is first entered and then closed through its far edge.

The functions do not use future candles to form a gap.  A caller may use the
returned ``formed_index`` to enforce entry only after formation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Sequence


@dataclass(frozen=True)
class Bar:
    open: float
    high: float
    low: float
    close: float
    timestamp: object | None = None
    volume: float | None = None


Direction = Literal["long", "short"]


@dataclass(frozen=True)
class FVG:
    direction: Direction
    formed_index: int
    formed_at: object | None
    lower: float
    upper: float
    entry: float
    stop: float
    target: float
    inverted: bool = False
    invalidated: bool = False

    @property
    def width(self) -> float:
        return self.upper - self.lower


def _target(direction: Direction, entry: float, width: float, target_mode: str,
            htf_level: float | None) -> float:
    if target_mode == "htf_level" and htf_level is not None:
        return htf_level
    # A gap-width measured move is deterministic and available without
    # look-ahead.  HTF levels can be supplied explicitly by the caller.
    return entry + width if direction == "long" else entry - width


def detect_fvg(candle1: Bar, candle2: Bar, candle3: Bar, *, formed_index: int = 2,
               entry_ratio: float = 0.5, stop_buffer: float = 0.0,
               target_mode: str = "measured_move",
               htf_level: float | None = None) -> FVG | None:
    """Detect exactly one three-candle FVG, or return ``None``.

    ``entry_ratio`` is measured from lower to upper gap edge and must be in
    [0, 1].  It is not optimized by this module.
    """
    if not 0.0 <= entry_ratio <= 1.0:
        raise ValueError("entry_ratio must be between 0 and 1")
    if candle1.high < candle3.low:
        direction: Direction = "long"
        lower, upper = candle1.high, candle3.low
        entry = lower + (upper - lower) * entry_ratio
        stop = lower - stop_buffer
    elif candle1.low > candle3.high:
        direction = "short"
        lower, upper = candle3.high, candle1.low
        entry = upper - (upper - lower) * entry_ratio
        stop = upper + stop_buffer
    else:
        return None
    if upper <= lower or stop == entry:
        return None
    return FVG(direction, formed_index, candle3.timestamp, lower, upper, entry,
               stop, _target(direction, entry, upper - lower, target_mode, htf_level))


def detect_fvgs(bars: Sequence[Bar], **kwargs: object) -> list[FVG]:
    """Return all three-candle FVGs in chronological order."""
    return [
        found
        for i in range(2, len(bars))
        if (found := detect_fvg(bars[i - 2], bars[i - 1], bars[i], formed_index=i, **kwargs))
        is not None
    ]


def detect_ifvgs(bars: Sequence[Bar], **kwargs: object) -> list[FVG]:
    """Return gaps that were entered and subsequently closed through.

    A bullish gap becomes a short IFVG after a bar's low enters the gap and a
    later close is below ``lower``.  A bearish gap becomes a long IFVG after a
    bar's high enters the gap and a later close is above ``upper``.  The
    returned setup uses the original gap, with direction inverted and the
    original opposite edge as the stop.
    """
    results: list[FVG] = []
    for gap in detect_fvgs(bars, **kwargs):
        entered = False
        for i in range(gap.formed_index + 1, len(bars)):
            bar = bars[i]
            if gap.direction == "long":
                entered = entered or bar.low <= gap.upper
                if entered and bar.close < gap.lower:
                    entry = (gap.lower + gap.upper) / 2.0
                    results.append(FVG("short", i, bar.timestamp, gap.lower, gap.upper,
                                       entry, gap.upper, entry - gap.width,
                                       inverted=True, invalidated=True))
                    break
            else:
                entered = entered or bar.high >= gap.lower
                if entered and bar.close > gap.upper:
                    entry = (gap.lower + gap.upper) / 2.0
                    results.append(FVG("long", i, bar.timestamp, gap.lower, gap.upper,
                                       entry, gap.lower, entry + gap.width,
                                       inverted=True, invalidated=True))
                    break
    return results


def bars_from_rows(rows: Iterable[dict[str, object]]) -> list[Bar]:
    """Small adapter for JSON/CSV OHLC rows used by research scripts."""
    return [Bar(float(r["open"]), float(r["high"]), float(r["low"]),
                float(r["close"]), r.get("timestamp"),
                float(r["volume"]) if r.get("volume") is not None else None)
            for r in rows]
