# Backtest results

## Run status

**Status: INCONCLUSIVE — no measured backtest is claimed in this commit.**

Exact task execution timestamp supplied by the connected execution environment:
`2026-09-19T13:45:35Z` (UTC). The GitHub integration could inspect and commit
repository files, but it does not provide a local Python interpreter, shell,
network HTTP client for Binance, or a notebook runtime to execute the new
runner. Therefore this report contains no invented row counts, timestamps,
trade counts, win rates, profit factors, expectancy, drawdown, or session
results. The first real run must be produced by the command below and its JSON
stdout should be preserved with the run timestamp.

## Required measured run

```bash
python -m pip install -r requirements.txt
PYTHONPATH=src python -m kyla_quant.backtest.ict_smc_orb \
  --symbol SOLUSDT --interval 5m --days 365 \
  --commission 0.0005 --spread-bps 1 --slippage-bps 1 > backtest-results.json
```

The same command with `--interval 1m` is supported. The runner fetches actual
public Binance klines from `https://api.binance.com/api/v3/klines`, records
`fetched_at_utc`, `first_timestamp_utc`, `last_timestamp_utc`, and `row_count`,
and evaluates FVG, IFVG, order block, ORB London, ORB New York, and each
sequence pattern through one cost-aware path. It reports all, IS (70%), OOS
(30%), and London/New York/other session results.

## Results table

No table cells are populated because no data fetch or computation occurred in
this connected environment. This is intentional and is the exact result of the
200-trade gate policy.

| Strategy/concept | Dataset | Rows / timestamps | Trades | Win rate | Profit factor | Net expectancy (R) | Max DD (R) | IS vs OOS | Session results | Status / exact reason |
|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| FVG | SOLUSDT Binance 5m | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | INCONCLUSIVE — computation and data fetch unavailable |
| IFVG | SOLUSDT Binance 5m | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | INCONCLUSIVE — computation and data fetch unavailable |
| Order block | SOLUSDT Binance 5m | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | INCONCLUSIVE — computation and data fetch unavailable |
| ORB London | SOLUSDT Binance 5m | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | INCONCLUSIVE — computation and data fetch unavailable |
| ORB New York | SOLUSDT Binance 5m | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | INCONCLUSIVE — computation and data fetch unavailable |
| SSS / BBB / BBS / SSB sequence path | SOLUSDT Binance 5m | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | INCONCLUSIVE — computation and data fetch unavailable |
| Gold proxy (`GC=F`) | Yahoo Finance/yfinance | NOT RUN; proxy only | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | INCONCLUSIVE — optional yfinance/OANDA access not executed |

A strategy is not PASS merely because it has positive expectancy: the runner's
status is INCONCLUSIVE below 200 completed trades. OANDA practice research is
also PENDING unless a configured practice token is deliberately used; no access
or result is claimed here.

## Known execution limitations

* No local computation or external-data execution tool was available through the
  connected GitHub environment, so tests and the real backtest were not run.
* `yfinance` is optional and was not used; `GC=F` is not spot XAUUSD.
* Binance spot klines are public market data, not broker fills; spread and
  slippage are explicit configured assumptions, not measured order-book costs.
* The runner uses OHLC bars, a conservative stop-first same-bar rule, and a
  next-bar touch entry. It does not claim tick-level execution.
* OANDA practice status is PENDING, not successful.

## Commands intended for validation

The implementation should be syntax-checked and run in a network-enabled clone
with the commands above. A future report must include the command, exact UTC
run time, data provenance, every measured metric, and any error output. Any
rebuild suggestion must alter one parameter only and require a new untouched
OOS validation.
