"""Reproducible ICT/SMC/ORB comparison runner.

This module fetches public data only when invoked locally, records provenance,
then evaluates all concepts through the same simple OHLC event simulator.
It intentionally refuses to label a result PASS when the 200-trade gate is not
met.  It is a research runner, not investment advice.
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Sequence

import pandas as pd
import requests

from kyla_quant.setups.sequence_setup import Bar as SequenceBar
from kyla_quant.setups.sequence_setup import detect_sequence
from kyla_quant.strategies.fvg import Bar, detect_fvgs, detect_ifvgs
from kyla_quant.strategies.order_block import detect_order_blocks
from kyla_quant.strategies.orb import ORBConfig, detect_orb_setups

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
YFINANCE_TICKER_URL = "https://finance.yahoo.com/quote/GC%3DF/history"


@dataclass(frozen=True)
class CostModel:
    commission: float = 0.0005
    spread_bps: float = 1.0
    slippage_bps: float = 1.0

    def round_trip_price_rate(self) -> float:
        # Commission, spread, and slippage are charged on both entry and exit.
        return 2.0 * (self.commission + self.spread_bps / 10_000 + self.slippage_bps / 10_000)


@dataclass(frozen=True)
class Setup:
    strategy: str
    direction: str
    formed_index: int
    entry: float
    stop: float
    target: float
    session: str = "other"
    latest_index: int | None = None


def fetch_binance_klines(symbol: str = "SOLUSDT", interval: str = "5m",
                         days: int = 365, limit: int = 1000,
                         session: requests.Session | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fetch paginated Binance spot klines and return exact row provenance."""
    if days <= 0 or limit > 1000:
        raise ValueError("days must be positive and Binance limit must be <= 1000")
    http = session or requests.Session()
    fetched_at = datetime.now(timezone.utc).isoformat()
    end_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_ms = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
    rows: list[list[Any]] = []
    cursor = start_ms
    while cursor < end_ms:
        response = http.get(BINANCE_KLINES_URL, params={
            "symbol": symbol.upper(), "interval": interval,
            "startTime": cursor, "endTime": end_ms, "limit": limit,
        }, timeout=30)
        response.raise_for_status()
        page = response.json()
        if not page:
            break
        rows.extend(page)
        next_cursor = int(page[-1][0]) + 1
        if next_cursor <= cursor:
            raise RuntimeError("Binance pagination did not advance")
        cursor = next_cursor
        if len(page) < limit:
            break
        time.sleep(0.05)
    columns = ["timestamp", "open", "high", "low", "close", "volume",
               "close_time", "quote_volume", "trades", "taker_buy_base",
               "taker_buy_quote", "unused"]
    frame = pd.DataFrame(rows, columns=columns)
    if frame.empty:
        raise RuntimeError("Binance returned no klines")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
    for column in ("open", "high", "low", "close", "volume"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame = frame.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
    provenance = {
        "source": "Binance public spot klines",
        "url": BINANCE_KLINES_URL,
        "symbol": symbol.upper(), "interval": interval,
        "requested_days": days, "fetched_at_utc": fetched_at,
        "row_count": int(len(frame)),
        "first_timestamp_utc": frame.timestamp.iloc[0].isoformat(),
        "last_timestamp_utc": frame.timestamp.iloc[-1].isoformat(),
    }
    frame.attrs["provenance"] = provenance
    return frame, provenance


def fetch_gold_proxy(start: str, end: str) -> tuple[pd.DataFrame | None, dict[str, Any]]:
    """Try optional yfinance GC=F; absence is an explicit pending result."""
    try:
        import yfinance as yf  # optional dependency by design
    except ImportError:
        return None, {"status": "PENDING", "reason": "yfinance is not installed", "ticker": "GC=F", "url": YFINANCE_TICKER_URL}
    frame = yf.download("GC=F", start=start, end=end, auto_adjust=False, progress=False)
    if frame.empty:
        return None, {"status": "PENDING", "reason": "yfinance returned no rows", "ticker": "GC=F", "url": YFINANCE_TICKER_URL}
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    frame = frame.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
    frame = frame.reset_index().rename(columns={"Date": "timestamp"})
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    return frame, {"status": "AVAILABLE", "ticker": "GC=F", "url": YFINANCE_TICKER_URL, "row_count": int(len(frame)),
                   "first_timestamp_utc": frame.timestamp.iloc[0].isoformat(), "last_timestamp_utc": frame.timestamp.iloc[-1].isoformat()}


def _bars(frame: pd.DataFrame) -> list[Bar]:
    return [Bar(float(r.open), float(r.high), float(r.low), float(r.close), r.timestamp, float(r.volume))
            for r in frame.itertuples()]


def _sequence_setups(frame: pd.DataFrame) -> list[Setup]:
    work = frame.copy()
    work["ema"] = work.close.ewm(span=20, adjust=False, min_periods=20).mean()
    work["ema_previous"] = work.ema.shift(1)
    work["momentum"] = work.close.diff(3)
    work["average_volume"] = work.volume.rolling(20, min_periods=20).mean()
    bars: list[SequenceBar] = []
    out: list[Setup] = []
    for i, row in enumerate(work.itertuples()):
        bars.append(SequenceBar(float(row.open), float(row.high), float(row.low), float(row.close),
                                None if pd.isna(row.ema) else float(row.ema),
                                None if pd.isna(row.ema_previous) else float(row.ema_previous),
                                None if pd.isna(row.momentum) else float(row.momentum),
                                None if pd.isna(row.volume) else float(row.volume),
                                None if pd.isna(row.average_volume) else float(row.average_volume)))
        if i < 2:
            continue
        signal = detect_sequence(bars[-3:], min_momentum=0.0, min_volume_ratio=1.0, wick_rejection=True)
        if signal is None:
            continue
        row_atr = float((work.high - work.low).rolling(14, min_periods=14).mean().iloc[i])
        if pd.isna(row_atr) or row_atr <= 0:
            continue
        long_side = signal.direction == "long"
        entry = float(row.close)
        stop = float(row.low - row_atr) if long_side else float(row.high + row_atr)
        target = entry + (entry - stop) if long_side else entry - (stop - entry)
        out.append(Setup("sequence_" + signal.name, "long" if long_side else "short", i, entry, stop, target))
    return out


def build_setups(frame: pd.DataFrame) -> dict[str, list[Setup]]:
    bars = _bars(frame)
    output: dict[str, list[Setup]] = {}
    for name, gaps in (("fvg", detect_fvgs(bars)), ("ifvg", detect_ifvgs(bars))):
        output[name] = [Setup(name, g.direction, g.formed_index, g.entry, g.stop, g.target) for g in gaps]
    blocks = detect_order_blocks(bars)
    output["order_block"] = [Setup("order_block", b.direction, b.formed_index, b.entry, b.stop, b.target) for b in blocks]
    orb = detect_orb_setups(bars, ORBConfig())
    output["orb"] = [Setup("orb_" + x.session, x.direction, x.formed_index, x.entry, x.stop, x.target,
                           x.session) for x in orb]
    output["sequence"] = _sequence_setups(frame)
    return output


def _session(ts: object) -> str:
    hour = pd.Timestamp(ts).tz_convert("UTC").hour
    if 9 <= hour < 14:
        return "london"
    if 14 <= hour < 20:
        return "new_york"
    return "other"


def simulate(frame: pd.DataFrame, setups: Sequence[Setup], costs: CostModel,
             start: int = 0, end: int | None = None, max_hold_bars: int = 0) -> list[dict[str, Any]]:
    end = len(frame) if end is None else min(end, len(frame))
    trades: list[dict[str, Any]] = []
    occupied_until = -1
    for setup in sorted(setups, key=lambda x: x.formed_index):
        if setup.formed_index < start or setup.formed_index >= end or setup.formed_index <= occupied_until:
            continue
        fill = None
        for j in range(setup.formed_index + 1, end):
            if frame.low.iloc[j] <= setup.entry <= frame.high.iloc[j]:
                fill = j
                break
        if fill is None:
            continue
        risk = abs(setup.entry - setup.stop)
        if risk <= 0:
            continue
        last = min(end - 1, fill + max_hold_bars) if max_hold_bars else end - 1
        exit_i, exit_price, reason = last, float(frame.close.iloc[last]), "time"
        for j in range(fill, last + 1):
            hit_stop = frame.low.iloc[j] <= setup.stop if setup.direction == "long" else frame.high.iloc[j] >= setup.stop
            hit_target = frame.high.iloc[j] >= setup.target if setup.direction == "long" else frame.low.iloc[j] <= setup.target
            if hit_stop:  # conservative when stop and target are in the same OHLC bar
                exit_i, exit_price, reason = j, setup.stop, "stop"
                break
            if hit_target:
                exit_i, exit_price, reason = j, setup.target, "target"
                break
        raw_r = ((exit_price - setup.entry) if setup.direction == "long" else (setup.entry - exit_price)) / risk
        cost_r = setup.entry * costs.round_trip_price_rate() / risk
        trades.append({"strategy": setup.strategy, "session": setup.session or _session(frame.timestamp.iloc[fill]),
                       "formed_index": setup.formed_index, "entry_index": fill, "exit_index": exit_i,
                       "entry_timestamp": frame.timestamp.iloc[fill].isoformat(), "exit_timestamp": frame.timestamp.iloc[exit_i].isoformat(),
                       "raw_r": raw_r, "cost_r": cost_r, "r": raw_r - cost_r, "exit_reason": reason})
        occupied_until = exit_i
    return trades


def metrics(trades: Sequence[dict[str, Any]], minimum_trades: int = 200) -> dict[str, Any]:
    values = [float(t["r"]) for t in trades]
    if not values:
        return {"trade_count": 0, "win_rate": None, "profit_factor": None, "net_expectancy_r": None,
                "max_drawdown_r": None, "status": "INCONCLUSIVE", "reason": "no completed trades"}
    wins = [x for x in values if x > 0]
    losses = [x for x in values if x < 0]
    equity, peak, drawdown = 0.0, 0.0, 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = min(drawdown, equity - peak)
    return {"trade_count": len(values), "win_rate": len(wins) / len(values),
            "profit_factor": sum(wins) / abs(sum(losses)) if losses else None,
            "net_expectancy_r": sum(values) / len(values), "max_drawdown_r": abs(drawdown),
            "status": "PASS" if len(values) >= minimum_trades else "INCONCLUSIVE",
            "reason": None if len(values) >= minimum_trades else f"{len(values)} trades is below the {minimum_trades}-trade gate"}


def run_comparison(frame: pd.DataFrame, costs: CostModel = CostModel(),
                   train_fraction: float = 0.70, minimum_trades: int = 200) -> dict[str, Any]:
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    split = int(len(frame) * train_fraction)
    setups = build_setups(frame)
    report: dict[str, Any] = {"config": {"costs": asdict(costs), "train_fraction": train_fraction,
                                          "minimum_trades": minimum_trades, "bar_fill": "next-bar touch",
                                          "same_bar_policy": "stop first", "max_hold_bars": 0}, "strategies": {}}
    for name, candidates in setups.items():
        all_trades = simulate(frame, candidates, costs)
        is_trades = simulate(frame, candidates, costs, 0, split)
        oos_trades = simulate(frame, candidates, costs, split, len(frame))
        by_session = {s: metrics([t for t in all_trades if t["session"] == s], minimum_trades=0)
                      for s in ("london", "new_york", "other")}
        report["strategies"][name] = {"all": metrics(all_trades, minimum_trades),
                                       "is": metrics(is_trades, 0), "oos": metrics(oos_trades, 0),
                                       "per_session": by_session}
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Binance klines and compare ICT/SMC/ORB concepts")
    parser.add_argument("--symbol", default="SOLUSDT")
    parser.add_argument("--interval", choices=("1m", "5m"), default="5m")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--commission", type=float, default=0.0005)
    parser.add_argument("--spread-bps", type=float, default=1.0)
    parser.add_argument("--slippage-bps", type=float, default=1.0)
    args = parser.parse_args()
    frame, provenance = fetch_binance_klines(args.symbol, args.interval, args.days)
    report = run_comparison(frame, CostModel(args.commission, args.spread_bps, args.slippage_bps))
    report["run_utc"] = datetime.now(timezone.utc).isoformat()
    report["data_provenance"] = provenance
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
