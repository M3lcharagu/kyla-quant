#!/usr/bin/env python3
"""Dependency-free SOLUSDT 5-minute closed-candle paper trader.

The runner deliberately uses the repository's strategy_factory loader and Binance
fetcher, while recording simulated fills in the existing SQLite journal.  It does
not place exchange orders.
"""
from __future__ import annotations

import argparse
import json
import os
import pkgutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from quant.data import Candle  # noqa: E402
import kill_switch  # noqa: E402
import strategy_factory as factory  # noqa: E402
import trade_journal as journal  # noqa: E402

SYMBOL = "SOLUSDT"
INTERVAL = "5m"
BAR_SIZE = timedelta(minutes=5)
MAX_HOLD = timedelta(minutes=45)
MAKER_FEE_PER_SIDE = 0.0002
DEFAULT_LIMIT = 500
DEFAULT_DB = ROOT / "journal" / "trades.db"
DEFAULT_STATE = ROOT / "journal" / "paper_trader_state.json"


@dataclass
class Position:
    strategy: str
    journal_id: int
    side: str
    entry_time: datetime
    entry_price: float
    size: float
    stop: Optional[float]
    target: Optional[float]


def utc_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, (int, float)):
        result = datetime.fromtimestamp(float(value), tz=timezone.utc)
    else:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def iso(value: Any) -> str:
    return utc_datetime(value).isoformat()


