"""Momentum breakout clears the prior 12-bar high/low and uses an ATR stop/target, with a 45-minute cap. It tests directional expansion; choppy ranges, gaps, and OHLC intrabar ambiguity can create false breaks."""
from ._common import ResearchStrategy, atr, channel, value
class MomentumBreakout(ResearchStrategy):
    def next(self, c):
        if (out := self._step(c)) is not None: return out
        close, vol = float(value(c, "close")), atr(self.bars)
        hi, lo, signal = channel(self.bars, 12, "high"), channel(self.bars, 12, "low"), None
        if vol and hi is not None and close > hi: signal = self._enter(c, "long", close-.8*vol, close+1.5*vol, "12-bar high break")
        elif vol and lo is not None and close < lo: signal = self._enter(c, "short", close+.8*vol, close-1.5*vol, "12-bar low break")
        return self._finish(c, signal)
