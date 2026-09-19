# London Scalp Pack

Research/paper signals only. The executor must re-check quote freshness, tick size, margin, broker/exchange rules, position state, fills, fees and news before acting.

## Interface and paths

The requested bare `london_orb.py` and `backtest.py` paths are absent at repository root and are not an interface to invent. The checked tree's similarly named modules are `quant/strategies/london_orb.py` and `quant/backtest.py`. The amended stream modules are `quant/strategies/asian_range_breakout.py`, `quant/strategies/gold_killzone_scalp.py`, and `quant/strategies/sol_micro_scalp.py`; each is stdlib-only and exposes `next(candle) -> Signal | None`, plus class methods `next`, `fit`, and `evaluate`. Signal fields are `action`, `entry`, `stop`, `target`, `timestamp`, `reason`, and `risk_r`; gold and SOL add metadata. The repository runner/data contract remains the actual `quant` and `src/kyla_quant` code, not a claimed missing root file.

## Clock and window

- Available window: **09:00-16:00 EAT**, `Africa/Nairobi`, UTC+3 year-round.
- London open: **10:00 EAT in BST / 11:00 EAT in GMT**, equal to **07:00 / 08:00 UTC**.
- US cash open is **18:30 EAT**; therefore NAS100 ORB is excluded.
- Use `zoneinfo`, never a hard-coded London offset.

## Hour-by-hour map

| EAT | What is live | Status |
|---|---|---|
| 09:00 | Pre-London quiet: prepare levels, data and news gates; no scheduled FX/gold entry, while SOL is 24/7. | FILTERED |
| 10:00 | London open 10:00-10:30: GBPUSD ORB range is 10:00-10:15 then breakout/retest; USDJPY and XAUUSD can become live, subject to UK data gates. | TRADE |
| 11:00 | AM momentum 10:30-12:00: GBPUSD priority candidate, USDJPY and XAUUSD remain eligible under their gates. | TRADE |
| 12:00 | Late AM momentum: GBPUSD remains eligible; XAUUSD remains live through 13:00. | TRADE |
| 13:00 | GBPUSD expires at 13:00; lunch lull begins. No new GBPUSD/gold entries; USDJPY is also lunch-filtered until 14:00. | STAND DOWN |
| 14:00 | PM drift 14:00-16:00: scheduled FX/gold entries are closed; manage approved trades only, with SOL still 24/7. | FILTERED |
| 15:00-16:00 | PM drift continues; no new London FX/gold setup. SOL remains live only with its funding, ATR and BTC-dump gates. | FILTERED |

## Four strategies

1. **GBPUSD London ORB (priority candidate).** Build the 15-minute range from **10:00-10:15 EAT (07:00-07:15 UTC)**, then require breakout plus retest, stop beyond the range, target **2R**, and invalidate at **13:00 EAT**. This is the narrative priority candidate; do not claim a new `london_orb.py` root path when integrating it with the actual repository interface.
2. **USDJPY Asian range.** Build the range **03:00-10:00 EAT (00:00-07:00 UTC)**. Accept a **5-minute close breakout** only from **10:00-14:00 EAT**, stop at the range extreme, use configurable fixed-R target, and lock entries on BoJ intervention/rate-check headlines.
3. **XAUUSD killzone FVG.** During **10:00-13:00 EAT**, require an Asian high/low liquidity sweep, displacement, then FVG retrace; stop beyond the sweep and target opposing liquidity or fixed R. A live spread is mandatory; skip spread **>2x rolling median** and reject missing live spread or median.
4. **SOL 24/7 Binance futures maker-side.** Target **0.5-1%**, hold **30-45 minutes max**, require a funding check, reject compressed ATR, reject BTC candle dumps, and price maker fee **0.02% per side** (`0.0002`) in cost math. There is no fixed EAT session.

## Stand-down rules

Stand down for UK CPI/GDP/BoE speeches, spread widening over the configured gate, the thin **13:00-14:00 EAT** lunch, and red-news overlap. GBPJPY is allowed only when the target is **at least 20 pips**. Do not force a trade to fill a schedule.

## Risk

Use fixed fractional risk of **0.5-1% per strategy**, maximum **2 concurrent** positions, never hold GBPUSD and GBPJPY both long, and apply a daily kill switch at **-3R**. The **$150/week trailing target on $5k stays**; it is a tracking target, not a reason to increase risk.

## Verification table

| Strategy | Public data now | Required data/token | 200-trade gate |
|---|---|---|---|
| GBPUSD London ORB | No verified public stream in this pack | OANDA practice token Mel creates | 200 trades minimum |
| USDJPY Asian range | No verified public stream in this pack | OANDA practice token Mel creates | 200 trades minimum |
| XAUUSD killzone FVG | No verified public stream in this pack | OANDA practice token Mel creates, live spread and rolling median | 200 trades minimum |
| SOL Binance futures | Binance klines = yes | Funding and BTC dump feed/check | 200 trades minimum |
| NAS100 ORB | Excluded: US cash open is 18:30 EAT | None | Not applicable |

No strategy is promoted on win rate alone. Log timestamps, normalized EAT/UTC time, levels, spread/median, funding, fees, rejection reasons, fills and this commit SHA; keep train/test data chronological and out of sample.
