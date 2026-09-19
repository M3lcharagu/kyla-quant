# KYLA Quant — CRYPTO + SOLANA (SOL) specification

_Status: research/specification; current research pass dated 2026-09-19. Not a promise of profitability._

## Executive decisions

- Treat SOL as a continuously traded, high-volatility market whose liquidity, spread, volume and jump risk vary by UTC hour and regime. “24/7” is not “uniformly liquid.”
- Do not hard-code universal SOL daily range, 1m/5m/15m ATR, BTC correlation or BTC beta. Calculate them from a named exchange, UTC sample, frequency and lookback. The supplied “SOL beta 1.5–2x BTC” is a hypothesis to test, not a constant.
- The strongest evidence-backed opportunities are conditional risk premia: funding/basis carry, event-volatility/risk management, and flow/breadth confirmation. Directional folklore is not an edge until it survives costs and out-of-sample tests.
- Memecoin launch scalping is an adverse-selection business: bots, priority fees, MEV, insider/creator concentration, mobile liquidity and rug/exit risk dominate. Do not map a SOL sequence signal directly onto a new low-liquidity token.
- Keep one strategy per account: separate spot direction, futures sequence/leverage, and any Deriv CFD experiment. Do not mix spot and futures P&L or signals in one performance record.

## 1. SOL market facts and measurement rules

### Market structure

SOL spot and perpetuals trade continuously, including weekends. Crypto activity is time-varying: US hours are an important price-discovery/liquidity window; weekends often have lower institutional participation and thinner books. Thin weekend liquidity can still produce sharper jumps, so “quieter” means lower average activity, not lower risk. FX’s weekend closure makes naïve SOL-vs-FX comparisons invalid unless the sampling convention is stated.

SOL is qualitatively more volatile than major G10 FX, but this pass found no auditable universal current multiplier. Report log-return realized volatility or normalized true range using the same UTC bars and lookback for SOL and the chosen FX pair. For true range:

`TR_t = max(H_t-L_t, abs(H_t-C_{t-1}), abs(L_t-C_{t-1}))`

`ATR_n = Wilder/declared moving average(TR, n)` and `ATR% = 100 * ATR / close`.

For 1m/5m/15m, state exchange/instrument (SOLUSDT spot or SOLUSDT perpetual), UTC sample, n (e.g. 14), and report median/IQR/percentiles, not one “typical” number. A 14-bar ATR is 14 bars of that timeframe and is not directly comparable across timeframes without an explicit scaling model. Do not invent current ATR values.

Compute rolling BTC/SOL correlation and SOL-on-BTC beta from synchronized log returns:

`rho = Cov(rSOL,rBTC)/(sdSOL*sdBTC)`

`beta = Cov(rSOL,rBTC)/Var(rBTC)`.

Use 30/90/365-day or intraday windows and label regime. High beta helps scalping as a contextual leading risk filter and gives larger movement per BTC impulse; it hurts because BTC shocks, liquidation cascades and correlation breaks can invalidate a standalone SOL signal. Correlation/beta are not direction guarantees.

### Binance costs and break-even math

Verify live account tier, jurisdiction, promotion and BNB setting before trading. Common base rates found in official references:

- Spot VIP 0: maker 0.10%, taker 0.10%; BNB spot discount commonly makes 0.075% effective, subject to current schedule.
- USDⓈ-M futures baseline: maker 0.02%, taker 0.05%; BNB futures discount is commonly 10%, subject to current schedule.
- Perpetual funding is normally exchanged at 00:00, 08:00 and 16:00 UTC (8-hour default); positive funding means longs pay shorts. Contract intervals/parameters can change. Funding is separate from commission.

For a gross scalp target T, round-trip commission c, and no spread/slippage/funding:

`cost share of target = c / T`

For a symmetric gross target and stop of T, with the same round-trip cost on wins and losses:

`break-even win rate p = (T + c) / (2T)`.

Examples (fees only):

