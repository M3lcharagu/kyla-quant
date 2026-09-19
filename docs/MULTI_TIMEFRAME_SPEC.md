# KYLA Multi-Timeframe Strategy Research & Timeframe-Stacking Specification

Status: research design; no performance claim is approved until KYLA's own net-of-cost walk-forward tests pass. Date: 2026-09-19.

**Label:** Specification/research note only; not financial advice and not validated performance.

## Executive verdict

**USEFUL:** top-down analysis is a documented, testable architecture: completed higher-timeframe trend/regime filter, then lower-timeframe structure and entry trigger. It is a hypothesis, not a universal edge. The strongest directly reproducible public example found is Quantpedia's BTC D1/H1 MACD filter: BTC/USD Gemini, Dec 2018-Nov 2025; H1 MACD-only reported 2,262 trades, 4.6% annual return, Sharpe 0.33, Calmar 0.19, max drawdown -23.9%; adding a completed daily MACD direction filter reported about 1,000 trades, 6.6% annual return, Sharpe 0.80, max drawdown -12.4%; the final trailing-stop version reported Sharpe 1.07 and Calmar 0.87. Transaction costs were not specified, so this is evidence of a design pattern, not validated net performance.

**USEFUL WITH CAUTION:** Tradeciety documents weekly->daily/4H, daily->4H/1H or 30m/15m, 4H->30m/15m, and 1H->15m/5m or 5m/1m; it says higher timeframe sets sentiment/context/bias and lower timeframe times entries, and permits neutral/stand-down conditions. This is educational documentation, not peer-reviewed evidence. Backtrex gives useful anti-lookahead guidance: only the last fully closed HTF bar, align it to the next LTF bar, and use `request.security()` with `barmerge.lookahead_off` and `close[1]` in Pine; it recommends 3-5 years, 20-30% OOS, >=100 trades, multiple regimes/instruments, and simple parameterization, but does not provide cost evidence.

**SKIP as an entry signal for now:** 30-second bars. Public evidence located does not establish robust, net-of-cost 30s profitability for XAUUSD CFDs or SOL API execution. Use 30s only for pre-registered management/execution observability until a tick/event-level, bid/ask, latency-aware test proves otherwise.

## Research evidence

### Documented top-down methods

- Tradeciety: start on HTF for sentiment, trend, levels and bullish/bearish/neutral bias; use LTF for a directional entry. Examples include HTF breakout, bounce, fakeout, candlestick and chart-pattern bias followed by an LTF confirmation. It says keep one combination consistent for at least 30-50 trades. Useful architecture, not causal proof.
- Backtrex: HTF trend filter (e.g. 4H/daily) + LTF entry (e.g. 15m/1H); never use an unfinished HTF candle. Signal only after HTF close and act on the next LTF bar. Its validation advice is useful for KYLA but is not a published performance result.
- Quantpedia BTC example above: completed daily MACD direction -> hourly MACD entry improved reported Sharpe/drawdown versus hourly-only in its stated sample, but costs were not stated and the article's result is not independently validated here.
- Available academic/research leads (ResearchGate/SSRN) discuss multi-timeframe rule generation and crypto signal confirmation, but the search did not verify a reproducible, net-of-cost XAUUSD/NQ/SOL result. Do not cite these as proof.

### XAUUSD/NQ/crypto evidence quality

No public source found supplied a single reproducible strategy with exact KYLA SSS/BBB/BBS/SSB rules, exact FVG/OB/ORB definitions, bid/ask costs, slippage, latency, dates and trade list for all three markets. Reported internet figures such as XAUUSD 58-64% win rate / PF 1.45-1.78, NQ PF 1.35-1.65 and crypto 48-54% / PF 1.35-1.62 are incomplete, non-comparable reports and are **SKIP** as validation. KYLA must generate its own trade-level results.

### 30-second evidence and honest verdict

At 30s holding periods, spread, commission, slippage, queue position, partial fills, latency and price sequencing inside candles can be as large as the signal. One-minute OHLC is inadequate when stop and target can both be touched; fills at mid, zero latency, fixed spread and automatic limit fills are optimistic. Credible testing requires tick/event data, separate bid/ask, time-varying spread, commissions/financing/venue fees, randomized or calibrated slippage, latency delay, partial/rejected fills, queue assumptions, OOS/walk-forward and execution replay.

**XAUUSD cost references:** Pepperstone's official pricing page states Standard gold CFD spreads and 0.15 points, with no commission (other than overnight funding), and Razor raw XAU/USD spreads from 0.08 plus commission from $3.50 per lot per side; it says pricing data covered 2026-08-01 through 2026-08-31 and varies by account/market. XM lists GOLD average spread 3.0 pips and as low as 2.4 pips, but does not explain pip convention/account type. These are broker-specific, not universal 'typical' spreads; news/rollover can widen them.

