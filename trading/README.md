# Trading starter

This directory is a deliberately small **paper-trading signal scaffold**. It is not financial advice, not a production system, and not connected to a broker or exchange. It places no live orders and includes no fabricated backtest results.

## Files

- `paper_signal.js` — dependency-free Node.js module/CLI that validates candle input and returns a conservative paper-only decision.
- `strategy_placeholder.md` — explicit placeholder for future trendline + POI + FVG scalping rules.

## Run

Provide a JSON file containing an array of candles. Each candle should have numeric `time`, `open`, `high`, `low`, and `close` fields. Volume is optional.

```bash
node trading/paper_signal.js path/to/candles.json
```

The output is a JSON proposal with `mode: "paper"`. A valid input still produces `HOLD` until a reviewed strategy is implemented. Missing, stale, or invalid input returns a rejected/hold state rather than a guess.

Before any future promotion, require reproducible data, cost/slippage assumptions, out-of-sample testing, risk limits, security review, legal review, human approval, and the R13 gate. Live execution is intentionally out of scope.
