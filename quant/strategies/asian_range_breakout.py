"""USDJPY Asian range breakout; stdlib-only streaming adapter."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo
EAT = ZoneInfo("Africa/Nairobi")

@dataclass(frozen=True)
class Signal:
    action: str
    entry: float
    stop: float
    target: float
    timestamp: datetime
    reason: str
    risk_r: float = 0.0

@dataclass(frozen=True)
class Config:
    range_start: time = time(3, 0)
    range_end: time = time(10, 0)
    breakout_start: time = time(10, 0)
    breakout_end: time = time(14, 0)
    target_r: float = 2.0
    boj_lock: bool = False
    require_five_minute: bool = True

def _get(c: Any, key: str, default: Any = None) -> Any:
    return c.get(key, default) if isinstance(c, Mapping) else getattr(c, key, default)

def _ts(c: Any) -> datetime:
    value = _get(c, "timestamp", _get(c, "time"))
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime):
        raise TypeError("timestamp must be datetime or ISO-8601")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

def _window(t: time, start: time, end: time) -> bool:
    return start <= t < end

def _is_five_minute(c: Any) -> bool:
    value = _get(c, "timeframe_minutes", _get(c, "minutes", _get(c, "timeframe")))
    if value is None:
        return True  # adapter default: incoming breakout candles are 5-minute candles
    if isinstance(value, str):
        value = value.lower().replace("min", "").strip()
    try:
        return float(value) == 5.0
    except (TypeError, ValueError):
        return False

class AsianRangeBreakout:
    """Build 03:00-10:00 EAT, then accept only 5-minute closes to 14:00 EAT."""
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        if self.config.target_r <= 0:
            raise ValueError("target_r must be positive")
        self._reset()

    def _reset(self) -> None:
        self.day = None
        self.high = None
        self.low = None
        self.emitted = False
        self._boj_lock = False

    def set_boj_lock(self, locked: bool) -> None:
        self._boj_lock = bool(locked)

    def next(self, candle: Any) -> Signal | None:
        ts = _ts(candle)
        local = ts.astimezone(EAT)
        if local.date() != self.day:
            self._reset()
            self.day = local.date()
        high = float(_get(candle, "high"))
        low = float(_get(candle, "low"))
        close = float(_get(candle, "close"))
        clock = local.time().replace(tzinfo=None)
        if _window(clock, self.config.range_start, self.config.range_end):
            self.high = high if self.high is None else max(self.high, high)
            self.low = low if self.low is None else min(self.low, low)
            return None
        if not _window(clock, self.config.breakout_start, self.config.breakout_end):
            return None
        if self.config.require_five_minute and not _is_five_minute(candle):
            return None
        if self.emitted or self.high is None or self.low is None or self.high <= self.low:
            return None
        dynamic_lock = any(bool(_get(candle, k, False)) for k in ("boj_lock", "boj_intervention_lock", "rate_check_lock"))
        if self.config.boj_lock or self._boj_lock or dynamic_lock:
            return None
        if close > self.high:
            action = "long"
        elif close < self.low:
            action = "short"
        else:
            return None
        entry = close
        stop = self.low if action == "long" else self.high
        risk = entry - stop if action == "long" else stop - entry
        if risk <= 0:
            return None
        target = entry + self.config.target_r * risk if action == "long" else entry - self.config.target_r * risk
        self.emitted = True
        return Signal(action, entry, stop, target, ts, "USDJPY Asian range 5-minute close breakout", self.config.target_r)

    def fit(self, data: Iterable[Any]) -> "AsianRangeBreakout":
        return self

    def evaluate(self, data: Iterable[Any], costs: Any = None) -> dict[str, Any]:
        self._reset()
        signals = [s for c in data if (s := self.next(c)) is not None]
        return {"status": "OK", "signals": signals, "count": len(signals), "costs": costs}

_DEFAULT = AsianRangeBreakout()
def next(candle: Any) -> Signal | None:
    return _DEFAULT.next(candle)