**SOL cost reference:** Binance official fee page states Regular User spot base 0.100% maker / 0.100% taker, or 0.07500% / 0.07500% with the listed 25% BNB discount; fee tier depends on account/volume. API has no magic exemption. A SOL spread is live order-book state, not fixed.

### Break-even math (price/percentage units)

Let `T` = gross target distance, `L` = gross stop distance, and `C` = all-in round-trip cost in the same units: spread + commissions + expected slippage + latency/impact allowance + any applicable funding/fees. For symmetric `T=L`, the win-rate break-even is:

`p_BE = (T + C) / (2T) = 0.50 + C/(2T)`

For asymmetric distances:

`p_BE = (L + C) / (T + L)`

These formulas assume fixed costs and no additional selection bias; real results need trade-level simulation.

Illustrative XAUUSD scenarios, not claims about a universal typical quote:
- If C=$0.42/oz (e.g. $0.25 spread + $0.10 total slippage + $0.07 commission-equivalent) and T=L=$0.50, p_BE=92%; at T=L=$1.00, 71%; at $2.00, 60.5%.
- A $0.15 spread alone with T=$0.50 gives 65%; with T=$1.00 gives 57.5%. Add commission/slippage before using these figures.
- A quoted 0.0 minimum/raw spread is not zero all-in cost.

Illustrative SOL spot scenarios:
- Binance base taker fees alone are 0.10% each side = 0.20% round trip before spread/slippage. If assumed spread+slippage adds 0.10%, C=0.30%; T=L=0.50% gives p_BE=80%; T=L=1.00% gives 65%.
- At Kraken's reported base taker example of 0.25% each side (verify live schedule before use), fees alone are 0.50%; with 0.10% spread+slippage, C=0.60%. At a 0.50% target, a symmetric scalp has p_BE=110% and is impossible before adverse selection; at 1.00%, 80%.
- Maker economics cannot simply be substituted: a resting limit order may not fill, may be adversely selected, and missed fills change the strategy.

**Verdict:** 30s is not approved as a directional signal for XAUUSD CFD or SOL API. Treat it as a spread/feed/latency-sensitive execution experiment. It becomes eligible only after a preregistered tick/event backtest plus paper/live shadow execution demonstrates positive net expectancy under stressed costs and no lookahead. No public evidence found proves it works robustly in the requested instruments.

## KYLA stack design

### Canonical state and hierarchy

1. **1h regime/bias (direction gate):** completed 1h bars only. Consume EMA50/EMA200 relationship and slopes, 1h market structure (HH/HL or LH/LL), and monthly context. State is `BULL`, `BEAR`, or `NEUTRAL`. Long gate: EMA50 > EMA200 with acceptable slopes, bullish 1h structure, and monthly context not explicitly bearish. Short is the exact inverse. Mixed conditions => NEUTRAL. The monthly context may be neutral; it must not contradict the selected direction.
2. **30m structure/context:** completed 30m bars. Consume 30m swing structure, FVG/order-block zones, ORB zones, and sequence state. It can locate/qualify a zone, but cannot override 1h direction. A clear 30m opposite structure at the proposed entry => stand down; neutral/unclear means no setup approval, not an automatic reversal.
3. **15m setup context:** completed 15m bars. Consume 15m structure, FVG/OB/ORB zone interaction, liquidity sweep/reclaim and sequence state. It must agree with 1h for a trade: bullish setup for long, bearish for short. 1h/15m disagreement => no trade until a newly closed 15m bar resolves it.
4. **5m execution:** completed 5m bars. Consume SSS/BBB/BBS/SSB sequence module, FVG retest and sweep+reclaim trigger. The selected variant uses 5m as the sole directional trigger; do not pick 1m or 5m after observing results.
5. **1m execution:** completed 1m bars. Same trigger modules as 5m, but only in variants explicitly using 1m. It is not an additional discretionary vote. A 1m signal cannot override a 1h/15m/30m gate.
6. **30s management only:** completed 30s bars and live bid/ask. No new directional entries, no bias changes, no pattern-generated entries, and no direction flips. It may only execute a pre-registered bracket/exit-management rule, monitor spread/quote quality, and choose between already-authorized exit actions. A fixed management rule must be declared before the test (for example, existing stop/target management plus a spread guard and a fixed time-stop); no tuning from observed results.

### Cascade and contradiction rules

