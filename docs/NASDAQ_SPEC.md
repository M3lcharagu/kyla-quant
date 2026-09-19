# NAS100 / NQ — Nairobi scalper fact sheet
Research date: 2026-09-19 (Africa/Nairobi). U.S. cash session is on EDT (UTC−4) at this date.

## Executive facts
NAS100 is the CFD name for the Nasdaq-100; NQ is the CME E-mini futures contract and MNQ its 1/10-size Micro. Liquidity/volatility normally has a U/reverse-J shape: London–NY overlap and 09:30 ET cash open are active, midday contracts, and the close often re-expands. This is a tendency, not a guaranteed edge.

## Session map: EAT (UTC+3)
| Window | EDT (roughly Mar–Nov) | EST (roughly Nov–Mar) | Use |
|---|---|---|---|
| NY premarket starts 04:00 ET | 11:00–16:30 | 12:00–17:30 | levels/news prep; not equivalent to cash open |
| London–NY overlap 08:00–11:30 ET | 15:00–18:30 | 16:00–19:30 | liquidity/continuation tests |
| NYSE/Nasdaq cash open 09:30 ET | 16:30 | 17:30 | prime ORB/execution window |
| 10:00 ET data/killzone start | 17:00 | 18:00 | data reaction; ICT 10:00–11:00 window ends 18:00/19:00 |
| midday lull ~11:30–13:30 ET | 18:30–20:30 | 19:30–21:30 | generally skip low-quality scalps |
| late session 15:00–16:00 ET | 22:00–23:00 | 23:00–00:00 | close-flow/PM tests |

The often-quoted fixed EAT times 15:30 or 17:30 for the cash open are not both correct: 09:30 ET is 16:30 EAT during U.S. daylight time and 17:30 during U.S. standard time. Kenya does not change clocks; U.S./UK DST transition weeks need checking. Exchange premarket is not one single opening; use the 04:00 ET start above and distinguish it from 09:30 ET cash open.

## Volatility / ATR
A precise universal NQ 5m or 15m ATR value/multiplier was not verified. 5m is more responsive/noisy; 15m smoother for structure. Build a time-of-day seasonal profile from continuous front-month NQ/MNQ data: separate ETH/RTH, roll consistently, calculate ATR5 and ATR15 by exact time slot, median/percentiles, and split ordinary vs CPI/NFP/FOMC and volatility regimes. Do not use a fixed “open is X times overnight ATR” claim without testing.

## Costs and point-value math
### Retail CFDs
CFD specifications are feed/account-specific and floating. OANDA EU US100 page showed a live example spread 1.1 (29955.5−29954.4), minimum step 0.1, contract size described as price × $20 per 1 lot, hours Mon–Fri 00:01–22:59; US100 commission was not specifically stated. Under that multiplier: P/L = index-point move × 20 × lots; 1.00 lot = $20/index point, 0.10 lot = $2/point. A 1.1-point spread is about $22 at 1 lot. Verify the exact platform spec; do not treat this as universal.
Deriv US Tech 100 official page says spread from $0.90, but returned page did not show contract size, point value, commission or hours; verify in-platform. FTMO US100 index commission is 0 in its symbols information, but spread is live/variable. No universal OANDA/Deriv/FTMO retail spread should be assumed.
Round-trip cost as percentage of target = (all-in round-trip cost in points ÷ target points) × 100. Illustrative OANDA 1.1-point spread equivalent: 10-point target = 11%; 20 = 5.5%; 30 = 3.67%, before slippage/swaps. Add commission as commission dollars ÷ dollars/point ÷ target points. Slippage/news widening can dominate.

### CME futures
MNQ: multiplier $2 × Nasdaq-100 index; tick 0.25 point; tick value $0.50; $2/point. NQ: $20 × index; $5/tick. Margins are dynamic; no fixed September-2026 margin was verified. Historical indicative ~$836 initial/$760 maintenance is not guaranteed. Reported exchange/clearing component roughly $0.25–$0.35 per MNQ side is not all-in: broker commission, exchange, clearing, NFA/regulatory fees vary. Compare CFD using its actual multiplier, not MNQ assumptions. Futures give transparent tick math and centralized execution but require a futures broker/data and margin; CFDs offer fractional sizing but spread/slippage/swap and prop rules matter.

## Edges: evidence flags
- 5m ORB: define 09:30–09:35 ET; 15m ORB: 09:30–09:45 ET. Test close breakout vs retest, one trade/day, stop/target/trailing. Reported NQ/community figures include ~41.1% wins in a 1,517-trade automated test and 260/444 = 58.56% in another; other summaries ~40–55%. Rules/samples differ, likely regime-dependent, not validated. Arithmetic only: 41.1% with 2R winners/1R losers = +0.233R before costs; 58.56% at 1:1 = +0.171R before costs. Do not hard-code a win rate.
- VWAP reclaim/rejection: useful testable filter/setup (long reclaim above session VWAP, short rejection below, with slope/volume/regime); no robust NQ-only stats verified. Published 50–65% or +1.3R–1.8R claims are unsupported here: folklore until reproduced.
- ICT NY AM 10:00–11:00 ET: a hypothesis/time window, not documented proof of edge. Map 17:00–18:00 EAT in EDT, 18:00–19:00 in EST.
- CPI/NFP/FOMC: usually volatility/event-risk expansion; direction is not guaranteed. Use calendar, event-specific slippage, wider invalidation or skip.
- London–NY continuation: plausible and testable after overnight/London range break; not proven universal edge.

