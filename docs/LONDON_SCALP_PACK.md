# London Scalp Pack

This pack contains three **pure Python standard-library** signal generators:

- `quant/strategies/asian_range_breakout.py`
- `quant/strategies/gold_killzone_scalp.py`
- `quant/strategies/sol_micro_scalp.py`

The originally named `london_orb.py` and `backtest.py` paths are absent. The
actual repository strategy code is in `src/kyla_quant/strategies/`, and the
actual runner is `src/kyla_quant/backtest/backtesting_py_runner.py`.
Existing strategies there are deterministic detectors and data classes (for
example `Bar`, `detect_fvgs`, and `detect_orb_setups`). The runner's actual
contract is a strategy with `fit(data)` and `evaluate(data, costs=...)`, plus a
walk-forward split and cost validation. Each new class implements that
contract and also provides the requested streaming `next(candle) -> Signal |
None` adapter. The module-level `next(candle)` is only a convenience; use a
class instance for isolated state.

## Candle and signal contract

A candle may be a mapping or object with `timestamp`, `open`, `high`, `low`,
and `close`. `volume` and `spread` are optional where stated. Use an aware
`datetime` or ISO-8601 timestamp. Naive timestamps are treated as UTC. Signals
contain action, entry, stop, target, timestamp, reason, and risk multiple.
They are not orders: execution must re-check quote freshness, tick size,
margin, exchange rules, position state, and actual fills.

`fit` is deliberately a no-op because these are fixed, auditable rules, not
fitted models. `evaluate` resets the stream and returns status, signals, count,
and the supplied costs object. It does not claim profitability or simulate
fills. The repository runner remains responsible for a train/test split,
minimum-cycle gate, and report.

## DST-aware clocks

EAT is `Africa/Nairobi` (UTC+03:00, no DST). London and New York are resolved
with `zoneinfo`, never by adding a fixed offset.

| Setup/window | Local rule | UTC winter | UTC summer | EAT winter / summer |
|---|---|---|---|---|
| Asian range | 00:00-06:00 EAT | 21:00-03:00, crosses UTC date | same | 00:00-06:00 / 00:00-06:00 |
| London kill zone | 08:00-10:00 Europe/London | 08:00-10:00 GMT | 07:00-09:00 BST | 11:00-13:00 / 10:00-12:00 |
| New York kill zone | 08:30-10:30 America/New_York | 13:30-15:30 EST | 12:30-14:30 EDT | 16:30-18:30 / 15:30-17:30 |
| SOL micro window | 15:30-18:00 EAT | 12:30-15:00 | same | 15:30-18:00 |

The displayed winter/summer dates are explanatory; `zoneinfo` is authoritative
on the actual UK/US transition days. EAT windows do not move with DST.

## Strategy rules

### 1. Asian range breakout

1. Build the high and low from 00:00 through 06:00 EAT, inclusive of bars
   beginning in that interval and exclusive of 06:00.
2. Ignore an absent/zero range and reject a range wider than 2% of its
   midpoint. This avoids treating a data gap or extreme event as a normal
   breakout.
3. During 08:00-10:00 London local time, wait for a candle close above the
   range high (long) or below the range low (short).
4. Default behavior requires a later touch of the broken edge that closes
   back in the breakout direction. Set `require_retest=False` only when an
   explicit close-break test is intended.
5. Entry is the confirmation candle close. Stop is the opposite range edge
   plus the configured buffer on the safe side. Target is 2R by default.
6. Only one signal is emitted per EAT day; no chasing outside the window.

### 2. Gold kill-zone scalp

1. Use previous completed EAT-day high and low as liquidity references; the
   first day in a sample is intentionally untradeable until a reference
   exists.
2. In London or New York kill zone, a bullish setup sweeps the prior low and
   closes back above it. A bearish setup sweeps the prior high and closes
   back below it.
3. A later candle must displace through the preceding candle's high/low in
   the sweep direction and have body size at least `displacement_atr * ATR`.
   ATR uses prior observed ranges only; there is no look-ahead.