- Event order: close/commit 1h -> update bias; close/commit 30m and 15m -> update context/setup; only then accept the selected 5m or 1m trigger. HTF values are frozen between their closes.
- Long requires `1h=BULL` AND `15m=BULL`; short requires `1h=BEAR` AND `15m=BEAR`. If either is neutral or opposite, stand down. If 30m is enabled and explicitly opposite, stand down. For the 30m/5m/30s management variant, 30m is the directional gate and the 5m trigger; no 1h signal is silently added.
- The LTF trigger must be in the same direction and occur after the most recent qualifying HTF setup/zone. An LTF trigger alone is never sufficient.
- One position per symbol/direction; no stacking repeated triggers from the same zone unless that rule is preregistered. No lookahead: only fully closed HTF data; enter at the next executable LTF event with bid/ask costs.
- If a higher timeframe changes to neutral/opposite while a trade is open, apply the fixed exit policy; do not invent a reversal entry.
- News/session/spread filters, if used, are fixed in the configuration and identical across variants.

## Pre-registered timeframe-switching test matrix

Lock this matrix and all parameter values before opening the OOS results. Each row is a separate strategy ID; no ad-hoc timeframe tweaking or selecting a combination after seeing results.

| ID | Bias/regime | Setup/context | Trigger | 30s role | Status |
|---|---|---|---|---|---|
| MTF-A | 1h | 15m | 1m SSS/BBB/BBS/SSB + FVG retest or sweep/reclaim | none | USEFUL test |
| MTF-B | 1h | 30m | 5m same locked trigger family | none | USEFUL test |
| MTF-C | 1h | 15m | 5m same locked trigger family | none | USEFUL test |
| MTF-D | 30m | 30m context | 5m locked trigger | management only | EXPERIMENT; not comparable to A-C as same HTF gate is intentionally different |

For each row: same instrument universe (XAUUSD CFD, NQ/MNQ with contract specification fixed, and SOL venue/pair fixed), same historical period, sessions, signal definitions, risk model, spread/commission/slippage/latency model, and data-quality rules. Run the same rows separately per asset; never pool incompatible costs. Use only completed bars, bid/ask simulation, and event ordering.

### Anti-data-mining protocol

- Commit/hash the config, matrix, code version, data snapshot and cost model before OOS. The four rows are the complete primary comparison; additions require a new research track.
- Use a fixed walk-forward schedule chosen before inspection (recommended template: fixed 12-month development / 3-month test rolling schedule, or another schedule recorded in the preregistration). Every row receives exactly the same folds and no retuning on OOS.
- Require at least 200 closed trades per strategy/asset for the primary gate. If a row cannot reach 200 under the locked period, report `INSUFFICIENT SAMPLE`, not failure/success and not a post-hoc longer period.
- Report gross and net expectancy in R, win rate, average win/loss, profit factor, max drawdown, Sharpe/Sortino, turnover, trade count, losing streak, spread/slippage distribution, latency sensitivity and results by regime/session. Include the full trade list and rejected-signal count.
- Stress costs at baseline, +25% spread/slippage, +50% spread/slippage, and a latency shock fixed in advance. A strategy that fails modest stress is not robust.
- Acceptance must be predeclared: positive net expectancy after baseline and stressed costs, PF/drawdown limits selected before testing, no catastrophic single-fold dependence, and no material collapse from development to OOS. Do not crown the highest-return row; retain only rows passing the fixed gate.
- Compare each MTF row with a locked single-timeframe control using the same trigger and costs. The question is incremental value of the hierarchy, not absolute backtest return.

## USEFUL / SKIP summary

- USEFUL: completed-bar HTF bias -> LTF setup -> LTF trigger; explicit neutral/stand-down state; no-lookahead synchronization; Quantpedia BTC D1/H1 example as a reproducibility lead; bid/ask and cost-aware WFO.
- USEFUL TEST: MTF-A/B/C and the deliberately different management experiment MTF-D.
- SKIP: 30s as a standalone signal; candle-only backtests for 30s; mid-price/zero-slippage results; unverified internet win-rate/PF claims; changing TFs after seeing OOS; treating 0.0 raw/minimum spread as free.

## Sources (exact URLs)

- https://tradeciety.com/how-to-perform-a-multiple-time-frame-analysis
- https://backtrex.com/en/blog/multi-timeframe-backtesting-guide
- https://quantpedia.com/how-to-design-a-simple-multi-timeframe-trend-strategy-on-bitcoin/
- https://www.pepperstone.com/en-eu/ways-to-trade/pricing
- https://www.xm.com/precious-metals
- https://www.binance.com/en/fee/trading
- https://researchgate.net/publication/384458498_The_impact_of_transactions_costs_and_slippage_on_algorithmic_trading_performance
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5143158
- https://cftc.gov/sites/default/files/2020-02/ABHFT20191129_ada.pdf
- https://researchgate.net/publication/300209390_Developing_Multi-Time_Frame_Trading_Rules_with_a_Trend_Following_Strategy_using_GA
- https://researchgate.net/publication/347407733_Generating_a_Multi-Timeframe_Trading_Strategy_based_on_Three_Exponential_Moving_Averages_and_a_Stochastic_Oscillator