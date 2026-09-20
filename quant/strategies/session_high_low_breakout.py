"""Session high/low breakout tracks the running 09:00-16:00 EAT range and trades one break per day, capped at 45 minutes. It tests liquid daytime expansion; a range can be stale, and the EAT filter excludes valid overnight behavior."""
from ._common import ResearchStrategy, atr, eat_clock, value
class SessionHighLowBreakout(ResearchStrategy):
    def __init__(self): super().__init__(); self.day=self.sh=self.sl=None; self.traded=False
    def next(self,c):
        if (out:=self._step(c)) is not None:return out
        day,minute=eat_clock(c)
        if day!=self.day:self.day,self.sh,self.sl,self.traded=day,None,None,False
        close,h,l=float(value(c,"close")),float(value(c,"high")),float(value(c,"low")); signal=None
        if 540<=minute<=960:
            oldh,oldl=self.sh,self.sl
            if not self.traded and atr(self.bars) and oldh is not None:
                vol=atr(self.bars)
                if close>oldh:self.traded=True; signal=self._enter(c,"long",close-vol,close+1.4*vol,"EAT session high break")
                elif close<oldl:self.traded=True; signal=self._enter(c,"short",close+vol,close-1.4*vol,"EAT session low break")
            self.sh=h if self.sh is None else max(self.sh,h); self.sl=l if self.sl is None else min(self.sl,l)
        return self._finish(c,signal)
