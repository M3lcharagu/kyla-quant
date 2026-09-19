"""XAUUSD 10:00-13:00 EAT Asian-liquidity-sweep/FVG scalp."""
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
    risk_r: float = 1.5
    session: str = "killzone"

@dataclass(frozen=True)
class Config:
    asian_start: time = time(3, 0)
    asian_end: time = time(10, 0)
    killzone_start: time = time(10, 0)
    killzone_end: time = time(13, 0)
    target_r: float = 1.5
    stop_buffer: float = 0.0
    atr_period: int = 14
    displacement_atr: float = 1.0
    spread_multiple: float = 2.0

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

class GoldKillzoneScalp:
    """Track Asian 03:00-10:00 EAT high/low; trade sweep, displacement, FVG retrace."""
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self._reset()

    def _reset(self) -> None:
        self.day = None
        self.asian_high = None
        self.asian_low = None
        self.previous = None
        self.ranges = []
        self.sweep = None
        self.fvg = None
        self.emitted = False

    def next(self, candle: Any) -> Signal | None:
        ts = _ts(candle)
        local = ts.astimezone(EAT)
        if local.date() != self.day:
            self._reset()
            self.day = local.date()
        high, low = float(_get(candle, "high")), float(_get(candle, "low"))
        close = float(_get(candle, "close"))
        open_ = float(_get(candle, "open", close))
        clock = local.time().replace(tzinfo=None)
        if _window(clock, self.config.asian_start, self.config.asian_end):
            self.asian_high = high if self.asian_high is None else max(self.asian_high, high)
            self.asian_low = low if self.asian_low is None else min(self.asian_low, low)
            self.ranges.append(max(0.0, high - low))
            self.previous = candle
            return None
        if not _window(clock, self.config.killzone_start, self.config.killzone_end):
            self.previous = candle
            return None
        if self.emitted or self.asian_high is None or self.asian_low is None:
            self.previous = candle
            return None
        spread = _get(candle, "spread")
        median = _get(candle, "rolling_median_spread", _get(candle, "spread_median"))
        if spread is None or median is None:
            self.previous = candle
            return None
        spread, median = float(spread), float(median)
        if median <= 0 or spread > self.config.spread_multiple * median:
            self.previous = candle
            return None
        if self.sweep is None:
            if low < self.asian_low and close > self.asian_low:
                self.sweep = {"action": "long", "extreme": low, "remaining": 3}
            elif high > self.asian_high and close < self.asian_high:
                self.sweep = {"action": "short", "extreme": high, "remaining": 3}
            self.previous = candle
            return None
        action = self.sweep["action"]
        if self.fvg is None:
            prev_high = float(_get(self.previous, "high")) if self.previous is not None else None
            prev_low = float(_get(self.previous, "low")) if self.previous is not None else None
            body = abs(close - open_)
            recent = self.ranges[-self.config.atr_period:]
            atr = sum(recent) / len(recent) if recent else max(high - low, body)
            directional = (action == "long" and close > open_) or (action == "short" and close < open_)
            displaced = directional and body >= self.config.displacement_atr * atr
            if displaced and action == "long" and prev_high is not None and low > prev_high:
                self.fvg = (prev_high, low, action)
            elif displaced and action == "short" and prev_low is not None and high < prev_low:
                self.fvg = (high, prev_low, action)
            self.sweep["remaining"] -= 1
            if self.sweep["remaining"] <= 0 and self.fvg is None:
                self.sweep = None
            self.previous = candle
            self.ranges.append(max(0.0, high - low))
            return None
        gap_low, gap_high, gap_action = self.fvg
        retraced = low <= gap_high and high >= gap_low
        closes_in_direction = (gap_action == "long" and close >= gap_low) or (gap_action == "short" and close <= gap_high)
        if not (retraced and closes_in_direction):
            self.previous = candle
            self.ranges.append(max(0.0, high - low))
            return None
        entry = close
        stop = self.sweep["extreme"] - self.config.stop_buffer if action == "long" else self.sweep["extreme"] + self.config.stop_buffer
        risk = entry - stop if action == "long" else stop - entry
        if risk <= 0:
            return None
        target = entry + self.config.target_r * risk if action == "long" else entry - self.config.target_r * risk
        self.emitted = True
        return Signal(action, entry, stop, target, ts, "XAUUSD Asian liquidity sweep, displacement, FVG retrace", self.config.target_r)

    def fit(self, data: Iterable[Any]) -> "GoldKillzoneScalp":
        return self

    def evaluate(self, data: Iterable[Any], costs: Any = None) -> dict[str, Any]:
        self._reset()
        signals = [s for c in data if (s := self.next(c)) is not None]
        return {"status": "OK", "signals": signals, "count": len(signals), "costs": costs}

_DEFAULT = GoldKillzoneScalp()
def next(candle: Any) -> Signal | None:
    return _DEFAULT.next(candle)
