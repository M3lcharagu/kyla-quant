# KYLA Trading Journal

`scripts/trade_journal.py` is a network-free, standard-library-only Python 3.9 CLI. By default it creates/uses `journal/trades.db` relative to the repository root. The database directory and SQLite file are local runtime state and are ignored by the repository's SQLite rules.

## Quick start

```bash
python3 scripts/trade_journal.py add
python3 scripts/trade_journal.py add --json '{"symbol":"BTCUSDT","direction":"long","entry_time":"2026-09-20T10:00:00Z","entry_price":65000,"size":0.01,"stop_loss":64000,"profit_target":67000,"currency":"USDT","tags":"breakout"}'
python3 scripts/trade_journal.py report
```

`add` without `--json` prompts for every field. `--json` accepts an object, `@path/to/trade.json`, or `-` for JSON on stdin. The optional global `--db PATH` is useful for a temporary smoke test, for example:

```bash
python3 scripts/trade_journal.py --db /tmp/kyla-journal.db add --json '{"symbol":"ETHUSDT","direction":"short","entry_price":2000,"exit_price":1900,"size":1,"fees":2}'
python3 scripts/trade_journal.py --db /tmp/kyla-journal.db report
```

## Import and backup

Import detects `.json` versus CSV by extension; use `--format` when reading stdin or an unusual filename. JSON may be a list of trade objects or an object containing `trades`, `data`, `rows`, `results`, or `items`. CSV/JSON field names are normalized and common LuxAlgo exports are supported, including aliases such as `Ticker`/`Symbol`, `Side`/`Direction`, `Quantity`/`Size`, `Open Time`/`Entry Time`, `Close Time`/`Exit Time`, `Open Price`/`Entry Price`, `Close Price`/`Exit Price`, `SL`, `TP`, `Commission`, `P&L`, `Net P&L`, `Setup`, and `Comments`. `buy`/`sell` and common result labels are normalized too.

```bash
python3 scripts/trade_journal.py import luxalgo-export.csv
python3 scripts/trade_journal.py import luxalgo-export.json --format json
python3 scripts/trade_journal.py export --format csv --output journal/trades-backup.csv
python3 scripts/trade_journal.py export --format json --output journal/trades-backup.json
```

Imports continue past bad rows and report skipped row numbers. Export includes the database `id` and all schema columns, making CSV/JSON suitable for a human-readable backup. No network access, API key, SSL workaround, or third-party package is used.

## Reports and open trades

`report` prints net P&L, trade win percentage, profit factor, day win percentage, average win, average loss, trade count, total fees, expectancy, and the KYLA Edge Score. A trade is treated as open when its status is `open` and it has no P&L; open trades are excluded from closed-trade performance rates. Null `exit_time`, `gross_pnl`, and `net_pnl` are therefore valid. P&L is derived from entry/exit price and size when possible, with short trades using the inverse price change; missing exit data remains null. Fees default to zero and net P&L defaults to gross P&L minus fees.

The KYLA Edge Score is an original transparent composite, not LuxAlgo's: 35% trade-win rate, 25% profit-factor component `PF/(PF+1)` scaled to 100, 20% day-win rate, 10% reviewed-trade rate, and 10% expectancy quality (100 for positive expectancy, 50 for zero, 0 for negative). Open trades are excluded from these rates; with no closed P&L the score is 0.

## Complete schema

The SQLite table is `trades`. Times are stored as text so ISO-8601 timestamps, dates, or source-specific timestamps can be retained without timezone assumptions. Monetary and size values are SQLite `REAL`; `rating` is an integer; `reviewed` is `0` or `1`.

| Column | SQLite type | Null/default | Meaning |
|---|---|---|---|
| `id` | INTEGER | primary key | Auto-incrementing trade identifier; preserved when importing a non-conflicting backup ID. |
| `account_id` | TEXT | nullable | Account, portfolio, or broker identifier. |
| `symbol` | TEXT | required | Instrument/ticker. |
| `asset_class` | TEXT | nullable | Crypto, forex, equity, futures, etc. |
| `direction` | TEXT | required | Exactly `long` or `short`; imports also accept buy/sell. |
| `status` | TEXT | `open` | Exactly `open`, `win`, `loss`, or `breakeven`. |
| `entry_time` | TEXT | nullable | Entry/open timestamp or date. |
| `exit_time` | TEXT | nullable | Exit/close timestamp or date; null for open trades. |
| `size` | REAL | nullable | Quantity, contracts, or position size. |
| `entry_price` | REAL | nullable | Average entry price. |
| `exit_price` | REAL | nullable | Average exit price. |
| `stop_loss` | REAL | nullable | Planned stop-loss price. |
| `profit_target` | REAL | nullable | Planned take-profit price. |
| `fees` | REAL | `0` | Commission, fees, or other trading costs. |
| `gross_pnl` | REAL | nullable | P&L before fees; may be derived from price and size. |
| `net_pnl` | REAL | nullable | P&L after fees; null is valid for open trades. |
| `currency` | TEXT | nullable | P&L/quote currency. |
| `screenshot_path` | TEXT | nullable | Local screenshot or chart path; no file is uploaded. |
| `tags` | TEXT | nullable | Comma-separated labels or source labels. |
| `mistakes` | TEXT | nullable | Rule breaks or execution mistakes. |
| `playbook` | TEXT | nullable | Setup, strategy, or playbook name. |
| `notes` | TEXT | nullable | Free-form journal notes/comments. |
| `rating` | INTEGER | nullable | Optional post-trade rating. |
| `reviewed` | INTEGER | `0` | `1` if reviewed, otherwise `0`. |
