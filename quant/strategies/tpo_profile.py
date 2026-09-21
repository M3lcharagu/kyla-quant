"""TPO profile candle proxy.

Order-book/DOM/tape/footprint features are candle approximations because the feed has no order book.
USEFUL: liquid 5-minute auctions. SKIP: thin/fragmented sessions or missing timestamps.
"""
from __future__ import annotations
from typing import Any
from ._common import timestamp, value

def _f(c: Any, k: str, d: float = 0.0) -> float: return float(value(c, k, d) or d)

class TPO_Profile:
    """After two hours, break a 70%% close-price TPO value area."""
    def __init__(self, bars_before_profile: int = 24, value_area: float = .70, bucket_size: float = .5, reward_risk: float = 1.5) -> None:
        if bars_before_profile < 1 or not 0 < value_area < 1 or bucket_size <= 0 or reward_risk <= 0: raise ValueError("invalid TPO parameters")
        self.n, self.va, self.bs, self.rr = bars_before_profile, value_area, bucket_size, reward_risk; self.day = None; self.bars = []; self.prev = None; self.active = None; self.traded = False
    def _profile(self) -> tuple[float, float, float] | None:
        if len(self.bars) < self.n: return None
        counts = {}
        for c in self.bars:
            k = round(_f(c, "close") / self.bs); counts[k] = counts.get(k, 0) + 1
        poc = max(counts, key=counts.get); need = max(1, int(len(self.bars) * self.va + .999)); included = {poc}; total = counts[poc]
        while total < need and len(included) < len(counts):
            k = max((x for x in counts if x not in included), key=counts.get); included.add(k); total += counts[k]
        return poc * self.bs, min(included) * self.bs, max(included) * self.bs
    def _manage(self, c: Any) -> dict[str, Any] | None:
        if not self.active: return None
        a = self.active; hi, lo = _f(c, "high"), _f(c, "low"); hit = lo <= a["stop"] or hi >= a["target"] if a["side"] == "long" else hi >= a["stop"] or lo <= a["target"]
        if hit: self.active = None; return {"action": "exit", "reason": "TPO_mid_value_or_opposite_extreme"}
        return {"action": "hold"}
    def next(self, candle: Any) -> dict[str, Any]:
        ts = timestamp(candle)
        if self.day != ts.date(): self.day = ts.date(); self.bars = []; self.prev = None; self.active = None; self.traded = False
        managed = self._manage(candle); self.bars.append(candle)
        if managed is not None: return managed
        p, close, prev = self._profile(), _f(candle, "close"), self.prev; self.prev = close
        if not p or prev is None or self.traded: return {"action": "hold"}
        mid, val, vah = p; side = "long" if prev <= vah < close else "short" if prev >= val > close else None
        if not side: return {"action": "hold"}
        stop = mid; extreme = max(_f(x, "high") for x in self.bars) if side == "long" else min(_f(x, "low") for x in self.bars); risk = close - stop if side == "long" else stop - close
        target = extreme if (extreme > close if side == "long" else extreme < close) else (close + self.rr * risk if side == "long" else close - self.rr * risk)
        if risk <= 0: return {"action": "hold"}
        self.active = {"side": side, "stop": stop, "target": target}; self.traded = True
        return {"action": "enter", "side": side, "stop": stop, "target": target, "reason": "70_percent_TPO_value_area_breakout", "poc": mid, "val": val, "vah": vah}

__all__ = ["TPO_Profile"]
