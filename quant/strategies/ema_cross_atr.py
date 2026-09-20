"""EMA-cross trend enters an 8/21 cross with a one-ATR stop, two-ATR target, and 45-minute cap. It tests clean directional runs; lag and whipsaw around a flat crossover are expected failure modes."""
from ._common import ResearchStrategy, atr, ema, value
class EMACrossATR(ResearchStrategy):
    def next(self,c):
        if (out:=self._step(c)) is not None:return out
        before=(ema(self.bars,8),ema(self.bars,21)); now=self.bars+[c]; fast,slow,vol=ema(now,8),ema(now,21),atr(self.bars); close=float(value(c,"close")); signal=None
        if None not in before+(fast,slow,vol):
            if before[0]<=before[1] and fast>slow: signal=self._enter(c,"long",close-vol,close+2*vol,"8/21 bullish cross")
            elif before[0]>=before[1] and fast<slow: signal=self._enter(c,"short",close+vol,close-2*vol,"8/21 bearish cross")
        return self._finish(c,signal)
