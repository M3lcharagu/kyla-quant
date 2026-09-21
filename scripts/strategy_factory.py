#!/usr/bin/env python3
"""Real multi-market strategy scanner; legacy single-symbol JSON CLI is preserved."""
from __future__ import annotations
import argparse, importlib, inspect, json, logging, sys
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from quant.backtest import Backtester
from quant import data as data_api

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
LOGGER = logging.getLogger(__name__)
DEFAULT_MODULES = [
    "quant.strategies.momentum_breakout", "quant.strategies.opening_range_breakout",
    "quant.strategies.rolling_vwap_mean_reversion", "quant.strategies.rsi2_reversal",
    "quant.strategies.volume_confirmed_breakout", "quant.strategies.ema_cross_atr",
    "quant.strategies.session_high_low_breakout", "quant.strategies.donchian_scalp",
    "quant.strategies.orb_range", "quant.strategies.volume_profile_imbalance",
    "quant.strategies.no_effort_40range", "quant.strategies.tpo_profile",
    "quant.strategies.deep_gamma_delta",
]
SYMBOLS = ["SOLUSDT", "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"]
INTERVALS = ["1m", "5m", "15m", "30m", "1h"]
MIN_USABLE_CANDLES = 300


def strategy_class(module_name: str, class_name: str | None = None):
    module = importlib.import_module(module_name)
    if class_name: return getattr(module, class_name)
    found = [c for _, c in inspect.getmembers(module, inspect.isclass) if c.__module__ == module_name and callable(getattr(c, "next", None))]
    if not found: raise TypeError(f"no strategy class exposing next() in {module_name}")
    return found[0]


class SignalAdapter:
    def __init__(self, raw: Any): self.raw = raw
    def next(self, candle: Any):
        signal = self.raw.next(candle)
        if signal is None: return {"action": "hold"}
        if hasattr(signal, "__dataclass_fields__"): signal = {k: getattr(signal, k) for k in signal.__dataclass_fields__}
        elif hasattr(signal, "__dict__") and not isinstance(signal, dict): signal = vars(signal)
        elif isinstance(signal, str): signal = {"action": signal}
        if not isinstance(signal, dict): raise TypeError("strategy signal must be a mapping/string/object")
        action = str(signal.get("action", signal.get("signal", "hold"))).lower()
        if action in ("buy", "long"): return {**signal, "action": "enter", "side": "long"}
        if action in ("sell", "short"): return {**signal, "action": "enter", "side": "short"}
        if action in ("close", "flatten"): return {**signal, "action": "exit"}
        return {**signal, "action": action}


def metrics(result: Any, initial: float = 10_000.0) -> dict[str, Any]:
    trades = result.trades
    wins = sum(t.pnl > 0 for t in trades); losses = sum(t.pnl < 0 for t in trades)
    out = dict(result.metrics)
    out.update(net_profit=result.final_equity - initial, net_profit_pct=(result.final_equity - initial) / initial * 100.0,
               trades=len(trades), wins=wins, losses=losses, win_rate=wins / len(trades) * 100.0 if trades else 0.0)
    out["verdict"] = "INCONCLUSIVE" if len(trades) < 50 else "PASS" if out.get("profit_factor", 0) > 1.15 and out["win_rate"] >= 45 and out["net_profit_pct"] > 0 else "FAIL"
    return out


def _loaders(symbol: str, interval: str, limit: int):
    opener = data_api.urlopen; start = end = None
    loaders = [("Binance spot", lambda: data_api._fetch_binance(symbol, interval, limit, start, end, opener)),
               ("Bybit spot", lambda: data_api._fetch_bybit(symbol, interval, limit, start, end, opener)),
               ("OKX", lambda: data_api._fetch_okx(symbol, interval, limit, start, end, opener))]
    if data_api._compact(symbol) == "SOLUSDT" and interval.lower() in ("5m", "5"):
        loaders += [("Gate.io spot", lambda: data_api._fetch_gate(limit, opener)),
                    ("KuCoin", lambda: data_api._fetch_kucoin(limit, opener)),
                    ("MEXC", lambda: data_api._fetch_mexc(limit, opener)),
                    ("Bitfinex", lambda: data_api._fetch_bitfinex(limit, end, opener)),
                    ("Bitstamp", lambda: data_api._fetch_bitstamp(limit, opener))]
    return loaders


