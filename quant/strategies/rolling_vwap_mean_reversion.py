"""Rolling VWAP-ish mean reversion fades a one-ATR excursion from a 24-bar volume-weighted typical-price mean, capped at 45 minutes. It tests rotation; persistent trends can stay far from VWAP and punish contrarian entries."""
from ._common import ResearchStrategy, atr, value
class RollingVWAPMeanReversion(ResearchStrategy):
    def next(self,c):
        if (out:=self._step(c)) is not None:return out
        vol,signal=atr(self.bars),None
        if vol and len(self.bars)>=24:
            w=self.bars[-24:]; qty=sum(float(value(x,"volume",0) or 0) for x in w)
            vwap=sum(((float(value(x,"high"))+float(value(x,"low"))+float(value(x,"close")))/3)*float(value(x,"volume",0) or 0) for x in w)/qty if qty else None
            close,op=float(value(c,"close")),float(value(c,"open"))
            if vwap is not None and close<vwap-.8*vol and close>op: signal=self._enter(c,"long",close-vol,vwap,"VWAP-ish downside excursion")
            elif vwap is not None and close>vwap+.8*vol and close<op: signal=self._enter(c,"short",close+vol,vwap,"VWAP-ish upside excursion")
        return self._finish(c,signal)
