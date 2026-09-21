"""Candle delta momentum proxy.

Order-book/DOM/tape/footprint features are candle approximations because the feed has no order book.
USEFUL: liquid markets with robust range and volume. SKIP: zero-range candles or when true bid/ask delta is required.
"""
from __future__ import annotations
from typing import Any
from ._common import value

def _f(c: Any, k: str, d: float = 0.0) -> float: return float(value(c, k, d) or d)

class DeepGamma_Delta:
    """Candle delta=(close-open)/(high-low)*volume; K-bar cross, swing stop, 1.5R/reversal."""
    def __init__(self, k_bars: int = 3, momentum_threshold: float = .20, local_lookback: int = 5, swing_lookback: int = 5, reward_risk: float = 1.5, reversal_threshold: float = .05) -> None:
        self.k, self.th, self.lb, self.sb, self.rr, self.rev = k_bars, momentum_threshold, local_lookback, swing_lookback, reward_risk, reversal_threshold; self.bars = []; self.prev = None; self.active = None
    def _delta(self, c: Any) -> float:
        r = _f(c, "high") - _f(c, "low"); return (_f(c, "close") - _f(c, "open")) / r * _f(c, "volume") if r > 0 else 0
    def _mom(self) -> float:
        b = self.bars[-self.k:]; v = sum(_f(x, "volume") for x in b); return sum(self._delta(x) for x in b) / v if v else 0
    def next(self, candle: Any) -> dict[str, Any]:
        self.bars.append(candle); self.bars = self.bars[-max(100, self.k + self.lb) :]; mom = self._mom()
        if self.active:
            a = self.active; hi, lo = _f(candle, "high"), _f(candle, "low"); hit = lo <= a["stop"] or hi >= a["target"] if a["side"] == "long" else hi >= a["stop"] or lo <= a["target"]; reverse = mom < -self.rev if a["side"] == "long" else mom > self.rev
            self.prev = mom
            if hit or reverse: self.active = None; return {"action": "exit", "reason": "swing_stop_target_or_momentum_reversal"}
            return {"action": "hold"}
        if len(self.bars) < max(self.k + self.lb, self.sb + 1): self.prev = mom; return {"action": "hold"}
        prior = self.prev if self.prev is not None else 0; prior_bars = self.bars[-self.lb-1:-1]; close = _f(candle, "close"); long = prior <= self.th < mom and close > max(_f(x, "high") for x in prior_bars); short = prior >= -self.th > mom and close < min(_f(x, "low") for x in prior_bars); self.prev = mom
        if not (long or short): return {"action": "hold"}
        side = "long" if long else "short"; swing = self.bars[-self.sb:]; stop = min(_f(x, "low") for x in swing) if long else max(_f(x, "high") for x in swing); risk = close - stop if long else stop - close
        if risk <= 0: return {"action": "hold"}
        target = close + self.rr * risk if long else close - self.rr * risk; self.active = {"side": side, "stop": stop, "target": target}
        return {"action": "enter", "side": side, "stop": stop, "target": target, "reason": "K_bar_candle_delta_momentum_cross", "delta_momentum": mom}

__all__ = ["DeepGamma_Delta"]
