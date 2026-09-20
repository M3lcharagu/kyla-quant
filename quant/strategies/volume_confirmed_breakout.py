"""Volume-confirmed breakout requires a 12-bar channel break and volume above 1.5 times its prior 20-bar mean, with ATR exits and a 45-minute cap. It rejects quiet noise; venue-specific volume and one-off prints can still give false confirmation."""
from ._common import ResearchStrategy, atr, channel, value, vol_avg
class VolumeConfirmedBreakout(ResearchStrategy):
    def next(self,c):
        if (out:=self._step(c)) is not None:return out
        close,volume=float(value(c,"close")),float(value(c,"volume",0) or 0); vol,avg=atr(self.bars),vol_avg(self.bars,20); hi,lo=channel(self.bars,12,"high"),channel(self.bars,12,"low"); signal=None
        if vol and avg and volume>1.5*avg:
            if hi is not None and close>hi: signal=self._enter(c,"long",close-.8*vol,close+1.6*vol,"volume high break")
            elif lo is not None and close<lo: signal=self._enter(c,"short",close+.8*vol,close-1.6*vol,"volume low break")
        return self._finish(c,signal)
