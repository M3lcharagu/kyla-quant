"""Asian range breakout; stdlib-only, stateful next(candle) adapter."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, time, timezone
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

EAT = ZoneInfo("Africa/Nairobi")
LONDON = ZoneInfo("Europe/London")

@dataclass(frozen=True)
class Signal:
    action: str
    entry: float
    stop: float
    target: float
    timestamp: datetime
    reason: str
    risk_r: float = 2.0

@dataclass(frozen=True)
class Config:
    range_start: time = time(0, 0)
    range_end: time = time(6, 0)
    london_start: time = time(8, 0)
    london_end: time = time(10, 0)
    target_r: float = 2.0
    stop_buffer: float = 0.0
    require_retest: bool = True
    max_range_fraction: float = 0.02

def _v(c: Any, key: str, default: Any = None) -> Any:
    return c.get(key, default) if isinstance(c, Mapping) else getattr(c, key, default)

def _ts(c: Any) -> datetime:
    value = _v(c, "timestamp")
    if isinstance(value, str): value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime): raise TypeError("timestamp must be datetime or ISO-8601")
    return (value if value.tzinfo else value.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)

def _in(ts: datetime, zone: ZoneInfo, start: time, end: time) -> bool:
    value = ts.astimezone(zone).time().replace(tzinfo=None)
    return start <= value < end if start < end else value >= start or value < end

class AsianRangeBreakout:
    """00:00-06:00 EAT range; one London 08:00-10:00 local break/retest."""
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config(); self._reset()
    def _reset(self) -> None:
        self.day = None; self.high = None; self.low = None; self.breakout = None; self.emitted = False
    def next(self, candle: Any) -> Signal | None:
        ts = _ts(candle); local = ts.astimezone(EAT); day = local.date()
        if day != self.day:
            self.day = day; self.high = self.low = self.breakout = None; self.emitted = False
        hi, lo, close = float(_v(candle, "high")), float(_v(candle, "low")), float(_v(candle, "close"))
        lt = local.time().replace(tzinfo=None)
        if self.config.range_start <= lt < self.config.range_end:
            self.high = hi if self.high is None else max(self.high, hi); self.low = lo if self.low is None else min(self.low, lo); return None
        if self.high is None or self.low is None or self.emitted or not _in(ts, LONDON, self.config.london_start, self.config.london_end): return None
        width, mid = self.high - self.low, (self.high + self.low) / 2
        if width <= 0 or (mid and width / abs(mid) > self.config.max_range_fraction): return None
        if self.breakout is None:
            if close > self.high: self.breakout = "long"
            elif close < self.low: self.breakout = "short"
            else: return None
            if self.config.require_retest: return None
        elif self.breakout == "long" and not (lo <= self.high and close > self.high): return None
        elif self.breakout == "short" and not (hi >= self.low and close < self.low): return None
        entry = close
        stop = self.low - self.config.stop_buffer if self.breakout == "long" else self.high + self.config.stop_buffer
        risk = entry - stop if self.breakout == "long" else stop - entry
        if risk <= 0: return None
        target = entry + self.config.target_r * risk if self.breakout == "long" else entry - self.config.target_r * risk
        self.emitted = True
        return Signal(self.breakout, entry, stop, target, ts, "Asian range break with London retest" if self.config.require_retest else "Asian range close break", self.config.target_r)
    def fit(self, data: Iterable[Any]) -> "AsianRangeBreakout": return self
    def evaluate(self, data: Iterable[Any], costs: Any = None) -> dict[str, Any]:
        self._reset(); signals = []
        for candle in data:
            signal = self.next(candle)
            if signal: signals.append(asdict(signal))
        return {"status": "OK", "signals": signals, "count": len(signals), "costs": costs}

_DEFAULT = AsianRangeBreakout()
def next(candle: Any) -> Signal | None: return _DEFAULT.next(candle)
