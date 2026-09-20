"""Tiny stdlib-only indicators and position state for research strategies."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional
EAT = timezone(timedelta(hours=3))

def value(c: Any, key: str, default=None):
    return c.get(key, default) if isinstance(c, dict) else getattr(c, key, default)

def timestamp(c: Any) -> datetime:
    raw = value(c, "timestamp", value(c, "time"))
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(raw / 1000 if raw > 10_000_000_000 else raw, timezone.utc)
    out = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    return out if out.tzinfo else out.replace(tzinfo=timezone.utc)

def closes(bars: List[Any], n: int):
    return [float(value(x, "close")) for x in bars[-n:]]

def ema(bars: List[Any], n: int) -> Optional[float]:
    vals = closes(bars, n)
    if len(vals) < n: return None
    out, alpha = sum(vals[:n]) / n, 2.0 / (n + 1)
    for x in vals[n:]: out = alpha * x + (1 - alpha) * out
    return out

def atr(bars: List[Any], n=14) -> Optional[float]:
    if len(bars) < n + 1: return None
    out = []
    for i in range(len(bars) - n, len(bars)):
        h, l = float(value(bars[i], "high")), float(value(bars[i], "low"))
        pc = float(value(bars[i - 1], "close"))
        out.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(out) / n

def channel(bars: List[Any], n: int, key: str):
    vals = [float(value(x, key)) for x in bars[-n:]]
    return (max(vals) if key == "high" else min(vals)) if len(vals) == n else None

def vol_avg(bars: List[Any], n: int):
    vals = [float(value(x, "volume", 0) or 0) for x in bars[-n:]]
    return sum(vals) / n if len(vals) == n else None

def eat_clock(c):
    t = timestamp(c).astimezone(EAT)
    return t.date(), t.hour * 60 + t.minute

class ResearchStrategy:
    max_hold_minutes = 45
    def __init__(self): self.bars, self.active = [], None
    def _manage(self, c):
        if self.active is None: return None
        h, l, a = float(value(c, "high")), float(value(c, "low")), self.active
        hit = (l <= a["stop"] or h >= a["target"]) if a["side"] == "long" else (h >= a["stop"] or l <= a["target"])
        if hit or timestamp(c) - a["time"] >= timedelta(minutes=self.max_hold_minutes):
            self.active = None
            return {"action": "exit"}
        return {"action": "hold"}
    def _enter(self, c, side, stop, target, reason):
        self.active = {"side": side, "stop": stop, "target": target, "time": timestamp(c)}
        return {"action": "enter", "side": side, "stop": stop, "target": target, "quantity": 1.0, "reason": reason}
    def _finish(self, c, signal=None):
        self.bars.append(c); self.bars = self.bars[-120:]
        return signal
    def _step(self, c):
        out = self._manage(c)
        return self._finish(c, out) if out is not None else None
