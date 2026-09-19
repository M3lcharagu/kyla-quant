"""SQLite trade journal schema with full audit-oriented fields."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id TEXT NOT NULL UNIQUE,
    cycle_id TEXT,
    sequence_type TEXT,
    venue TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT,
    side TEXT NOT NULL,
    status TEXT NOT NULL,
    opened_at TEXT,
    closed_at TEXT,
    entry_price REAL,
    exit_price REAL,
    stop_price REAL,
    target_price REAL,
    quantity REAL,
    risk_fraction REAL,
    risk_amount REAL,
    realized_pnl REAL,
    realized_r REAL,
    spread_cost REAL,
    slippage_cost REAL,
    commission_cost REAL,
    total_cost REAL,
    exit_reason TEXT,
    time_in_trade_seconds INTEGER,
    data_snapshot_id TEXT,
    strategy_version TEXT,
    config_hash TEXT,
    stance TEXT,
    event_lock INTEGER NOT NULL DEFAULT 0,
    kill_switch INTEGER NOT NULL DEFAULT 0,
    mel_approval TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def initialize(path: str | Path) -> sqlite3.Connection:
    """Create the local journal database; credentials are never stored here."""
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.execute(SCHEMA)
    connection.commit()
    return connection