4. The sweep expires after `confirmation_bars` (default 3). Entry is the
   displacement close; stop is beyond the sweep extreme; target is 1.5R.
5. At most one trade per kill zone. An optional absolute `spread` field is
   rejected above `max_spread`. The implementation does not pretend to know
   news, fills, or broker spread when those fields are absent; production
   callers must add those gates.

### 3. SOL micro scalp

1. Use the fixed 15:30-18:00 EAT window (12:30-15:00 UTC) so this crypto
   window does not drift with London/New York DST.
2. Maintain session VWAP from positive-volume bars and fast/slow EMA defaults
   of 9/21. Long requires close above VWAP, fast EMA above slow EMA, and a
   break of the previous candle high. Short is mirrored below VWAP/EMAs and
   the previous low.
3. Require at least `min_volume` and, when supplied, reject spread above
   `max_spread`. Stop distance is `0.8 * ATR` (or a conservative fallback for
   a cold start); target is 1.2R.
4. Limit to three trades per EAT day with a three-bar cooldown. Never widen a
   stop, average down, or infer leverage, quantity, liquidation, or fees.

## Risk policy (mandatory before live use)

- Treat these as research/paper signals, not financial advice or a promise of
  edge. Start in replay, then paper trading, then the smallest permitted
  live size only after verification.
- Size from the actual stop: `quantity = account_risk_cash / abs(entry-stop)`.
  Include commission, spread, slippage, funding/borrow cost, and contract
  multiplier. A signal's R target is not a guaranteed fill.
- A conservative initial policy is 0.25%-0.50% account risk per trade, 1%
  maximum realized daily loss, one open position per symbol, and no more than
  two correlated positions. Stop for the day after the loss limit; do not
  martingale, revenge trade, or move a stop farther away.
- Reject stale/out-of-session candles, impossible OHLC, non-positive risk,
  missing volume where required, excessive spread, abnormal range, and any
  duplicate signal. Add an economic-calendar blackout for high-impact USD,
  GBP, and gold events; this code cannot discover news by itself.
- For crypto, separately enforce exchange maintenance, liquidation distance,
  leverage, funding, mark/index-price divergence, and websocket freshness.
  For XAUUSD/FX, separately enforce lot size, session liquidity, and broker
  trading hours.

## Verification checklist

1. Syntax/import check with no third-party packages:

   ```bash
   python -m compileall -q quant src
   python - <<'PY'
   from quant.strategies import AsianRangeBreakout, GoldKillzoneScalp, SolMicroScalp
   for cls in (AsianRangeBreakout, GoldKillzoneScalp, SolMicroScalp):
       s = cls(); assert hasattr(s, "next") and hasattr(s, "fit") and hasattr(s, "evaluate")
   print("imports and interfaces ok")
   PY
   ```

2. Feed deterministic synthetic candles with aware UTC timestamps. Assert the
   Asian setup cannot signal before its range is complete, each strategy keeps
   its stated daily/session cap, every signal has positive stop distance, and
   every timestamp is in its configured window.
3. Test a London winter date and a London summer date, and the corresponding
   New York dates. Compare `astimezone(ZoneInfo(...))` rather than hard-coded
   UTC offsets. Include the US/UK DST transition weeks and the Asian range's
   UTC-date crossing.
4. Run `run_walk_forward` from
   `kyla_quant.backtest.backtesting_py_runner` with a validated non-zero cost
   model and enough chronological observations for the minimum-cycle gate.
   Keep train and test data strictly time ordered; never fit on the test set.
5. Verify no look-ahead: ATR/reference levels use only prior bars, a breakout
   uses a closed candle, and the runner's test result is out of sample.
6. Report trade count, win rate, expectancy after costs, max drawdown, daily
   loss breaches, average slippage, rejected signals, and results separately
   for winter/summer and each symbol. Do not promote based on win rate alone;
   require a pre-declared out-of-sample threshold and a forward paper period.
7. Log input timestamp, normalized UTC timestamp, session, reference levels,
   spread/volume, entry/stop/target, rejection reason, fill, fees, and code
   commit SHA so every signal can be replayed.