def number(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def closed_candles(candles: Iterable[Candle], now: Optional[datetime] = None) -> list[Candle]:
    now = now or datetime.now(timezone.utc)
    return sorted(
        (c for c in candles if utc_datetime(c.timestamp) + BAR_SIZE <= now),
        key=lambda c: utc_datetime(c.timestamp),
    )


def discover_strategies() -> Dict[str, Any]:
    """Load every concrete strategy module through strategy_factory."""
    import quant.strategies as strategy_package

    loaded: Dict[str, Any] = {}
    for module_info in sorted(pkgutil.iter_modules(strategy_package.__path__), key=lambda item: item.name):
        if module_info.name.startswith("_"):
            continue
        module_name = "quant.strategies." + module_info.name
        try:
            loaded[module_info.name] = factory.load_strategy(module_name)
        except Exception as exc:  # keep a single incompatible module from stopping all paper runs
            print(f"skip_strategy={module_info.name} reason={type(exc).__name__}:{exc}", file=sys.stderr)
    if not loaded:
        raise RuntimeError("no loadable strategies found in quant.strategies")
    return loaded


def load_positions(conn) -> Dict[str, Position]:
    rows = conn.execute(
        "SELECT id, account_id, entry_time, entry_price, size, direction, stop_loss, profit_target "
        "FROM trades WHERE symbol=? AND status='open' AND account_id LIKE 'paper:%' ORDER BY id",
        (SYMBOL,),
    ).fetchall()
    positions: Dict[str, Position] = {}
    for row in rows:
        strategy = str(row["account_id"])[len("paper:"):]
        if strategy in positions:
            continue
        positions[strategy] = Position(
            strategy=strategy,
            journal_id=int(row["id"]),
            side=str(row["direction"]),
            entry_time=utc_datetime(row["entry_time"]),
            entry_price=float(row["entry_price"]),
            size=float(row["size"] or 1.0),
            stop=number(row["stop_loss"]),
            target=number(row["profit_target"]),
        )
    return positions


def load_state(path: Path) -> Optional[datetime]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        value = payload.get("last_closed_candle")
        return utc_datetime(value) if value else None
    except (FileNotFoundError, OSError, ValueError, TypeError):
        return None


def save_state(path: Path, timestamp: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps({"symbol": SYMBOL, "interval": INTERVAL, "last_closed_candle": timestamp.isoformat()}),
        encoding="utf-8",
    )
    temporary.replace(path)


def strategy_levels(signal: Dict[str, Any], side: str, entry: float) -> Tuple[Optional[float], Optional[float]]:
    stop = number(signal.get("stop", signal.get("stop_loss")))
    target = number(signal.get("target", signal.get("profit_target", signal.get("take_profit"))))
    if stop is not None and ((side == "long" and stop >= entry) or (side == "short" and stop <= entry)):
        stop = None
    if target is not None and ((side == "long" and target <= entry) or (side == "short" and target >= entry)):
        target = None
    return stop, target


def open_position(
    conn,
    strategy: str,
    signal: Dict[str, Any],
    candle: Candle,
    positions: Dict[str, Position],
    killcheck: bool,
) -> bool:
    side = str(signal.get("side", "")).lower()
    if side not in ("long", "short") or strategy in positions:
        return False
    if killcheck:
        try:
            kill_switch.require_clear("paper_trading")
        except kill_switch.KillSwitchArmed as exc:
            print(f"strategy={strategy} action=blocked reason=kill_switch")
            return False
    entry_price = float(candle.close)
    size = number(signal.get("quantity", signal.get("size", 1.0))) or 1.0
    stop, target = strategy_levels(signal, side, entry_price)
    entry_time = iso(candle.timestamp)
    entry_fee = entry_price * size * MAKER_FEE_PER_SIDE
    payload = {
        "account_id": "paper:" + strategy,
        "symbol": SYMBOL,
        "asset_class": "crypto",
        "direction": side,
        "status": "open",
        "entry_time": entry_time,
        "exit_time": None,
        "size": size,
        "entry_price": entry_price,
        "exit_price": None,
        "stop_loss": stop,
        "profit_target": target,
        "fees": entry_fee,
        "gross_pnl": None,
        "net_pnl": None,
        "currency": "USDT",
        "screenshot_path": None,
        "tags": "paper_trader,strategy=" + strategy,
        "mistakes": None,
        "playbook": strategy,
        "notes": "simulated entry; maker fee per side=0.0002",
        "rating": 0,
        "reviewed": 0,
    }
    journal_id = int(journal.insert(conn, payload))
    positions[strategy] = Position(strategy, journal_id, side, utc_datetime(candle.timestamp), entry_price, size, stop, target)
    print(
        f"candle={iso(candle.timestamp)} strategy={strategy} action=entry side={side} "
        f"price={entry_price:.6f} stop={stop if stop is not None else '-'} target={target if target is not None else '-'}"
    )
    return True


def close_position(conn, position: Position, candle: Candle, price: float, reason: str, positions: Dict[str, Position]) -> None:
    sign = 1.0 if position.side == "long" else -1.0
    gross = sign * (float(price) - position.entry_price) * position.size
    fees = position.entry_price * position.size * MAKER_FEE_PER_SIDE + float(price) * position.size * MAKER_FEE_PER_SIDE
    net = gross - fees
    conn.execute(
        "UPDATE trades SET status='win' if ? > 0 else 'loss', exit_time=?, exit_price=?, fees=?, "
        "gross_pnl=?, net_pnl=?, notes=? WHERE id=?",
        (net, iso(candle.timestamp), float(price), fees, gross, net, f"simulated exit; reason={reason}; maker fee per side=0.0002", position.journal_id),
    )
    conn.commit()
    print(
        f"candle={iso(candle.timestamp)} strategy={position.strategy} action=exit side={position.side} "
        f"price={float(price):.6f} reason={reason} net={net:.6f}"
    )
    positions.pop(position.strategy, None)


def protective_exit(position: Position, candle: Candle) -> Optional[Tuple[float, str]]:
    if position.side == "long":
        if position.stop is not None and float(candle.low) <= position.stop:
            return position.stop, "stop"
        if position.target is not None and float(candle.high) >= position.target:
            return position.target, "target"
    else:
        if position.stop is not None and float(candle.high) >= position.stop:
            return position.stop, "stop"
        if position.target is not None and float(candle.low) <= position.target:
            return position.target, "target"
    if utc_datetime(candle.timestamp) >= position.entry_time + MAX_HOLD:
        return float(candle.close), "max_hold_45m"
    return None


def process_candle(conn, strategies: Dict[str, Any], positions: Dict[str, Position], candle: Candle, killcheck: bool) -> int:
    events = 0
    for name, strategy in strategies.items():
        position = positions.get(name)
        if position is not None:
            triggered = protective_exit(position, candle)
            if triggered is not None:
                close_position(conn, position, candle, triggered[0], triggered[1], positions)
                events += 1
                position = None
        try:
            signal = strategy.next(candle) or {"action": "hold"}
        except Exception as exc:
            print(f"candle={iso(candle.timestamp)} strategy={name} action=error reason={type(exc).__name__}:{exc}", file=sys.stderr)
            continue
        action = str(signal.get("action", signal.get("signal", "hold"))).lower()
        side = str(signal.get("side", "")).lower()
        if position is not None and action == "exit":
            close_position(conn, position, candle, float(candle.close), "strategy_exit", positions)
            events += 1
            position = None
        elif action == "enter" and side in ("long", "short"):
            if position is not None and position.side != side:
                close_position(conn, position, candle, float(candle.close), "reverse", positions)
                events += 1
            if open_position(conn, name, signal, candle, positions, killcheck):
                events += 1
    return events


def run_cycle(
    conn,
    strategies: Dict[str, Any],
    positions: Dict[str, Position],
    state_path: Path,
    killcheck: bool,
) -> None:
    fetched = factory.fetch_paginated(SYMBOL, INTERVAL, DEFAULT_LIMIT)
    candles = closed_candles(fetched)
    if not candles:
        print("cycle=paper_trader candles=0 events=0 open=0")
        return
    last_processed = load_state(state_path)
    to_process: list[Candle] = []
    for candle in candles:
        timestamp = utc_datetime(candle.timestamp)
        if last_processed is None:
            if timestamp < utc_datetime(candles[-1].timestamp):
                for strategy in strategies.values():
                    strategy.next(candle)
            else:
                to_process.append(candle)
        elif timestamp <= last_processed:
            for strategy in strategies.values():
                strategy.next(candle)
        else:
            to_process.append(candle)
    events = 0
    for candle in to_process:
        events += process_candle(conn, strategies, positions, candle, killcheck)
        save_state(state_path, utc_datetime(candle.timestamp))
    print(
        f"cycle=paper_trader symbol={SYMBOL} interval={INTERVAL} candles={len(to_process)} "
        f"events={events} open={len(positions)} last={iso(candles[-1].timestamp)}"
    )


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="process currently closed candles once (the default)")
    parser.add_argument("--loop", type=float, metavar="MINUTES", help="poll every MINUTES; overrides --once")
    parser.add_argument("--killcheck", action="store_true", help="require scripts/kill_switch.py to be clear before entries")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite journal path")
    parser.add_argument("--state", default=str(DEFAULT_STATE), help="last-candle state path")
    args = parser.parse_args(argv)
    if args.loop is not None and args.loop <= 0:
        parser.error("--loop MINUTES must be greater than zero")
    return args


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    strategies = discover_strategies()
    conn = journal.connect(args.db)
    positions = load_positions(conn)
    try:
        while True:
            try:
                run_cycle(conn, strategies, positions, Path(args.state), args.killcheck)
            except Exception as exc:
                print(f"cycle=paper_trader action=error reason={type(exc).__name__}:{exc}", file=sys.stderr)
                if args.loop is None:
                    return 1
            if args.loop is None:
                return 0
            time.sleep(args.loop * 60.0)
    except KeyboardInterrupt:
        print("cycle=paper_trader action=stopped reason=keyboard_interrupt")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