| Venue/order | Round-trip fee c | c as share of 0.5% target | c as share of 1.0% target | BE win rate with equal gross stop/target |
|---|---:|---:|---:|---:|
| Binance spot, 0.10% taker each side | 0.20% | 40% | 20% | 70% at 0.5%/0.5%; 60% at 1%/1% |
| Binance spot, 0.075% BNB each side | 0.15% | 30% | 15% | 65% at 0.5%/0.5%; 57.5% at 1%/1% |
| Binance futures, 0.05% taker each side | 0.10% | 20% | 10% | 60% at 0.5%/0.5%; 55% at 1%/1% |
| Binance futures, 0.02% maker each side | 0.04% | 8% | 4% | 54% at 0.5%/0.5%; 52% at 1%/1% |

These are illustrative fee-only hurdles. Add bid/ask spread, market impact, slippage, failed/retried transactions, futures funding, liquidation and data latency. Maker orders are taker orders if they execute immediately. If the actual gross loss is L and gross win is W, with fixed round-trip cost c, use `p=(L+c)/(W+L)`; if costs vary by side/regime, use the distribution in backtest rather than a single c. A 0.5–1% scalp is therefore not automatically viable.

Deriv crypto CFD cost is not safely reducible to a fixed Binance-like percentage: use the live instrument specification for bid/ask spread, commission, swap/financing, margin and close-out. Deriv search results did not establish a universal current SOLUSD spread or standard swap. A reported swap-free MT5 rule is a 15-day grace period, then published SOLUSD administration fee `$0.03948 per lot per night`; do not convert that to a percentage without the applicable contract size. For a CFD, the approximate round-trip spread hurdle is the quoted full bid-ask percentage plus any commission; overnight financing is extra. Deriv synthetic indices are provider-generated, not SOL order books, and on-chain wallet/MEV/macro signals do not transfer.

## 2. Evidence flags for proposed edges

### USEFUL / testable

**Funding/basis carry — AMBER/GREEN, not free money.** Persistent funding/basis premia are documented risk premia. A delta-neutral candidate is long spot/short matching perpetual, but net return must exceed fees, spread, borrowing/collateral, funding reversals, exchange/counterparty and liquidation/collateral risks. High positive funding can mean crowded longs and tail risk; “short whenever funding is high” is not validated. Include funding timestamps and rate history in backtests.

**CPI/FOMC/macroeconomic releases — AMBER.** Event studies support predictable increases in crypto volume and volatility; direction is not reliably predictable without surprise versus consensus, positioning and regime. Use as a volatility/sizing filter and test first move versus 1–4h response. Do not use “buy every CPI” or “short every hawkish FOMC” as a rule.

**Bitcoin spot ETF flows — AMBER.** One cited preliminary investigation reported roughly 53–74 bp same-day BTC return per $100m net inflow, about 96 bp cumulative over ten days in one specification, and about 21% of daily return variation in that sample. These are sample-specific and endogenous (price can cause flows); they are BTC evidence, not a SOL coefficient. Use persistent flow plus price/breadth as confirmation, not a standalone next-day signal.

**US-hours/weekend structure — AMBER.** Lower weekend participation/thinner books and US-session price discovery are useful execution and sizing features. No robust universal weekend long/short direction anomaly was established. Test volume, spread, realized volatility and jump frequency separately.

### FOLKLORE / SKIP until proven out-of-sample

- Fixed BTC→ETH→SOL “rotation”: define flows, assets, rebalance, costs and survivorship before testing; available evidence supports regime-dependent co-demand, not a mechanical sequence.
- “Memecoin volume predicts SOL”: raw DEX volume can be new money, internal churn, leverage, wash trading or temporary liquidity migration. Use stablecoin netflow, breadth, unique traders/retention, depth, fees and exchange/bridge flows.
- “BTC dominance down equals altseason”: dominance is affected by token issuance/stablecoins and narrow rallies; use a fixed liquid universe and breadth.
- Guaranteed SOL beta/correlation, weekend gap rules, or high-funding directional signals.

## 3. SOL memecoin microstructure

