# Sequence setup specification

## Deterministic bars

A bar is `S` (sell/bearish) when `close < open` and `B` (buy/bullish) when `close > open`; doji bars are neither unless an explicit future policy says otherwise. A valid setup also records wick rejection, EMA direction, momentum, and volume conditions. These are explicit inputs, not discretionary after-the-fact labels.

The supported three-bar sequences are:

- **SSS** — three sell bars followed by a reversal/continuation trigger as configured.
- **BBB** — three buy bars followed by a reversal/continuation trigger as configured.
- **BBS** — buy, buy, sell sequence with the final bar's rejection and trend filters.
- **SSB** — sell, sell, buy sequence with the final bar's rejection and trend filters.

The detector is conservative: absent indicator or volume data yields no signal rather than an invented pass. Exact threshold calibration remains a TODO and must be versioned with backtests.

## Probe cycle

A 2:1 probe cycle uses full size on trades 1 and 2. Trade 3 is a minimal `0.25R` probe. A cycle stops after the configured sequence of outcomes or a risk gate. With two full-risk winners and one quarter-risk loss, the exact pre-cost math is:

`2x+1R - 0.25R = +1.75R per cycle before costs`

This is an accounting identity, not an expected result. Costs, losers, selection effects, and out-of-sample behavior must be included.

## Exit rule

Every setup supports a hard stop, target, and `TIME_EXIT`. A position must be flat at 43–45 minutes (configurable window; default hard cutoff 45 minutes) unless the order is already closed. No extension is allowed merely to avoid recording a loss.

## TODO / assumptions

Define market-specific tick/point semantics, exact stop/target placement, wick percentage, EMA periods, momentum window, volume baseline, and how overlapping signals are resolved. Mel approval is required before promotion.
