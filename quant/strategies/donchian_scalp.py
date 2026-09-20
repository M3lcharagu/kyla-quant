"""Donchian scalp enters a 20-bar channel break with a tighter 0.7-ATR stop and 1.2-ATR target, capped at 45 minutes. It is a compact trend-following baseline; narrow channels invite noise and the tight stop is vulnerable to wick reversals."""
from ._common import ResearchStrategy, atr, channel, value
class DonchianScalp(ResearchStrategy):
    def next(self,c):
        if (out:=self._step(c)) is not None:return out
        close,vol=float(value(c,"close")),atr(self.bars); hi,lo=channel(self.bars,20,"high"),channel(self.bars,20,"low"); signal=None
        if vol and hi is not None and close>hi: signal=self._enter(c,"long",close-.7*vol,close+1.2*vol,"20-bar Donchian high")
        elif vol and lo is not None and close<lo: signal=self._enter(c,"short",close+.7*vol,close-1.2*vol,"20-bar Donchian low")
        return self._finish(c,signal)