- Launches can begin on bonding curves and move into a public DEX pool. The creation/first-block window favors automated wallets; bonding-curve completion/graduation changes market structure; first-hour social demand can be exit liquidity.
- Screen creator/deployer and connected funding wallets, top-holder concentration, first-block buyer/seller history, LP ownership/withdrawability, mint/freeze/authority settings, synchronized buys/exits and exchange/market-maker transfers. Holder count alone is not organic adoption; “liquidity locked” does not stop insiders selling.
- In a constant-product pool `x*y=k`, order impact grows as order size becomes large relative to quote reserve. Displayed market cap is not executable liquidity. A nominal `$2m` market cap can have tiny bid depth; a 1% move in the token is not the same as 1% achievable exit price. Model price impact separately on entry and exit, plus pool fees, priority fees, pending-state adverse selection and liquidity removal.
- Bots can detect creation/liquidity, bid priority fees, back-run large trades, copy wallets and create artificial volume. MEV is not all fraudulent, but retail can be adversely selected. A permissive slippage setting allows a worse fill; it does not reduce impact. A tight setting can fail and expose the trader to retry/latency risk.
- Retail rapid trading bleeds through entry/exit impact, fees, priority costs, failed transactions, bots and adverse selection. Do not allow manual launch sniping in a KYLA production module. If researched at all, use a paper-trading/allowlist module with a hard liquidity/depth floor, creator/authority checks, max loss and no leverage.

## 4. Sequence/MTF implementation in KYLA

Keep existing KYLA SSS/BBB definitions; crypto translation is a market-data and execution wrapper:

1. **15m regime:** determine SSS/BBB directional state, BTC regime, volatility percentile, funding/basis and event/weekend flags.
2. **5m setup:** require the same directional state/structure and liquidity/ATR-normalized stop distance; reject if spread/impact budget exceeds the planned edge.
3. **1m trigger/execution:** enter only on the defined sequence confirmation and use realistic bid/ask plus latency/impact. A 1s stream is research-grade microstructure input, not a default signal timeframe; avoid claiming 1s Futures candles unless the current API supports them.
4. **Risk:** no trade when BTC impulse conflicts with SOL direction, when funding/liquidation risk is extreme, or when realized spread/impact exceeds budget. Weekend and macro flags reduce size or disable execution.
5. **Backtest:** use event-driven fills, no look-ahead, incomplete-candle exclusion, UTC timestamps, walk-forward/out-of-sample splits, and fee/spread/slippage/funding/liquidation models. Report expectancy after costs, turnover, max drawdown, tail loss, fill rate and sensitivity to 2x/5x cost.

Binance data endpoints:
- Spot klines: `GET /api/v3/klines`; official docs list `1s`, `1m`, `3m`, `5m`, `15m` and higher intervals.
- USDⓈ-M Futures klines: `GET /fapi/v1/klines`.
- Mark-price klines: `GET /fapi/v1/markPriceKlines`.
- Funding history: `GET /fapi/v1/fundingRate`.
- Force orders: `GET /fapi/v1/forceOrders`; liquidation WebSocket includes `!<symbol>@forceOrder`.

Use `backtesting.py` with commission and spread, but add custom execution logic for impact/slippage, funding, leverage, margin and liquidation. Its commission is charged on entry and exit in current documentation; validate installed-version behavior.

## 5. Account/module assignment

| Account | Single module | Instrument/rules | Status |
|---|---|---|---|
| Binance spot | SOL directional SSS/BBB MTF | SOLUSDT only initially; 15m/5m/1m; unleveraged; no launch memecoins; cost gate must pass | Preferred first production test |
| Binance USDⓈ-M futures | SOL perpetual sequence/momentum or separately researched funding carry | Isolated margin; conservative 1–2x cap for research; BTC filter; funding/liquidation/mark-price model; never share spot strategy P&L | Separate, higher-risk pilot only after spot validation |
| Deriv crypto CFD | Dedicated SOLUSD CFD sequence experiment only | Provider spread/swap/margin/close-out loaded live; no wallet-flow or DEX assumptions; no mixing with Binance stats | Skip until costs/data are transparent |
| Deriv synthetic | None in CRYPTO/SOL module | Not a real SOL market; no on-chain, ETF, macro or wallet-flow mapping | SKIP |
| Solana DEX/memecoins | Research/paper allowlist only | Hard liquidity/holder/authority/impact filters; no leverage; no manual sniping | SKIP for production until separately validated |

## 6. Source URLs

### Binance fees, funding, liquidation and API
https://binance.com/en/fee/trading
https://binance.com/en/fee/futureFee
https://binance.com/en/academy/articles/what-are-funding-rates-in-crypto-markets
https://binance.com/en/support/faq/detail/360033525031
https://binance.com/en/support/faq/detail/360033544231
https://binance.com/en/support/faq/detail/360033525271
https://binance.com/en/support/faq/detail/b3c689c1f50a44cabb3a84e663b81d93
https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market
https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data
https://developers.binance.com/en/docs/products/derivatives-trading-usds-futures/change-log
https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usds-futures/api/ws-streams/market
https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data

