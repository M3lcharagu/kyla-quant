#!/usr/bin/env python3
"""Run a small SOLUSDT 5-minute backtest with the repository's strategy APIs."""

import os
import sys
from datetime import timedelta


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from quant.backtest import Backtester, Strategy
from quant.costs import DEFAULT_COSTS
from quant.data import load_binance_klines
from quant.strategies.sol_micro_scalp import SolMicroScalp


class BacktestAdapter(Strategy):
    """Adapt SolMicroScalp signals to the Backtester protocol."""

    def __init__(self, config=None):
        self.scalper = SolMicroScalp(config)
        self.config = self.scalper.config
        self.active_position = None

    def next(self, candle):
        # Keep the strategy's rolling state advancing on every candle received.
        signal = self.scalper.next(candle)
        timestamp = getattr(candle, "timestamp", None)

        if self.active_position is not None:
            position = self.active_position
            high = float(candle.high)
            low = float(candle.low)
            side = position["side"]
            stop = position["stop"]
            target = position["target"]

            protective_hit = (
                (side == "long" and (low <= stop or high >= target))
                or (side == "short" and (high >= stop or low <= target))
            )
            if protective_hit:
                self.active_position = None
                return {"action": "exit"}

            entry_timestamp = position["entry_timestamp"]
            max_hold_minutes = getattr(self.config, "max_hold_minutes", 45)
            if timestamp is not None and entry_timestamp is not None:
                held_for = timestamp - entry_timestamp
                if held_for >= timedelta(minutes=max_hold_minutes):
                    self.active_position = None
                    return {"action": "exit"}

            # Ignore additional entries while the tracked position is active.
            return {"action": "hold"}

        action = getattr(signal, "action", None)
        if action not in ("long", "short"):
            return {"action": "hold"}

        stop = float(signal.stop)
        target = float(signal.target)
        self.active_position = {
            "side": action,
            "stop": stop,
            "target": target,
            "entry_timestamp": timestamp,
        }
        return {
            "action": "enter",
            "side": action,
            "stop": stop,
            "target": target,
            "quantity": 1.0,
        }


def _wrapped_candles():
    raw_candles = load_binance_klines("SOLUSDT", "5m", limit=1000)
    return [
        {
            "timestamp": candle.timestamp,
            "open": float(candle.open),
            "high": float(candle.high),
            "low": float(candle.low),
            "close": float(candle.close),
            "volume": None if candle.volume is None else float(candle.volume),
            "funding_rate": 0.0,
        }
        for candle in raw_candles
    ]


def main():
    candles = _wrapped_candles()
    cost_model = DEFAULT_COSTS["BINANCE_SOL_MAKER"]
    result = Backtester(
        BacktestAdapter(),
        initial_capital=10000.0,
        quantity=1.0,
        spread=0.0,
        slippage=0.0,
        commission=0.0,
        commission_rate=cost_model.commission_rate_per_side,
        min_trades=0,
    ).run(candles)

    metrics = result.metrics
    curve = result.equity_curve
    final_equity = result.final_equity
    net_profit = final_equity - 10000.0
    curve_min = min(curve) if curve else final_equity
    curve_max = max(curve) if curve else final_equity
    curve_end = curve[-1] if curve else final_equity

    print("SOLUSDT 5m backtest")
    print("-------------------")
    print("candles: {}".format(len(candles)))
    print(
        "cost model: BINANCE_SOL_MAKER "
        "(commission_rate_per_side={:.6f}, spread=0.0, slippage=0.0, commission=0.0)".format(
            cost_model.commission_rate_per_side
        )
    )
    print("trade count: {}".format(metrics["trade_count"]))
    print("win rate: {:.2%}".format(metrics["win_rate"]))
    print("net profit: {:.6f}".format(net_profit))
    print("max drawdown: {:.6f}".format(metrics["max_drawdown"]))
    print("profit factor: {}".format(metrics["profit_factor"]))
    print("expectancy R: {:.6f}".format(metrics["expectancy_r"]))
    print("final equity: {:.6f}".format(final_equity))
    print(
        "equity curve: points={}, min={:.6f}, max={:.6f}, end={:.6f}".format(
            len(curve), curve_min, curve_max, curve_end
        )
    )
    print("note: demo bypasses the 200-trade gate (min_trades=0).")


if __name__ == "__main__":
    main()
