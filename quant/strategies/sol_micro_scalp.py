"""24/7 Binance-futures SOL maker-side micro-scalp; stdlib only."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

@dataclass(frozen=True)
class CostConfig:
    maker_fee_per_side: float = 0.0002
    @property
    def round_trip_fee(self) -> float:
        return 2.0 * self.maker_fee_per_side
    def fee_for_notional(self, notional: float) -> float:
        return abs(float(notional)) * self.round_trip_fee

@dataclass(frozen=True)
class Signal:
    action: str
    entry: float
    stop: float
    target: float
    timestamp: datetime
    reason: str
    risk_r: float
    hold_minutes: int
    maker_fee_per_side: float = 0.0002

@dataclass(frozen=True)
class Config:
    target_fraction: float = 0.0075
    stop_fraction: float = 0.003
    max_hold_minutes: int = 45
    min_atr_fraction: float = 0.0003
    max_abs_funding: float = 0.005
    costs: CostConfig = CostConfig()
    def __post_init__(self) -> None:
        if not 0.005 <= self.target_fraction <= 0.01:
            raise ValueError("target_fraction must be 0.005-0.01")
        if not 30 <= self.max_hold_minutes <= 45:
            raise ValueError("max_hold_minutes must be 30-45")
        if self.stop_fraction <= 0 or self.costs.maker_fee_per_side != 0.0002:
            raise ValueError("positive stop and maker fee 0.0002/side required")

def _get(c: Any, key: str, default: Any = None) -> Any:
    return c.get(key, default) if isinstance(c, Mapping) else getattr(c, key, default)

def _ts(c: Any) -> datetime:
    value = _get(c, "timestamp", _get(c, "time"))
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime):
        raise TypeError("timestamp must be datetime or ISO-8601")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

class SolMicroScalp:
    """Continuous stream: no fixed EAT session is enforced."""
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self.previous = None
        self.ranges = []
    def next(self, candle: Any) -> Signal | None:
        ts = _ts(candle)
        high, low = float(_get(candle, "high")), float(_get(candle, "low"))
        close, open_ = float(_get(candle, "close")), float(_get(candle, "open", _get(candle, "close")))
        funding = _get(candle, "funding_rate", _get(candle, "funding"))
        if funding is None or abs(float(funding)) > self.config.max_abs_funding:
            self._remember(candle, high, low)
            return None
        if any(bool(_get(candle, k, False)) for k in ("btc_dump", "btc_candle_dump", "btc_dump_flag")):
            self._remember(candle, high, low)
            return None
        explicit = _get(candle, "atr_compressed")
        atr = _get(candle, "atr")
        if atr is None:
            recent = self.ranges[-14:]
            atr = sum(recent) / len(recent) if recent else high - low
        compressed = bool(explicit) if explicit is not None else float(atr) <= close * self.config.min_atr_fraction
        previous = self.previous
        self._remember(candle, high, low)
        if compressed or previous is None:
            return None
        prev_high, prev_low = float(_get(previous, "high")), float(_get(previous, "low"))
        if close > prev_high and close > open_:
            action = "long"
        elif close < prev_low and close < open_:
            action = "short"
        else:
            return None
        entry = close
        stop = entry * (1.0 - self.config.stop_fraction) if action == "long" else entry * (1.0 + self.config.stop_fraction)
        target = entry * (1.0 + self.config.target_fraction) if action == "long" else entry * (1.0 - self.config.target_fraction)
        return Signal(action, entry, stop, target, ts, "SOL 24/7 Binance futures maker-side micro scalp", self.config.target_fraction / self.config.stop_fraction, self.config.max_hold_minutes, self.config.costs.maker_fee_per_side)
    def _remember(self, candle: Any, high: float, low: float) -> None:
        self.ranges = (self.ranges + [max(0.0, high - low)])[-100:]
        self.previous = candle
    def fit(self, data: Iterable[Any]) -> "SolMicroScalp":
        return self
    def evaluate(self, data: Iterable[Any], costs: Any = None) -> dict[str, Any]:
        self.previous, self.ranges = None, []
        signals = [s for c in data if (s := self.next(c)) is not None]
        return {"status": "OK", "signals": signals, "count": len(signals), "costs": costs or self.config.costs}

_DEFAULT = SolMicroScalp()
def next(candle: Any) -> Signal | None:
    return _DEFAULT.next(candle)