### Volatility, correlation and market structure
https://mdpi.com/1911-8074/19/9/707
https://pmc.ncbi.nlm.nih.gov/articles/PMC7783506/
https://ledgerjournal.org/ojs/ledger/article/download/213/212/1232
https://papers.ssrn.com/sol3/Delivery.cfm/6f2e36a8-b571-47bb-8166-834ef6d86e02-MECA.pdf?abstractid=7434697&mirid=1
https://gitbook-docs.coinmetrics.io/market-data/market-data-overview
https://gitbook-docs.coinmetrics.io/coin-metrics-prices/coin-metrics-prices/reference-rate-metrics
https://gitbook-docs.coinmetrics.io/market-data/market-data-overview/realized-volatility-metrics
https://gitbook-docs.coinmetrics.io/network-data/network-data-overview/market/volatility

### Edge evidence
https://finance.wharton.upenn.edu/~jermann/AHJ-main-10.pdf
https://papers.ssrn.com/sol3/Delivery.cfm/6461606.pdf?abstractid=6461606&mirid=1&type=2
https://arxiv.org/html/2212.06888v5
https://www.mdpi.com/2227-7390/14/2/346
https://researchgate.net/publication/344638917_Do_FOMC_and_macroeconomic_announcements_affect_Bitcoin_prices
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4478184
https://www.sciencedirect.com/science/article/pii/S0165188920301482
https://cfbenchmarks.com/blog/btc-gives-back-gains-after-cpi-print
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6592830
https://ledger.pitt.edu/ojs/ledger/article/view/393/331
https://zuscholars.zu.ac.ae/works/7267/
https://falconx.io/newsroom/what-can-spot-etf-flows-tell-us-about-the-trajectory-of-bitcoin-prices-a-preliminary-statistical-investigation
https://nexo.com/blog/how-bitcoin-etf-flows-affect-price
https://blockscholes.com/research/bybit-x-block-scholes-the-altcoin-rotation-why-and-when-altcoins-outperform-bitcoin
https://bitcoinfoundation.org/news/altcoins/bitcoin-vs-solana-why-capital-is-rotating-into-sol-as-btc-nears-80k

### Deriv
https://deriv.com/trading-calculators/swap-calculator
https://deriv.com/trading-calculators
https://blog.deriv.com/blog/admin-fees-for-deriv-mt5-swap-free-accounts
https://deriv.com/markets/cryptocurrencies
https://deriv.com/markets/derived-indices/synthetic-indices

### Backtesting and Solana-risk references
https://kernc.github.io/backtesting.py
https://kernc.github.io/backtesting.py/doc/examples/Quick%20Start%20User%20Guide.html
https://kernc-backtesting-py.mintlify.app/concepts/backtest
https://kernc-backtesting-py.mintlify.app/api/backtest
https://github.com/kernc/backtesting.py
https://arxiv.org/html/2512.11850v1
https://arxiv.org/html/2608.20271
https://researchgate.net/publication/391904963_Trust_Dynamics_and_Bot-Driven_Responses_An_Approach_to_Rug_Pulls_in_Solana_Meme_Coin_Markets
https://papers.ssrn.com/sol3/Delivery.cfm/7128818.pdf?abstractid=7128818&mirid=1
https://chainalysis.com/blog/crypto-market-manipulation-wash-trading-pump-and-dump-2025
https://chainalysis.com/blog/illuminating-the-shadows-of-web3-hacks-ep-118
https://chainalysis.com/blog/ai-prediction-markets-the-future-of-crypto-in-2025-ep-148

## Research limitations

Some search-returned sources are working papers, vendor research or preliminary analyses rather than peer-reviewed evidence; some memecoin links may be future-dated relative to the stated research date and must not be treated as validated statistics. No current universal SOL ATR, daily range, correlation/beta, Deriv spread or SOL-specific funding rate was established here. Before production, pull fresh Binance candles/trades/order-book snapshots and Deriv live specifications, then rerun the cost and walk-forward tests.