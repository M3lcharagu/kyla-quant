"""XAUUSD sweep/displacement scalp; stdlib-only, stateful next(candle) adapter."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, time, timezone
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

EAT = ZoneInfo("Africa/Nairobi"); LONDON = ZoneInfo("Europe/London"); NEW_YORK = ZoneInfo("America/New_York")
@dataclass(frozen=True)
class Signal:
    action: str; entry: float; stop: float; target: float; timestamp: datetime; reason: str; risk_r: float = 1.5; session: str = ""
@dataclass(frozen=True)
class Config:
    london_start: time = time(8, 0); london_end: time = time(10, 0)
    new_york_start: time = time(8, 30); new_york_end: time = time(10, 30)
    target_r: float = 1.5; stop_buffer: float = 0.0; atr_period: int = 14
    displacement_atr: float = 1.0; confirmation_bars: int = 3
    max_spread: float | None = None; max_trades_per_session: int = 1

def _v(c: Any, key: str, default: Any = None) -> Any: return c.get(key, default) if isinstance(c, Mapping) else getattr(c, key, default)
def _ts(c: Any) -> datetime:
    value = _v(c, "timestamp")
    if isinstance(value, str): value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime): raise TypeError("timestamp must be datetime or ISO-8601")
    return (value if value.tzinfo else value.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
def _in(ts: datetime, zone: ZoneInfo, start: time, end: time) -> bool:
    value = ts.astimezone(zone).time().replace(tzinfo=None); return start <= value < end if start < end else value >= start or value < end

class GoldKillzoneScalp:
    """One trade per London/NY kill zone after prior-EAT-day sweep and displacement."""
    def __init__(self, config: Config | None = None) -> None: self.config = config or Config(); self._reset()
    def _reset(self) -> None:
        self.daily = {}; self.ranges = []; self.previous = None; self.session = None; self.sweep = None; self.trades = 0
    def _session(self, ts: datetime) -> str | None:
        if _in(ts, LONDON, self.config.london_start, self.config.london_end): return "london"
        if _in(ts, NEW_YORK, self.config.new_york_start, self.config.new_york_end): return "new_york"
        return None
    def next(self, candle: Any) -> Signal | None:
        ts = _ts(candle); day = ts.astimezone(EAT).date(); hi, lo, close = float(_v(candle,"high")), float(_v(candle,"low")), float(_v(candle,"close")); session = self._session(ts)
        if session != self.session: self.session, self.sweep, self.trades = session, None, 0
        old = [d for d in self.daily if d < day]; ref_hi = max((self.daily[d][0] for d in old), default=None); ref_lo = min((self.daily[d][1] for d in old), default=None)
        previous, atr = self.previous, (sum(self.ranges[-self.config.atr_period:]) / min(len(self.ranges), self.config.atr_period) if self.ranges else 0.0)
        spread = _v(candle, "spread")
        if session and self.trades < self.config.max_trades_per_session and self.sweep is None and ref_hi is not None and ref_lo is not None:
            if lo <= ref_lo < close: self.sweep = {"action":"long", "extreme":lo, "remaining":self.config.confirmation_bars}
            elif hi >= ref_hi > close: self.sweep = {"action":"short", "extreme":hi, "remaining":self.config.confirmation_bars}
        signal = None
        if session and self.sweep and self.trades < self.config.max_trades_per_session and previous is not None:
            body = abs(close - float(_v(candle,"open",close))); disp = not atr or body >= self.config.displacement_atr * atr
            spread_ok = self.config.max_spread is None or spread is None or float(spread) <= self.config.max_spread
            long_ok = self.sweep["action"] == "long" and close > float(_v(previous,"high")); short_ok = self.sweep["action"] == "short" and close < float(_v(previous,"low"))
            if disp and spread_ok and (long_ok or short_ok):
                entry = close; action = self.sweep["action"]
                stop = self.sweep["extreme"] - self.config.stop_buffer if action == "long" else self.sweep["extreme"] + self.config.stop_buffer
                risk = entry - stop if action == "long" else stop - entry
                if risk > 0:
                    target = entry + self.config.target_r * risk if action == "long" else entry - self.config.target_r * risk
                    signal = Signal(action, entry, stop, target, ts, "liquidity sweep plus displacement", self.config.target_r, session); self.trades += 1; self.sweep = None
            else:
                self.sweep["remaining"] -= 1
                if self.sweep["remaining"] <= 0: self.sweep = None
        self.daily.setdefault(day, [hi, lo]); self.daily[day] = [max(self.daily[day][0], hi), min(self.daily[day][1], lo)]
        self.ranges.append(max(0.0, hi-lo)); self.previous = candle; return signal
    def fit(self, data: Iterable[Any]) -> "GoldKillzoneScalp": return self
    def evaluate(self, data: Iterable[Any], costs: Any = None) -> dict[str, Any]:
        self._reset(); signals = []
        for candle in data:
            signal = self.next(candle)
            if signal: signals.append(asdict(signal))
        return {"status":"OK", "signals":signals, "count":len(signals), "costs":costs}

_DEFAULT = GoldKillzoneScalp()
def next(candle: Any) -> Signal | None: return _DEFAULT.next(candle)
