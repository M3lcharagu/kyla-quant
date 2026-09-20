"""RSI(2) reversal buys an oversold up-close or shorts an overbought down-close with an ATR envelope and 45-minute cap. It tests short-term snapback; RSI can remain extreme in a strong trend and the tiny sample is outlier-sensitive."""
from ._common import ResearchStrategy, atr, closes, value
def rsi2(v):
    if len(v)<3:return None
    d=[v[i]-v[i-1] for i in range(1,len(v))]; g=sum(max(x,0) for x in d); l=sum(max(-x,0) for x in d)
    return 100 if l==0 else 100-100/(1+g/l)
class RSI2Reversal(ResearchStrategy):
    def next(self,c):
        if (out:=self._step(c)) is not None:return out
        vol,ind=atr(self.bars),rsi2(closes(self.bars+[c],3)); close,op=float(value(c,"close")),float(value(c,"open")); signal=None
        if vol and ind is not None and ind<10 and close>op: signal=self._enter(c,"long",close-.8*vol,close+vol,"RSI(2) oversold turn")
        elif vol and ind is not None and ind>90 and close<op: signal=self._enter(c,"short",close+.8*vol,close-vol,"RSI(2) overbought turn")
        return self._finish(c,signal)
