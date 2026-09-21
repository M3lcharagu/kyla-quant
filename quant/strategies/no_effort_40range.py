"""No-effort 40-range candle proxy.

Order-book/DOM/tape/footprint features are candle approximations because the feed has no order book.
USEFUL: compressed opens followed by low-volume expansion. SKIP: unreliable volume or non-intraday data.
"""
from __future__ import annotations
from typing import Any
from ._common import atr, timestamp, value

def _f(c: Any, k: str, d: float = 0.0) -> float: return float(value(c, k, d) or d)

class NoEffort_40Range:
    """Opening range below .35 ATR14, low-volume breakout, edge stop and 2R/trailing."""
    def __init__(self, opening_bars: int = 3, atr_period: int = 14, max_range_atr: float = .35, volume_lookback: int = 20, reward_risk: float = 2.0, trailing_lookback: int = 3) -> None:
        self.n, self.ap, self.maxr, self.vn, self.rr, self.tn = opening_bars, atr_period, max_range_atr, volume_lookback, reward_risk, trailing_lookback; self.day = None; self.opening = []; self.h = self.l = None; self.hist = []; self.active = None; self.traded = False
    def _manage(self, c: Any) -> dict[str, Any] | None:
        if not self.active: return None
        a = self.active; hi, lo = _f(c, "high"), _f(c, "low")
        hit = lo <= a["stop"] or hi >= a["target"] if a["side"] == "long" else hi >= a["stop"] or lo <= a["target"]
        if hit: self.active = None; return {"action": "exit", "reason": "range_stop_or_2R"}
        if a["side"] == "long" and hi >= a["entry"] + a["risk"]: a["stop"] = max(a["stop"], min(_f(x, "low") for x in self.hist[-self.tn:]))
        if a["side"] == "short" and lo <= a["entry"] - a["risk"]: a["stop"] = min(a["stop"], max(_f(x, "high") for x in self.hist[-self.tn:]))
        return {"action": "hold"}
    def next(self, candle: Any) -> dict[str, Any]:
        ts = timestamp(candle)
        if self.day != ts.date(): self.day = ts.date(); self.opening = []; self.h = self.l = None; self.active = None; self.traded = False
        managed = self._manage(candle); self.hist.append(candle)
        if managed is not None: return managed
        bucket = int(ts.timestamp() // 300)
        if len(self.opening) < self.n and (not self.opening or bucket != self.opening[-1][0]):
            self.opening.append((bucket, candle)); hi, lo = _f(candle, "high"), _f(candle, "low"); self.h = hi if self.h is None else max(self.h, hi); self.l = lo if self.l is None else min(self.l, lo); return {"action": "hold"}
        if len(self.opening) < self.n or self.traded: return {"action": "hold"}
        a = atr(self.hist[:-1], self.ap); width = self.h - self.l
        if a is None or width <= 0 or width >= self.maxr * a: return {"action": "hold"}
        vs = [_f(x, "volume") for x in self.hist[-self.vn:]]; avg = sum(vs) / len(vs) if vs else 0
        if not avg or _f(candle, "volume") >= avg: return {"action": "hold"}
        close, hi, lo = _f(candle, "close"), _f(candle, "high"), _f(candle, "low"); loc = (close - lo) / (hi - lo) if hi > lo else .5; side = "long" if close > self.h and loc >= .7 else "short" if close < self.l and loc <= .3 else None
        if not side: return {"action": "hold"}
        stop = self.l if side == "long" else self.h; risk = close - stop if side == "long" else stop - close
        if risk <= 0: return {"action": "hold"}
        target = close + self.rr * risk if side == "long" else close - self.rr * risk; self.active = {"side": side, "entry": close, "stop": stop, "target": target, "risk": risk}; self.traded = True
        return {"action": "enter", "side": side, "stop": stop, "target": target, "reason": "no_effort_low_volume_breakout", "opening_range_atr": width / a}

__all__ = ["NoEffort_40Range"]
