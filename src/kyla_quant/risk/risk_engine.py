"""Risk controls: fixed sizing, limits, cooldown, news lock, and kill switch."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class RiskConfig:
    risk_per_trade_fraction: float = 0.0025
    max_daily_loss_fraction: float = 0.01
    max_trades_per_day: int = 3
    cooldown_minutes: int = 30
    funded_account_default: bool = True
    no_martingale: bool = True


@dataclass
class RiskState:
    daily_loss_fraction: float = 0.0
    trades_today: int = 0
    last_trade_at: datetime | None = None
    news_lock: bool = False
    kill_switch: bool = False


class RiskEngine:
    def __init__(self, config: RiskConfig | None = None) -> None:
        self.config = config or RiskConfig()
        self.state = RiskState()
        if not self.config.no_martingale:
            raise ValueError("martingale is prohibited")

    def position_size(self, equity: float, stop_distance: float, point_value: float = 1.0) -> float:
        if equity <= 0 or stop_distance <= 0 or point_value <= 0:
            raise ValueError("equity, stop distance, and point value must be positive")
        return equity * self.config.risk_per_trade_fraction / (stop_distance * point_value)

    def can_trade(self, now: datetime | None = None) -> tuple[bool, str]:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        if self.state.kill_switch:
            return False, "manual kill switch"
        if self.state.news_lock:
            return False, "news lock"
        if self.state.daily_loss_fraction >= self.config.max_daily_loss_fraction:
            return False, "max daily loss"
        if self.state.trades_today >= self.config.max_trades_per_day:
            return False, "max trades per day"
        if self.state.last_trade_at and now - self.state.last_trade_at < timedelta(minutes=self.config.cooldown_minutes):
            return False, "cooldown"
        return True, "allowed"

    def record_trade(self, realized_loss_fraction: float = 0.0, now: datetime | None = None) -> None:
        if realized_loss_fraction < 0:
            self.state.daily_loss_fraction += abs(realized_loss_fraction)
        self.state.trades_today += 1
        self.state.last_trade_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    def set_kill_switch(self, enabled: bool = True) -> None:
        self.state.kill_switch = enabled
