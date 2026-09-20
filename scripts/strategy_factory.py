#!/usr/bin/env python3
"""Stdlib-only SOLUSDT strategy research harness; exploratory, never validation."""
from __future__ import annotations
import argparse, importlib, inspect, json, os, ssl, sys, time, urllib.request
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, Optional

# Demo-only workaround retained from existing scripts; verify certificates in real use.
_ctx = ssl._create_unverified_context()
urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPSHandler(context=_ctx)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from quant.backtest import Backtester
from quant.costs import DEFAULT_COSTS
from quant.data import load_binance_klines

DEFAULT_MODULES = [
    "quant.strategies.momentum_breakout", "quant.strategies.opening_range_breakout",
    "quant.strategies.rolling_vwap_mean_reversion", "quant.strategies.rsi2_reversal",
    "quant.strategies.volume_confirmed_breakout", "quant.strategies.ema_cross_atr",
    "quant.strategies.session_high_low_breakout", "quant.strategies.donchian_scalp",
]

def fetch_paginated(symbol: str, interval: str, limit: int) -> list:
    """Fetch newest candles chronologically, respecting Binance's 1000-row page cap."""
    if limit < 1:
        raise ValueError("limit must be positive")
    rows, end_time = {}, None
    while len(rows) < limit:
        ask = min(1000, limit - len(rows))
        page = load_binance_klines(symbol.upper(), interval, end_time=end_time, limit=ask)
        if not page:
            break
        before = len(rows)
        for candle in page:
            rows[candle.timestamp] = candle
        if len(rows) == before:
            break
        end_time = int(min(rows).timestamp() * 1000) - 1
        if len(page) < ask:
            break
        time.sleep(0.10)
    return [rows[key] for key in sorted(rows)][-limit:]

def strategy_class(module_name: str, class_name: Optional[str]) -> type:
    module = importlib.import_module(module_name)
    if class_name:
        candidate = getattr(module, class_name)
        if not callable(getattr(candidate, "next", None)):
            raise TypeError("selected class must expose next(candle)")
        return candidate
    found = [c for _, c in inspect.getmembers(module, inspect.isclass)
             if c.__module__ == module_name and callable(getattr(c, "next", None))]
    if not found:
        raise TypeError("no module-local class with next(candle) found")
    return found[0]

class SignalAdapter:
    """Adapt Signal-like dataclasses/objects to the mapping API used by Backtester."""
    def __init__(self, raw: Any):
        self.raw = raw
    def next(self, candle: Any) -> Any:
        signal = self.raw.next(candle)
        if signal is None or isinstance(signal, (str, Mapping)):
            return signal
        if is_dataclass(signal):
            signal = asdict(signal)
        elif hasattr(signal, "__dict__"):
            signal = dict(vars(signal))
        else:
            raise TypeError("signal must be string, mapping, dataclass, or object")
        action = str(signal.get("action", signal.get("signal", "hold"))).lower()
        if action in ("long", "buy"):
            action = "enter"; signal["side"] = "long"
        elif action in ("short", "sell"):
            action = "enter"; signal["side"] = "short"
        elif action in ("close", "flatten"):
            action = "exit"
        signal["action"] = action
        return signal

def load_strategy(module_name: str, class_name: Optional[str]) -> SignalAdapter:
    cls = strategy_class(module_name, class_name)
    try:
        return SignalAdapter(cls())
    except TypeError as exc:
        raise TypeError("strategy must be constructible with no arguments") from exc

def verdict(m: Dict[str, Any]) -> str:
    count = int(m["trade_count"])
    sane = (0 <= float(m["win_rate"] or 0) <= 1 and
            count == int(m["wins"]) + int(m["losses"]) + int(m["flat_trades"]))
    if count < 200:
        return "INCONCLUSIVE"
    if not sane:
        return "FAIL"
    return "PASS research" if (m["net_profit"] > 0 and m["profit_factor"] > 1.15 and m["max_drawdown_pct"] < .20) else "FAIL"

def run_one(module_name: str, candles: Iterable[Any], class_name: Optional[str]) -> Dict[str, Any]:
    initial = 10000.0
    model = DEFAULT_COSTS["BINANCE_SOL_MAKER"]
    result = Backtester(load_strategy(module_name, class_name), initial_capital=initial,
        quantity=1.0, spread=0.0, slippage=0.0, commission=0.0,
        commission_rate=model.commission_rate_per_side, min_trades=200).run(candles)
    m = dict(result.metrics)
    curve = result.equity_curve or [initial]
    peak = max(curve) if curve else initial
    m.update({"strategy_module": module_name, "initial_capital": initial,
        "final_equity": result.final_equity, "net_profit": result.final_equity - initial,
        "max_drawdown_pct": m["max_drawdown"] / peak if peak else 0.0,
        "wins": sum(t.pnl > 0 for t in result.trades),
        "losses": sum(t.pnl < 0 for t in result.trades),
        "flat_trades": sum(t.pnl == 0 for t in result.trades),
        "win_rate_sanity": "0 <= win_rate <= 1 and wins+losses+flat_trades == trade_count"})
    m["verdict"] = verdict(m)
    return m

def main(argv=None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", default="SOLUSDT")
    parser.add_argument("--interval", default="5m")
    parser.add_argument("--limit", type=int, default=20000)
    parser.add_argument("--module", action="append", dest="modules", help="repeatable module path")
    parser.add_argument("--class", dest="class_name")
    args = parser.parse_args(argv)
    modules = args.modules or DEFAULT_MODULES
    candles = fetch_paginated(args.symbol, args.interval, args.limit)
    if not candles:
        raise RuntimeError("Binance returned no candles")
    model = DEFAULT_COSTS["BINANCE_SOL_MAKER"]
    output = {"dataset": {"source": "Binance public /api/v3/klines", "symbol": args.symbol.upper(),
        "interval": args.interval, "candles": len(candles), "start": candles[0].timestamp.isoformat(),
        "end": candles[-1].timestamp.isoformat()},
        "costs": {"model": "BINANCE_SOL_MAKER", "commission_rate_per_side": model.commission_rate_per_side,
                  "spread": 0.0, "slippage": 0.0},
        "thresholds": {"minimum_trades": 200, "net_profit_gt": 0.0, "profit_factor_gt": 1.15,
                       "max_drawdown_pct_lt": 0.20, "win_rate_sanity": "0 <= win_rate <= 1 and counts reconcile"},
        "results": [run_one(name, candles, args.class_name) for name in modules],
        "caveat": "Exploratory research only; no result is validated or proof of future performance."}
    print(json.dumps(output, indent=2, sort_keys=True, default=str))
    return output

if __name__ == "__main__":
    main()
