"""SOL micro scalp; stdlib-only VWAP/EMA alignment with ATR risk."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, time, timezone
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo
EAT = ZoneInfo("Africa/Nairobi")
@dataclass(frozen=True)
class Signal:
    action: str; entry: float; stop: float; target: float; timestamp: datetime; reason: str; risk_r: float = 1.2
@dataclass(frozen=True)
class Config:
    start: time = time(15,30); end: time = time(18,0); fast_period: int = 9; slow_period: int = 21; atr_period: int = 14
    stop_atr: float = 0.8; target_r: float = 1.2; max_spread: float | None = None; max_trades_per_day: int = 3; cooldown_bars: int = 3; min_volume: float = 0.0
def _v(c: Any, key: str, default: Any = None) -> Any: return c.get(key, default) if isinstance(c, Mapping) else getattr(c, key, default)
def _ts(c: Any) -> datetime:
    value = _v(c,"timestamp")
    if isinstance(value,str): value = datetime.fromisoformat(value.replace("Z","+00:00"))
    if not isinstance(value,datetime): raise TypeError("timestamp must be datetime or ISO-8601")
    return (value if value.tzinfo else value.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
class SolMicroScalp:
    """During 15:30-18:00 EAT, trade VWAP and EMA alignment through prior-bar high/low."""
    def __init__(self, config: Config | None = None) -> None: self.config=config or Config(); self._reset()
    def _reset(self) -> None: self.day=None; self.pv=0.0; self.vol=0.0; self.fast=None; self.slow=None; self.ranges=[]; self.previous=None; self.trades=0; self.cooldown=0
    def _ema(self, old: float | None, value: float, period: int) -> float: return value if old is None else old + 2.0/(period+1.0)*(value-old)
    def next(self, candle: Any) -> Signal | None:
        ts=_ts(candle); day=ts.astimezone(EAT).date()
        if day != self.day: self.day=day; self.pv=self.vol=0.0; self.fast=self.slow=None; self.ranges=[]; self.previous=None; self.trades=0; self.cooldown=0
        hi,lo,close=float(_v(candle,"high")),float(_v(candle,"low")),float(_v(candle,"close")); volume=float(_v(candle,"volume",0.0) or 0.0); prev=self.previous
        atr=sum(self.ranges[-self.config.atr_period:])/min(len(self.ranges),self.config.atr_period) if self.ranges else 0.0; typical=(hi+lo+close)/3.0
        if volume>0: self.pv+=typical*volume; self.vol+=volume
        vwap=self.pv/self.vol if self.vol else close; fast=self._ema(self.fast,close,self.config.fast_period); slow=self._ema(self.slow,close,self.config.slow_period); spread=_v(candle,"spread"); signal=None
        if self.cooldown: self.cooldown-=1
        lt=ts.astimezone(EAT).time().replace(tzinfo=None); active=self.config.start<=lt<self.config.end; spread_ok=self.config.max_spread is None or spread is None or float(spread)<=self.config.max_spread
        if active and prev is not None and volume>=self.config.min_volume and self.trades<self.config.max_trades_per_day and not self.cooldown and spread_ok:
            distance=self.config.stop_atr*(atr if atr>0 else max(hi-lo,close*0.001))
            if close>vwap and fast>slow and close>float(_v(prev,"high")): signal=Signal("long",close,close-distance,close+self.config.target_r*distance,ts,"VWAP/EMA alignment with micro breakout",self.config.target_r)
            elif close<vwap and fast<slow and close<float(_v(prev,"low")): signal=Signal("short",close,close+distance,close-self.config.target_r*distance,ts,"VWAP/EMA alignment with micro breakout",self.config.target_r)
            if signal: self.trades+=1; self.cooldown=self.config.cooldown_bars
        self.fast,self.slow=fast,slow; self.ranges.append(max(0.0,hi-lo)); self.previous=candle; return signal
    def fit(self, data: Iterable[Any]) -> "SolMicroScalp": return self
    def evaluate(self, data: Iterable[Any], costs: Any = None) -> dict[str, Any]:
        self._reset(); signals=[]
        for candle in data:
            signal=self.next(candle)
            if signal: signals.append(asdict(signal))
        return {"status":"OK","signals":signals,"count":len(signals),"costs":costs}
_DEFAULT=SolMicroScalp()
def next(candle: Any) -> Signal | None: return _DEFAULT.next(candle)
