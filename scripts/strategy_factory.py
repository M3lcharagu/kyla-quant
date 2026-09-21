#!/usr/bin/env python3
"""Real multi-market strategy scanner; legacy single-symbol JSON CLI is preserved."""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quant.backtest import Backtester
from quant import data as data_api

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
LOGGER = logging.getLogger(__name__)

DEFAULT_MODULES = [
    "quant.strategies.momentum_breakout",
    "quant.strategies.opening_range_breakout",
    "quant.strategies.rolling_vwap_mean_reversion",
    "quant.strategies.rsi2_reversal",
    "quant.strategies.volume_confirmed_breakout",
    "quant.strategies.ema_cross_atr",
    "quant.strategies.session_high_low_breakout",
    "quant.strategies.donchian_scalp",
]
SYMBOLS = ["SOLUSDT", "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"]
INTERVALS = ["1m", "5m", "15m", "30m", "1h"]
MIN_USABLE_CANDLES = 300


def strategy_class(module_name: str, class_name: str | None = None):
    module = importlib.import_module(module_name)
    if class_name:
        return getattr(module, class_name)
    found = [cls for _, cls in inspect.getmembers(module, inspect.isclass) if cls.__module__ == module_name and callable(getattr(cls, "next", None))]
    if not found:
        raise TypeError(f"no strategy class exposing next() in {module_name}")
    return found[0]


class SignalAdapter:
    def __init__(self, raw):
        self.raw = raw

    def next(self, candle):
        signal = self.raw.next(candle)
        if signal is None:
            return {"action": "hold"}
        if hasattr(signal, "__dataclass_fields__"):
            signal = {key: getattr(signal, key) for key in signal.__dataclass_fields__}
        elif hasattr(signal, "__dict__") and not isinstance(signal, dict):
            signal = vars(signal)
        if isinstance(signal, str):
            signal = {"action": signal}
        if not isinstance(signal, dict):
            raise TypeError("strategy signal must be a mapping/string/object")
        action = str(signal.get("action", signal.get("signal", "hold"))).lower()
        if action in ("buy", "long"):
            return {**signal, "action": "enter", "side": "long"}
        if action in ("sell", "short"):
            return {**signal, "action": "enter", "side": "short"}
        if action in ("close", "flatten"):
            return {**signal, "action": "exit"}
        return {**signal, "action": action}


def metrics(result, initial: float = 10_000.0) -> dict[str, Any]:
    values = dict(result.metrics)
    trades = result.trades
    wins = sum(trade.pnl > 0 for trade in trades)
    losses = sum(trade.pnl < 0 for trade in trades)
    values.update(
        net_profit=result.final_equity - initial,
        net_profit_pct=(result.final_equity - initial) / initial * 100.0,
        trades=len(trades),
        wins=wins,
        losses=losses,
        win_rate=wins / len(trades) * 100.0 if trades else 0.0,
        max_drawdown_pct=values.get("max_drawdown", 0.0) / max(max(result.equity_curve or [initial]), initial) * 100.0,
    )
    values["verdict"] = (
        "INCONCLUSIVE" if len(trades) < 50 else
        "PASS" if values.get("profit_factor", 0.0) > 1.15 and values.get("win_rate", 0.0) >= 45.0 and values.get("net_profit_pct", 0.0) > 0.0
        else "FAIL"
    )
    if not trades:
        values["no_trade_reason"] = "insufficient data" if len(result.equity_curve) < MIN_USABLE_CANDLES else "no entry signals"
    return values


def _timestamp_key(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value) / (1000.0 if value > 10_000_000_000 else 1.0)
    text = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    return parsed.timestamp()


