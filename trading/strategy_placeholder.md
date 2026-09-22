# Strategy placeholder: trendline + POI + FVG scalping

> **STATUS: NOT IMPLEMENTED.** This document is a specification placeholder, not a trading signal or financial advice.

Before coding any rule, define and review each item below with timestamped, reproducible data:

- **Market and session:** instrument, venue, timezone, session windows, and news/volatility exclusions.
- **Trendline:** objective swing-point detection, minimum touches, tolerance, invalidation, and look-ahead protection.
- **POI (point of interest):** exact qualifying structure, context timeframe, freshness, mitigation, and invalidation.
- **FVG (fair value gap):** candle definition, minimum size, fill rule, direction, and whether wicks count.
- **Entry:** the complete conjunction of trend, POI, FVG, trigger, spread, and data-freshness conditions.
- **Risk:** stop placement, position sizing, max attempts, daily loss limit, correlation rule, and kill switch.
- **Exit:** target, time stop, partials, invalidation, and fees/slippage treatment.
- **Evidence:** train/test split, out-of-sample protocol, walk-forward design, assumptions, and reproducible fixtures.
- **Gate:** QA, security, legal/compliance, provider terms, human approval, and R13 record before paper deployment.

Until every item is specified, tested, and approved, the executable scaffold must return `HOLD` and must not place orders.
