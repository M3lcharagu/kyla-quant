"""Candle volume-profile imbalance proxy.

Order-book/DOM/tape/footprint features are candle approximations because the feed has no order book.
USEFUL: liquid sessions with dependable volume. SKIP: thin markets or zero/misleading volume.
"""
from __future__ import annotations
from typing import Any
from ._common import timestamp, value

def _f(c: Any, k: str, d: float = 0.0) -> float: return float(value(c, k, d) or d)

class VolumeProfile_Imbalance:
    """Rolling two-session 20-bucket candle volume profile, POC cross and LVN/RR target."""
    def __init__(self, buckets: int = 20, sessions: int = 2, volume_lookback: int = 20, swing_lookback: int = 5, reward_risk: float = 1.5, above_average_multiple: float = 1.0) -> None:
        if buckets < 5 or sessions < 1 or reward_risk <= 0: raise ValueError("invalid profile parameters")
        self.n, self.ns, self.vn, self.sn, self.rr, self.vm = buckets, sessions, volume_lookback, swing_lookback, reward_risk, above_average_multiple
        self.day = None; self.cur: list[Any] = []; self.done: list[list[Any]] = []; self.hist: list[Any] = []; self.prev = None; self.active = None; self.traded = None
    def _profile(self) -> tuple[float, float, float, float, int] | None:
        bars = [x for s in self.done[-self.ns:] for x in s]
        if not bars: return None
        lo, hi = min(_f(x, "low") for x in bars), max(_f(x, "high") for x in bars); w = (hi - lo) / self.n or 1e-12; p = [0.0] * self.n
        for x in bars: p[min(self.n - 1, max(0, int((_f(x, "close") - lo) / w)))] += _f(x, "volume")
        pi = max(range(self.n), key=p.__getitem__); ordered = sorted(p); lv = ordered[len(p) // 4]; lvn = min((i for i, x in enumerate(p) if x <= lv), key=lambda i: abs(i - pi), default=pi)
        return lo + (pi + .5) * w, lo, hi, w, lvn
    def _manage(self, c: Any) -> dict[str, Any] | None:
        if not self.active: return None
        a = self.active; hi, lo = _f(c, "high"), _f(c, "low"); hit = lo <= a["stop"] or hi >= a["target"] if a["side"] == "long" else hi >= a["stop"] or lo <= a["target"]
        if hit: self.active = None; return {"action": "exit", "reason": "swing_stop_or_profile_target"}
        return {"action": "hold"}
    def next(self, candle: Any) -> dict[str, Any]:
        ts = timestamp(candle); day = ts.date()
        if self.day is None: self.day = day
        if day != self.day:
            if self.cur: self.done.append(self.cur)
            self.done = self.done[-self.ns:]; self.cur = []; self.day = day; self.traded = None
        managed = self._manage(candle); self.cur.append(candle); self.hist.append(candle)
        if managed is not None: return managed
        prof, close, prev = self._profile(), _f(candle, "close"), self.prev; self.prev = close
        if not prof or prev is None or self.traded == day: return {"action": "hold"}
        poc, lo, hi, w, li = prof; vs = [_f(x, "volume") for x in self.hist[-self.vn:]]; avg = sum(vs) / len(vs) if vs else 0
        if avg <= 0 or _f(candle, "volume") <= avg * self.vm: return {"action": "hold"}
        side = "long" if prev <= poc < close else "short" if prev >= poc > close else None
        if side is None: return {"action": "hold"}
        swings = self.hist[-self.sn:]; stop = min(_f(x, "low") for x in swings) if side == "long" else max(_f(x, "high") for x in swings); risk = close - stop if side == "long" else stop - close
        if risk <= 0: return {"action": "hold"}
        lvn = lo + (li + .5) * w; target = lvn if (lvn > close if side == "long" else lvn < close) else (close + self.rr * risk if side == "long" else close - self.rr * risk)
        if target <= close if side == "long" else target >= close: target = close + self.rr * risk if side == "long" else close - self.rr * risk
        self.active = {"side": side, "stop": stop, "target": target}; self.traded = day
        return {"action": "enter", "side": side, "stop": stop, "target": target, "reason": "above_average_volume_poc_cross", "poc": poc, "lvn": lvn}

__all__ = ["VolumeProfile_Imbalance"]
