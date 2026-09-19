# Market intelligence specification

## Purpose

Market intelligence is a fail-closed context layer. It describes current conditions; it does not create permission to trade by itself. Every output is timestamped in UTC and records source, freshness, and assumptions.

## Required state

`now_state.py` covers spread versus rolling median, realized-volatility state, session clock, trend/range classification, funding and open-interest context, and a news-lock state. `monthly_context.py` covers month-to-date returns, ranges and volatility, macro regime, and expiry context. `upcoming_events.py` caches FRED, BLS, and FOMC event placeholders and derives event risk.

## Stance gates

`stance_engine.py` can return `TRADE_ALLOWED`, `REDUCED`, `BLOCKED`, `FLAT_ONLY`, `DATA_FAILURE`, or `MANUAL_KILL`. A 30-minute event lock is a hard gate around configured high-impact releases. Missing data, stale data, a kill switch, invalid costs, or missing approval must not silently become permission to trade.

## Data policy

- UTC timestamps are mandatory.
- Venue and instrument tags are mandatory.
- Bid/ask are preserved where available; mid is never presented as a quote when it is only inferred.
- Rate limits, retries, reconnects, and gap detection are interfaces/stubs until tested against each vendor.
- FRED, BLS, and FOMC values are placeholders until source-specific adapters and licensing/usage checks are complete.

## TODOs

Define the exact instruments, lookback windows, session boundaries, rolling-median implementation, release-calendar sources, and data-quality thresholds before relying on any output.
