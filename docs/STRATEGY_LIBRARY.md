# Strategy library (exploratory)

This batch adds eight distinct stdlib-only 5-minute research strategies without replacing existing strategies. Each module has a one-paragraph logic/edge caveat in its module docstring. All use protective stops, targets, and a roughly 45-minute maximum hold; the opening-range and session strategies prefer 09:00-16:00 EAT where applicable.

## Evaluation protocol

The intended command is `python scripts/strategy_factory.py`, which installs the same **demo-only unverified urllib SSL opener** used by the existing demo scripts before fetching Binance public `SOLUSDT` klines. It paginates at most 1,000 rows per request and defaults to 20,000 candles of 5m data. The backtest uses the repository's actual `quant.backtest.Backtester`, `BINANCE_SOL_MAKER` costs (0.02% commission per side), zero configured spread/slippage, initial capital 10,000, and quantity 1.0. The factory's win-rate sanity check requires `0 <= win_rate <= 1` and wins + losses + flat trades to equal the trade count. The research thresholds are at least 200 trades, net profit > 0, profit factor > 1.15, and max drawdown < 20% of peak equity.

The factory was **not executable in this GitHub-only tool environment**: no local Python/network execution tool was available, so no Binance data was fetched and no backtest output was produced on 2026-09-20 UTC. The table therefore records no fabricated metrics. Dataset/date for this recorded run: **none fetched; no backtest date range available**. Costs/configuration are the intended protocol above, not realized results. `INCONCLUSIVE` means insufficient observed evidence, never validated.

| Name | File | Timeframe | Trades | Win rate | PF | Net profit | Max DD | Expectancy R | Verdict | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Momentum breakout | `quant/strategies/momentum_breakout.py` | 5m | — | — | — | — | — | — | INCONCLUSIVE | Not run: no local Python/network execution tool. |
| Opening-range breakout | `quant/strategies/opening_range_breakout.py` | 5m | — | — | — | — | — | — | INCONCLUSIVE | Not run; EAT range logic is documented in source. |
| Rolling VWAP-ish mean reversion | `quant/strategies/rolling_vwap_mean_reversion.py` | 5m | — | — | — | — | — | — | INCONCLUSIVE | Not run: no data fetched. |
| RSI(2) reversal | `quant/strategies/rsi2_reversal.py` | 5m | — | — | — | — | — | — | INCONCLUSIVE | Not run: no data fetched. |
| Volume-confirmed breakout | `quant/strategies/volume_confirmed_breakout.py` | 5m | — | — | — | — | — | — | INCONCLUSIVE | Not run: no data fetched. |
| EMA-cross trend with ATR stop | `quant/strategies/ema_cross_atr.py` | 5m | — | — | — | — | — | — | INCONCLUSIVE | Not run: no data fetched. |
| Session high/low breakout | `quant/strategies/session_high_low_breakout.py` | 5m | — | — | — | — | — | — | INCONCLUSIVE | Not run; 09:00-16:00 EAT filter is documented in source. |
| Donchian scalp | `quant/strategies/donchian_scalp.py` | 5m | — | — | — | — | — | — | INCONCLUSIVE | Not run: no data fetched. |

## Second iteration candidates

None can be selected responsibly from this batch because there are no actual metrics. A second iteration should be chosen only after the factory has produced real, reproducible output, then reviewed for trade-count sufficiency, costs, drawdown, regime sensitivity, and out-of-sample behavior. These exploratory results are not proof of profitability or validation.