def _validate_scan(candles, source: str) -> None:
    if not candles:
        raise ValueError(f"{source} returned no usable candles")
    previous = None
    for candle in candles:
        timestamp = _timestamp_key(candle.timestamp)
        if previous is not None and timestamp <= previous:
            raise ValueError(f"{source} timestamps are not strictly ascending")
        previous = timestamp
        prices = (candle.open, candle.high, candle.low, candle.close)
        if any(not (0.0 < float(price) < 200000.0) for price in prices):
            raise ValueError(f"{source} returned price outside generic bounds (0, 200000)")
        if candle.volume is None or float(candle.volume) <= 0.0:
            raise ValueError(f"{source} returned zero or missing volume")
        if float(candle.high) < max(candle.open, candle.close, candle.low) or float(candle.low) > min(candle.open, candle.close, candle.high):
            raise ValueError(f"{source} returned inconsistent OHLC")
    if len(candles) < MIN_USABLE_CANDLES:
        raise ValueError(f"{source} returned {len(candles)} candles; minimum usable is {MIN_USABLE_CANDLES}")


def _source_loaders(symbol: str, interval: str, limit: int):
    opener = data_api.urlopen
    start = end = None
    loaders = [
        ("Binance spot", lambda: data_api._fetch_binance(symbol, interval, limit, start, end, opener)),
        ("Bybit spot", lambda: data_api._fetch_bybit(symbol, interval, limit, start, end, opener)),
        ("OKX", lambda: data_api._fetch_okx(symbol, interval, limit, start, end, opener)),
    ]
    if data_api._compact(symbol) == "SOLUSDT" and interval.lower() in ("5m", "5"):
        loaders += [
            ("Gate.io spot", lambda: data_api._fetch_gate(limit, opener)),
            ("KuCoin", lambda: data_api._fetch_kucoin(limit, opener)),
            ("MEXC", lambda: data_api._fetch_mexc(limit, opener)),
            ("Bitfinex", lambda: data_api._fetch_bitfinex(limit, end, opener)),
            ("Bitstamp", lambda: data_api._fetch_bitstamp(limit, opener)),
        ]
    return loaders


def load_with_report(symbol: str, interval: str, limit: int):
    attempts = []
    for source, loader in _source_loaders(symbol, interval, limit):
        attempt = {"symbol": symbol, "timeframe": interval, "source": source, "status": "FAILURE", "candles": 0, "coverage": "THIN", "first": "-", "last": "-", "first_error": ""}
        try:
            candles = data_api._dedupe(loader())
            attempt["candles"] = len(candles)
            _validate_scan(candles, source)
            attempt.update(status="SUCCESS", coverage=coverage(len(candles)), first=str(candles[0].timestamp), last=str(candles[-1].timestamp))
            attempts.append(attempt)
            LOGGER.info("scanner dataset %s %s: %d candles from %s", symbol, interval, len(candles), source)
            return candles[-limit:], attempts
        except Exception as exc:
            attempt["first_error"] = str(exc).splitlines()[0][:300]
            attempts.append(attempt)
            LOGGER.warning("data source failed %s %s %s: %s", symbol, interval, source, attempt["first_error"])
    return [], attempts


def coverage(count: int) -> str:
    if count >= 10000:
        return "FULL"
    if count >= 1000:
        return "PARTIAL"
    return "THIN"


def run_one(module_name: str, candles, class_name: str | None = None):
    cls = strategy_class(module_name, class_name)
    result = Backtester(SignalAdapter(cls()), initial_capital=10_000.0, quantity=1.0, spread=0.0, slippage=0.0, commission=0.0, commission_rate=0.0002, min_trades=0).run(candles)
    result_metrics = metrics(result)
    result_metrics.update(strategy=module_name.rsplit(".", 1)[-1], strategy_module=module_name)
    return result_metrics


