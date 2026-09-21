"""ORB strategy.

Order-book/DOM/tape/footprint features are candle approximations because the feed has no order book.
USEFUL: liquid 5-minute opening impulses. SKIP: thin sessions or unreliable volume.
"""
from __future__ import annotations
from typing import Any
from ._common import atr, timestamp, value

def _v(c: Any, k: str, d: Any = 0) -> Any:
    return value(c, k, d)

class ORB_Range:
    """First three five-minute bars; breakout close; opposite-side/session stop and 1.5R."""
    def __init__(self, opening_bars: int = 3, reward_risk: float = 1.5, atr_period: int = 14,
                 session_start_hour: int = 0, session_end_hour: int = 24,
                 use_volume_filter: bool = False, volume_lookback: int = 20,
                 volume_multiple: float = 1.0) -> None:
        if opening_bars < 1 or reward_risk <= 0 or atr_period < 1: raise ValueError("invalid ORB parameters")
        self.n, self.rr, self.ap = opening_bars, float(reward_risk), atr_period
        self.sh, self.eh, self.vf, self.vn, self.vm = session_start_hour, session_end_hour, use_volume_filter, volume_lookback, volume_multiple
        self.day = None; self.opening: list[tuple[int, Any]] = []; self.h = self.l = None; self.hist: list[Any] = []; self.active = None; self.traded = False
    def _reset(self, day: Any) -> None:
        self.day, self.opening, self.h, self.l, self.active, self.traded = day, [], None, None, None, False
    def _manage(self, c: Any, ts: Any) -> dict[str, Any]:
        if self.active is None: return {"action": "hold"}
        a = self.active; hi, lo = float(_v(c, "high")), float(_v(c, "low"))
        hit = lo <= a["stop"] or hi >= a["target"] if a["side"] == "long" else hi >= a["stop"] or lo <= a["target"]
        if hit or ts.hour >= self.eh: self.active = None; return {"action": "exit", "reason": "stop_target_or_session_end"}
        return {"action": "hold"}
    def next(self, candle: Any) -> dict[str, Any]:
        ts = timestamp(candle)
        if self.day != ts.date(): self._reset(ts.date())
        if self.active is not None:
            out = self._manage(candle, ts); self.hist.append(candle); return out
        self.hist.append(candle)
        if not self.sh <= ts.hour < self.eh or self.traded: return {"action": "hold"}
        bucket = int(ts.timestamp() // 300)
        if len(self.opening) < self.n and (not self.opening or bucket != self.opening[-1][0]):
            self.opening.append((bucket, candle)); hi, lo = float(_v(candle, "high")), float(_v(candle, "low")); self.h = hi if self.h is None else max(self.h, hi); self.l = lo if self.l is None else min(self.l, lo); return {"action": "hold"}
        if len(self.opening) < self.n: return {"action": "hold"}
        if self.vf:
            recent = self.hist[-self.vn:]; avg = sum(float(_v(x, "volume")) for x in recent) / len(recent) if recent else 0
            if avg and float(_v(candle, "volume")) < avg * self.vm: return {"action": "hold"}
        close = float(_v(candle, "close")); side = "long" if close > self.h else "short" if close < self.l else None
        if side is None: return {"action": "hold"}
        stop = self.l if side == "long" else self.h; risk = close - stop if side == "long" else stop - close
        if risk <= 0: return {"action": "hold"}
        target = close + self.rr * risk if side == "long" else close - self.rr * risk; self.active = {"side": side, "stop": stop, "target": target}; self.traded = True
        return {"action": "enter", "side": side, "stop": stop, "target": target, "reason": "three_bar_opening_range_breakout", "atr14": atr(self.hist, self.ap)}

__all__ = ["ORB_Range"]
