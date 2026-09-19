# ICT / SMC / ORB research implementation

## Scope

This change adds deterministic, non-discretionary implementations under
`src/kyla_quant/strategies/`:

* **FVG**: bullish only when `candle1.high < candle3.low`; bearish only when
  `candle1.low > candle3.high`. The default retrace entry is the gap midpoint,
  the stop is beyond the gap, and the target is one gap-width measured move.
  An explicit higher-timeframe target can be supplied by a caller.
* **IFVG**: a formed gap must first be entered and then have a close through its
  far edge. The returned setup inverts direction and uses the opposite gap edge
  as the stop. It is not a label applied merely because a gap exists.
* **Order block**: the last opposite-direction candle before a displacement
  whose close-to-close move is greater than `displacement_atr * ATR` in
  `displacement_bars`. Default is ATR(14), 1.5 ATR, three bars. Entry is inside
  the candle, stop beyond its extreme, and target is a deterministic 1R move.
* **ORB**: first 15 UTC minutes beginning at London 09:00 and New York 14:30.
  The first post-range break is used, the opposite range edge is the stop, and
  the default target is 1R. Optional retest entry is supported. The latest
  exit is the earlier of 45 minutes after session open and 60 minutes after
  session open (the 45-minute cap therefore governs the default).
* **Sequence**: existing `SSS`, `BBB`, `BBS`, and `SSB` detection is wired into
  the same `ict_smc_orb.py` comparison path as `sequence_<pattern>` strategies.

The runner uses the same next-bar touch fill, stop-first same-bar policy, cost
model, IS/OOS split, and report schema for every concept. No parameters were
optimized by this change.

## Data and reproducibility

The runner obtains public Binance spot klines without authentication:

`https://api.binance.com/api/v3/klines`

Example command:

```bash
PYTHONPATH=src python -m kyla_quant.backtest.ict_smc_orb \
  --symbol SOLUSDT --interval 5m --days 365 \
  --commission 0.0005 --spread-bps 1 --slippage-bps 1
```

It paginates at Binance's 1,000-row limit and records fetch time, exact first
and last UTC timestamps, symbol, interval, and row count in the JSON report.
A 1m run is also supported. `GC=F` is only an optional Yahoo Finance/yfinance
gold proxy and must be labeled as a proxy, not XAUUSD:
`https://finance.yahoo.com/quote/GC%3DF/history`. If yfinance is absent or
returns no rows, the runner reports gold as PENDING rather than fabricating it.
OANDA is not called by this repository runner; practice-token execution remains
PENDING unless separately configured and explicitly run.

## Cost and formulas

Default costs are always on: 0.05% commission per side, 1 bp spread per side,
and 1 bp slippage per side. For a trade with entry `E`, exit `X`, stop `S`,
and direction sign `d` (+1 long, -1 short):

* raw R = `d * (X - E) / abs(E - S)`;
* round-trip price cost = `2 * (commission + spread_bps/10000 + slippage_bps/10000)`;
* cost R = `E * round_trip_price_cost / abs(E - S)`;
* measured net R = raw R - cost R;
* expectancy = mean(net R);
* profit factor = sum(positive net R) / abs(sum(negative net R));
* max drawdown = largest peak-to-trough decline of cumulative net R;
* win rate = positive-net-R trades / completed trades.

If a bar reaches both stop and target, stop is taken first. Setups are entered
only after formation and only when a later OHLC bar touches the entry. This is
conservative but still an OHLC-bar approximation; it is not tick data.

## Limitations and hypotheses

This implementation does not infer discretionary liquidity, news, spread
regimes, or a broker's XAUUSD feed. Binance spot klines are not futures and do
not represent OANDA execution. UTC session boundaries are explicit. Any future
rebuild should change one parameter at a time and require a fresh untouched OOS
run; examples are ATR threshold, entry ratio, ORB retest flag, or cost model,
not a license to search combinations until they pass.