def scan(symbols=SYMBOLS, intervals=INTERVALS, limit=3000, output=None, source_output="docs/DATA_SOURCES.md"):
    rows = []
    source_attempts = []
    for symbol in symbols:
        for interval in intervals:
            candles, attempts = load_with_report(symbol, interval, limit)
            source_attempts.extend(attempts)
            if not candles:
                reason = "data source exhaustion: " + "; ".join(a["first_error"] for a in attempts if a["first_error"])
                for module in DEFAULT_MODULES:
                    rows.append({"symbol": symbol, "interval": interval, "strategy": module.rsplit(".", 1)[-1], "verdict": "INCONCLUSIVE", "trades": 0, "no_trade_reason": reason[:500]})
                continue
            for module in DEFAULT_MODULES:
                try:
                    rows.append({"symbol": symbol, "interval": interval, **run_one(module, candles)})
                except Exception as exc:
                    rows.append({"symbol": symbol, "interval": interval, "strategy": module.rsplit(".", 1)[-1], "verdict": "INCONCLUSIVE", "trades": 0, "no_trade_reason": f"strategy error: {exc}"})
    if output:
        write_markdown(rows, Path(output))
    write_data_sources(source_attempts, Path(source_output))
    return rows


def write_data_sources(attempts, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Runtime data sources", "", "Generated by `python scripts/strategy_factory.py --scan`; only live provider responses are recorded.", "", "| Symbol | Timeframe | Source | Status | Candles | Coverage | First timestamp | Last timestamp | First error |", "|---|---|---|---|---:|---|---|---|---|"]
    for item in attempts:
        error = item.get("first_error", "").replace("|", "\\|") or "-"
        lines.append(f"| {item['symbol']} | {item['timeframe']} | {item['source']} | {item['status']} | {item['candles']} | {item['coverage']} | {item['first']} | {item['last']} | {error} |")
    successes = sum(item["status"] == "SUCCESS" for item in attempts)
    lines += ["", f"Attempted sources: **{len(attempts)}**; successful sources: **{successes}**; generated at **{datetime.now(timezone.utc).isoformat()}**.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_markdown(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda row: (row.get("symbol", ""), row.get("interval", ""), row.get("strategy", "")))
    lines = ["# Strategy library - real multi-market scan", "", "Generated by `python scripts/strategy_factory.py --scan`; values are fetched at workflow runtime and are not hardcoded.", "", "PASS requires PF > 1.15, win rate >= 45%, net profit > 0, and at least 50 trades. Costs include 0.0002 commission per side.", "", "| Symbol | Timeframe | Strategy | Verdict | Net profit % | Win rate % | Profit factor | Max drawdown % | Trades | Note |", "|---|---|---|---|---:|---:|---:|---:|---:|---|"]
    for row in rows:
        verdict = row.get("verdict", "INCONCLUSIVE")
        shown = f"**{verdict}**" if verdict == "PASS" else verdict
        note = row.get("no_trade_reason", "-").replace("|", "\\|")
        if isinstance(row.get("net_profit_pct"), (int, float)):
            lines.append(f"| {row.get('symbol','-')} | {row.get('interval','-')} | {row.get('strategy','-')} | {shown} | {row.get('net_profit_pct','-'):.4f} | {row.get('win_rate','-'):.2f} | {row.get('profit_factor','-'):.4f} | {row.get('max_drawdown_pct','-'):.4f} | {row.get('trades',0)} | {note} |")
        else:
            lines.append(f"| {row.get('symbol','-')} | {row.get('interval','-')} | {row.get('strategy','-')} | {shown} | - | - | - | - | 0 | {note} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="SOLUSDT")
    parser.add_argument("--interval", default="5m")
    parser.add_argument("--limit", type=int, default=2000)
    parser.add_argument("--module", action="append")
    parser.add_argument("--class", dest="class_name")
    parser.add_argument("--scan", action="store_true")
    parser.add_argument("--output", default="docs/STRATEGY_LIBRARY.md")
    args = parser.parse_args(argv)
    if args.scan:
        rows = scan(limit=args.limit, output=args.output)
        print(json.dumps({"runs": len(rows), "output": args.output, "source_output": "docs/DATA_SOURCES.md"}, indent=2))
        return
    candles = data_api.load_binance_candles(args.symbol, args.interval, limit=args.limit)
    modules = args.module or DEFAULT_MODULES
    result = {"dataset": {"symbol": args.symbol, "interval": args.interval, "candles": len(candles)}, "results": [run_one(module, candles, args.class_name) for module in modules]}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
