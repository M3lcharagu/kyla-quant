"""Opening-range breakout builds 09:00-09:15 EAT and takes one late-morning break, capped at 45 minutes. It tests session-open expansion; a news spike can make the range too wide and the entry too late."""
from ._common import ResearchStrategy, atr, eat_clock, value
class OpeningRangeBreakout(ResearchStrategy):
    def __init__(self): super().__init__(); self.day=self.rh=self.rl=None; self.traded=False
    def next(self, c):
        if (out := self._step(c)) is not None: return out
        day, minute = eat_clock(c)
        if day != self.day: self.day,self.rh,self.rl,self.traded=day,None,None,False
        h,l,close=float(value(c,"high")),float(value(c,"low")),float(value(c,"close"))
        if 540 <= minute < 555:
            self.rh=h if self.rh is None else max(self.rh,h); self.rl=l if self.rl is None else min(self.rl,l)
            return self._finish(c)
        vol,signal=atr(self.bars),None
        if not self.traded and vol and self.rh is not None and 555 <= minute < 720:
            if close > self.rh: self.traded=True; signal=self._enter(c,"long",close-vol,close+1.5*vol,"opening-range high")
            elif close < self.rl: self.traded=True; signal=self._enter(c,"short",close+vol,close-1.5*vol,"opening-range low")
        return self._finish(c,signal)
