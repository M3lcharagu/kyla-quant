"""Small, dependency-free, event-driven candle backtester."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, Union


@dataclass(frozen=True)
class Candle:
    """One OHLCV event delivered to a strategy."""

    timestamp: Any
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class Strategy:
    """Strategy interface; return a signal from ``next(candle)``."""

    def next(self, candle: Candle) -> Any:
        raise NotImplementedError


@dataclass(frozen=True)
class Trade:
    side: str
    quantity: float
    entry_timestamp: Any
    exit_timestamp: Any
    entry_price: float
    exit_price: float
    gross_pnl: float
    costs: float
    pnl: float
    r_multiple: float
    exit_reason: str

    @property
    def net_pnl(self) -> float:
        return self.pnl

    @property
    def profit(self) -> float:
        return self.pnl


@dataclass
class BacktestResult:
    equity_curve: List[float]
    trades: List[Trade]
    metrics: Dict[str, Any]

    @property
    def final_equity(self) -> float:
        return self.equity_curve[-1] if self.equity_curve else 0.0


@dataclass
class _Position:
    side: str
    quantity: float
    entry_timestamp: Any
    entry_raw_price: float
    entry_price: float
    entry_cost: float
    stop: Optional[float]
    target: Optional[float]
    risk_amount: float


CandleLike = Union[Candle, Mapping[str, Any]]


class Backtester:
    """Run one strategy over candles with conservative, explicit execution rules.

    Signals may be ``"exit"``/``"hold"`` or mappings such as
    ``{"action": "enter", "side": "long", "stop": 99, "target": 103}``.
    Entries and signal exits fill at the candle close. Protective stops and
    targets are checked against the next candles' OHLC before the strategy is
    called; if both trigger in one candle, the stop wins.

    ``spread`` and ``slippage`` are price units per side. ``commission`` is a
    price-unit commission per unit per side, while ``commission_rate`` is an
    optional notional percentage expressed as a decimal (0.001 = 0.1%).
    """

    def __init__(
        self,
        strategy: Strategy,
        initial_capital: float = 10_000.0,
        spread: float = 0.0,
        slippage: float = 0.0,
        commission: float = 0.0,
        commission_rate: float = 0.0,
        quantity: float = 1.0,
        min_trades: int = 200,
    ) -> None:
        if initial_capital <= 0 or quantity <= 0:
            raise ValueError("initial_capital and quantity must be positive")
        if any(value < 0 for value in (spread, slippage, commission, commission_rate)):
            raise ValueError("cost parameters cannot be negative")
        if min_trades < 0:
            raise ValueError("min_trades cannot be negative")
        self.strategy = strategy
        self.initial_capital = float(initial_capital)
        self.spread = float(spread)
        self.slippage = float(slippage)
        self.commission = float(commission)
        self.commission_rate = float(commission_rate)
        self.quantity = float(quantity)
        self.min_trades = int(min_trades)

    def run(self, candles: Iterable[CandleLike]) -> BacktestResult:
        bars = [self._candle(item) for item in candles]
        equity: List[float] = []
        trades: List[Trade] = []
        position: Optional[_Position] = None
        cash = self.initial_capital

        for candle in bars:
            if position is not None:
                stop_hit = self._protective_exit(candle, position)
                if stop_hit is not None:
                    raw_price, reason = stop_hit
                    trade, cash = self._close(position, candle, raw_price, reason, cash)
                    trades.append(trade)
                    position = None

            signal = self._signal(self.strategy.next(candle))
            action = signal["action"]
            side = signal.get("side")

            if action == "exit" and position is not None:
                trade, cash = self._close(position, candle, candle.close, "signal", cash)
                trades.append(trade)
                position = None
            elif action == "enter" and side in ("long", "short"):
                if position is not None and position.side != side:
                    trade, cash = self._close(position, candle, candle.close, "reverse", cash)
                    trades.append(trade)
                    position = None
                if position is None:
                    position, cash = self._open(candle, side, signal, cash)
                else:
                    if "stop" in signal:
                        position.stop = signal["stop"]
                    if "target" in signal:
                        position.target = signal["target"]

            marked = cash
            if position is not None:
                sign = 1.0 if position.side == "long" else -1.0
                marked += sign * (candle.close - position.entry_raw_price) * position.quantity
            equity.append(marked)

        if position is not None and bars:
            trade, cash = self._close(position, bars[-1], bars[-1].close, "end", cash)
            trades.append(trade)
            equity[-1] = cash

        return BacktestResult(equity, trades, self._metrics(trades, equity))

    def _open(
        self,
        candle: Candle,
        side: str,
        signal: Mapping[str, Any],
        cash: float,
    ) -> Tuple[_Position, float]:
        quantity = float(signal.get("quantity", signal.get("size", self.quantity)))
        if quantity <= 0:
            raise ValueError("signal quantity must be positive")
        raw = float(candle.close)
        price = self._execution_price(raw, side, entering=True)
        entry_cost = self._cost(raw, price, quantity)
        stop = self._number(signal.get("stop"))
        target = self._number(signal.get("target"))
        risk = abs(raw - stop) * quantity if stop is not None and raw != stop else 1.0
        return (
            _Position(side, quantity, candle.timestamp, raw, price, entry_cost, stop, target, risk),
            cash - entry_cost,
        )

    def _close(
        self,
        position: _Position,
        candle: Candle,
        raw_price: float,
        reason: str,
        cash: float,
    ) -> Tuple[Trade, float]:
        raw_price = float(raw_price)
        exit_price = self._execution_price(raw_price, position.side, entering=False)
        exit_cost = self._cost(raw_price, exit_price, position.quantity)
        sign = 1.0 if position.side == "long" else -1.0
        gross = sign * (raw_price - position.entry_raw_price) * position.quantity
        costs = position.entry_cost + exit_cost
        pnl = gross - costs
        trade = Trade(
            position.side,
            position.quantity,
            position.entry_timestamp,
            candle.timestamp,
            position.entry_price,
            exit_price,
            gross,
            costs,
            pnl,
            pnl / position.risk_amount,
            reason,
        )
        return trade, cash + gross - exit_cost

    def _protective_exit(
        self, candle: Candle, position: _Position
    ) -> Optional[Tuple[float, str]]:
        if position.side == "long":
            if position.stop is not None:
                if candle.open <= position.stop:
                    return candle.open, "stop"
                if candle.low <= position.stop:
                    return position.stop, "stop"
            if position.target is not None:
                if candle.open >= position.target:
                    return candle.open, "target"
                if candle.high >= position.target:
                    return position.target, "target"
        else:
            if position.stop is not None:
                if candle.open >= position.stop:
                    return candle.open, "stop"
                if candle.high >= position.stop:
                    return position.stop, "stop"
            if position.target is not None:
                if candle.open <= position.target:
                    return candle.open, "target"
                if candle.low <= position.target:
                    return position.target, "target"
        return None

    def _execution_price(self, raw: float, side: str, entering: bool) -> float:
        impact = self.spread / 2.0 + self.slippage
        buy = (side == "long" and entering) or (side == "short" and not entering)
        return raw + impact if buy else raw - impact

    def _cost(self, raw: float, executed: float, quantity: float) -> float:
        return abs(executed - raw) * quantity + self.commission * quantity + abs(raw * quantity) * self.commission_rate

    @staticmethod
    def _number(value: Any) -> Optional[float]:
        return None if value is None else float(value)

    @staticmethod
    def _candle(value: CandleLike) -> Candle:
        if isinstance(value, Candle):
            return value
        if not isinstance(value, Mapping):
            raise TypeError("candles must be Candle instances or mappings")
        timestamp = value.get("timestamp", value.get("time", value.get("date")))
        return Candle(
            timestamp,
            float(value["open"]),
            float(value["high"]),
            float(value["low"]),
            float(value["close"]),
            None if value.get("volume") is None else float(value["volume"]),
        )

    @staticmethod
    def _signal(value: Any) -> Dict[str, Any]:
        if value is None:
            return {"action": "hold"}
        if isinstance(value, str):
            text = value.lower().strip()
            if text in ("exit", "close"):
                return {"action": "exit"}
            if text in ("long", "enter_long"):
                return {"action": "enter", "side": "long"}
            if text in ("short", "enter_short"):
                return {"action": "enter", "side": "short"}
            return {"action": "hold"}
        if not isinstance(value, Mapping):
            raise TypeError("strategy signals must be strings, mappings, or None")
        signal = dict(value)
        action = str(signal.get("action", signal.get("signal", "hold"))).lower()
        if action in ("buy", "sell"):
            signal["side"] = "long" if action == "buy" else "short"
            action = "enter"
        if action in ("close", "flatten"):
            action = "exit"
        if action in ("long", "short"):
            signal["side"] = action
            action = "enter"
        signal["action"] = action
        if signal.get("side") is not None:
            signal["side"] = str(signal["side"]).lower()
        return signal

    def _metrics(self, trades: List[Trade], equity: List[float]) -> Dict[str, Any]:
        count = len(trades)
        wins = [trade.pnl for trade in trades if trade.pnl > 0]
        losses = [trade.pnl for trade in trades if trade.pnl < 0]
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        expectancy = sum(trade.r_multiple for trade in trades) / count if count else 0.0
        peak = self.initial_capital
        max_drawdown = 0.0
        for value in equity:
            peak = max(peak, value)
            max_drawdown = max(max_drawdown, peak - value)
        profit_factor = gross_profit / gross_loss if gross_loss else (float("inf") if gross_profit else 0.0)
        passed = count >= self.min_trades
        return {
            "win_rate": len(wins) / count if count else 0.0,
            "expectancy_r": expectancy,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "trade_count": count,
            "final_equity": equity[-1] if equity else self.initial_capital,
            "gate_passed": passed,
            "gate_message": (
                "200-trade gate passed"
                if passed and self.min_trades == 200
                else ("trade-count gate passed" if passed else f"200-trade gate failed: need at least {self.min_trades} completed trades; got {count}")
            ),
        }


__all__ = ["BacktestResult", "Backtester", "Candle", "Strategy", "Trade"]