## Cross-market regime confirmation
No stable universal correlation study was verified. NQ–gold is generally low/intermittent; USDJPY is a yield/carry/liquidity proxy, not a fixed inverse. Yen strength/carry unwind can coincide with NQ and BTC selling. BTC (and likely SOL) can co-move with NQ in risk-on/liquidity regimes and decouple or fall together during stress. Use synchronized log returns and rolling correlations/beta by regime; treat gold/JPY/BTC/SOL as confirmation/risk context, never deterministic signal. SOL-specific NQ statistics were not found.

## Prop-firm constraints and sizing
FTMO US100 is available as a Nasdaq CFD. Official FTMO: 2-Step maximum daily loss 5% of initial simulated capital; 1-Step 3%; equity includes floating and closed P/L, commission and swaps; resets at midnight CE(S)T. Live index spread is variable and commission is 0 per symbols info. Size from actual US100 $/point: risk dollars = stop points × $/point × lots + costs; keep a buffer because floating loss and reset timing count.
PipFarm Classic: official page says maximum daily loss 3% (4% from Rank 4+), trading day starts 22:00 GMT standard / 21:00 GMT during U.S. DST; account-wide max loss depends on mode (one-stage trailing 8%/9% Rank 2+, one-stage static 6%/7%, two-stage 9%/10%). Instant EOD trailing is different: no standard MDL, 1% Pip Protector, 5% trailing EOD rising to 6% at Rank 2+. Verify current product rules and US100 symbol conditions. Never transfer CME MNQ $2/point to a CFD.

## KYLA module mapping
1. Sequence/context: overnight high/low, London range, prior day levels, gap and VWAP; classify trend/range/news.
2. ORB module: 5m/15m range, breakout close/retest, one attempt, ATR-normalized stop, daily loss guard.
3. VWAP module: reclaim/rejection and slope/hold confirmation; reject if contrary to selected regime.
4. Event module: calendar gate; separate news and ordinary models.
5. Confirmation: rolling NQ–gold/USDJPY/BTC/SOL returns only as a soft regime feature.
6. Execution/risk: broker-specific point value, spread/slippage, EAT/DST window, prop-firm equity and reset limits.

## USEFUL / SKIP
USEFUL: EAT/DST-aware session gates; separate ETH/RTH; 5m trigger + 15m context; ORB/VWAP variants; ATR percentiles by time slot; news tags; out-of-sample/year/regime splits; actual spread/slippage/commission; max drawdown and losing streaks.
SKIP: universal ORB win-rate claims; fixed EAT cash-open times; unsupported VWAP/ICT expectancy claims; assuming MNQ fees/point value on CFD; treating correlation as causation; testing only trend/news days; ignoring floating prop loss/reset.

## Minimum backtest spec
Use continuous front-month NQ/MNQ with roll policy; 5m and 15m bars timestamped ET; 5/15/30m OR definitions; close/retest entries; stops/targets in R and ATR; VWAP definition; one-trade/day and opposite-break rules; CPI/NFP/FOMC tags; spread, commission, slippage, and latency; in/out-of-sample by year and regime; trades, win rate, avg win/loss, expectancy, profit factor, drawdown, losing streak and cost sensitivity.

## Sources
https://www.cmegroup.com/markets/equities/nasdaq/micro-e-mini-nasdaq-100.html
https://www.cmegroup.com/markets/equities/nasdaq/nasdaq-futures.html
https://www.cmegroup.com/markets/equities/nasdaq/e-mini-nasdaq-100.contractSpecs.html
https://www.cmegroup.com/articles/faqs/micro-e-mini-equity-index-futures-frequently-asked-questions.html
https://www.cmegroup.com/company/clearing-fees.html
https://oanda.com/eu-en/trading/indices-cfd/us100
https://oanda.com/eu-en/document/50
https://deriv.com/markets/stock-indices/us-indices/us-tech-100
https://ftmo.com/en/symbols/
https://academy.ftmo.com/lesson/maximum-daily-loss/
https://help.pipfarm.com/articles/7719299-classic-mode-introduction
https://help.pipfarm.com/articles/4791772-eod-trailing-instant-account
https://tradingview.com/symbols/CME_MINI-NQ1!
https://tradethatswing.com/opening-range-breakout-strategy-up-400-this-year/
https://tradingview.com/script/slULs42t-15-Min-ORB-Strategy-for-NQ-w-5-min-Confirmation/
https://reddit.com/r/TopstepCommunity/comments/1v9rb3/ran_the_15min_nq_opening_range_breakout_through/
https://reddit.com/r/Trading/comments/1vfxu30/1500_backtested_trade_results_on_the_15min_orb/
https://reddit.com/r/Daytrading/comments/1lgk0cp/why_dont_more_people_do_the_15min_opening_range/
https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID3793585_code3212131.pdf?abstractid=3574323&mirid=1
https://academicweb.nd.edu/~zda/intramom.pdf
https://www.sciencedirect.com/science/article/pii/S1059056025009530
https://finance.yahoo.com/markets/crypto/articles/bitcoin-correlation-gold-just-hit-153154868.html
https://www.tradingview.com/news/stocktwits:c3b8ace99094b:0-bitcoin-gold-correlation-hits-nearly-six-year-high-as-btc-breaks-from-tech-stocks/
https://help.pipfarm.com/articles/3317481-max-daily-loss-rule-explained