def load_with_report(symbol: str, interval: str, limit: int):
    attempts = []
    for source, loader in _loaders(symbol, interval, limit):
        row = {"symbol": symbol, "timeframe": interval, "source": source, "status": "FAILURE", "candles": 0, "coverage": "THIN", "first_error": ""}
        try:
            candles = data_api._dedupe(loader()); row["candles"] = len(candles); data_api._validate(candles, source)
            row.update(status="SUCCESS", coverage=coverage(len(candles)), first=str(candles[0].timestamp), last=str(candles[-1].timestamp)); attempts.append(row)
            return candles[-limit:], attempts
        except Exception as exc:
            row["first_error"] = str(exc).splitlines()[0][:300]; attempts.append(row)
    return [], attempts


def coverage(count: int) -> str: return "FULL" if count >= 10000 else "PARTIAL" if count >= 1000 else "THIN"


def run_one(module_name: str, candles: list[Any], class_name: str | None = None) -> dict[str, Any]:
    cls = strategy_class(module_name, class_name)
    result = Backtester(SignalAdapter(cls()), initial_capital=10_000.0, quantity=1.0, spread=0.0, slippage=0.0, commission=0.0, commission_rate=0.0002, min_trades=0).run(candles)
    out = metrics(result); out.update(strategy=module_name.rsplit(".", 1)[-1], strategy_module=module_name); return out


def scan(symbols=SYMBOLS, intervals=INTERVALS, limit=3000, output=None):
    rows, source_attempts = [], []
    for symbol in symbols:
        for interval in intervals:
            candles, attempts = load_with_report(symbol, interval, limit); source_attempts.extend(attempts)
            if not candles:
                reason = "data source exhaustion: " + "; ".join(a["first_error"] for a in attempts if a["first_error"])
                rows.extend({"symbol": symbol, "interval": interval, "strategy": m.rsplit(".", 1)[-1], "verdict": "INCONCLUSIVE", "trades": 0, "no_trade_reason": reason[:500]} for m in DEFAULT_MODULES); continue
            for module in DEFAULT_MODULES:
                try: rows.append({"symbol": symbol, "interval": interval, **run_one(module, candles)})
                except Exception as exc: rows.append({"symbol": symbol, "interval": interval, "strategy": module.rsplit(".", 1)[-1], "verdict": "INCONCLUSIVE", "trades": 0, "no_trade_reason": f"strategy error: {exc}"})
    if output: write_markdown(rows, Path(output))
    write_sources(source_attempts, ROOT / "docs/DATA_SOURCES.md")
    return rows


def write_sources(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True); lines = ["# Runtime data sources", "", "| Symbol | Timeframe | Source | Status | Candles | Coverage | First | Last | Error |", "|---|---|---|---:|---:|---|---|---|---|"]
    for x in rows: lines.append("| {symbol} | {timeframe} | {source} | {status} | {candles} | {coverage} | {first} | {last} | {first_error} |".format(**{k: x.get(k, "-") or "-" for k in ("symbol", "timeframe", "source", "status", "candles", "coverage", "first", "last", "first_error")}))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True); lines = ["# Strategy library - real multi-market scan", "", f"Registered strategies: **{len(DEFAULT_MODULES)}**", "", "| Symbol | Timeframe | Strategy | Verdict | Net profit % | Win rate % | Trades | Note |", "|---|---|---|---|---:|---:|---:|---|"]
    for r in sorted(rows, key=lambda x: (x.get("symbol", ""), x.get("interval", ""), x.get("strategy", ""))): lines.append(f"| {r.get('symbol','-')} | {r.get('interval','-')} | {r.get('strategy','-')} | {r.get('verdict','INCONCLUSIVE')} | {r.get('net_profit_pct','-')} | {r.get('win_rate','-')} | {r.get('trades',0)} | {r.get('no_trade_reason','-')} |" )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--symbol", default="SOLUSDT"); p.add_argument("--interval", default="5m"); p.add_argument("--limit", type=int, default=2000); p.add_argument("--module", action="append"); p.add_argument("--class", dest="class_name"); p.add_argument("--scan", action="store_true"); p.add_argument("--output", default="docs/STRATEGY_LIBRARY.md"); args = p.parse_args(argv)
    if args.scan:
        rows = scan(limit=args.limit, output=args.output); print(json.dumps({"strategy_count": len(DEFAULT_MODULES), "runs": len(rows), "output": args.output, "source_output": "docs/DATA_SOURCES.md"}, indent=2)); return
    candles = data_api.load_binance_candles(args.symbol, args.interval, limit=args.limit); modules = args.module or DEFAULT_MODULES
    print(json.dumps({"dataset": {"symbol": args.symbol, "interval": args.interval, "candles": len(candles)}, "results": [run_one(m, candles, args.class_name) for m in modules]}, indent=2, sort_keys=True, default=str))

if __name__ == "__main__": main()
