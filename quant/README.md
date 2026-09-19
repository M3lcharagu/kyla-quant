# KYLA QUANT v0.1

A small, dependency-free research scaffold for disciplined, cost-aware market-system experiments. It does not connect to live accounts or imply profitability.

## Goals

- Make assumptions, timestamps, execution rules, and costs explicit.
- Keep strategy logic reproducible from a candle stream and pre-registered parameters.
- Separate data, signals, execution simulation, and reporting.
- Prefer inspectable standard-library code; keep live integrations behind credential and QA gates.

## Research rules

**200-trade gate.** Fewer than 200 completed trades is an incomplete sample, not a production claim. `Backtester` reports `gate_passed=False` and a failure message below 200 by default. The gate does not make a weak strategy good; it prevents tiny samples being treated as evidence.

**Cost-aware philosophy.** Model spread, commission, and slippage before interpreting results. The simulator treats a quoted spread as the full bid/ask difference and applies half at entry and half at exit, plus per-side slippage and commission. Defaults in `quant.costs` are starting assumptions and must be measured for the venue, account tier, session, and contract.

**MTF pre-registration; no post-result tweaking.** Before a multi-timeframe experiment, register timeframes, alignment, lookbacks, entry/exit rules, and parameters. Do not change a timeframe, threshold, session boundary, or filter after seeing results and call it the same experiment. A change starts a new experiment and validation sample.

**One strategy per account.** During validation, run one strategy per account so risk, execution, and attribution stay legible. A portfolio combination is a separate experiment.

## Included v0.1

- `costs.py`: all-in cost arithmetic, instrument assumptions, and `p_BE = 0.5 + C/(2T)`.
- `data.py`: public Binance klines, explicit OANDA practice stub, and local CSV fallback.
- `backtest.py`: event-driven candles, entries/exits, costs, equity curve, trades, and metrics.
- `strategies/london_orb.py`: initial GBPUSD London ORB skeleton.
- `tests/test_costs.py`: standard-library sanity tests.

`docs/FOREX_PAIRS_SPEC.md` was not present on the inspected `main` branch. The ORB uses the task-specified windows (Asian 00:00-07:00 UTC; entries 07:00-11:00 UTC) and labels remaining values as initial guesses requiring validation.

## Exact Catalina test plus demo command

From the repository root:

```sh
python3 -m unittest discover quant/tests && python3 - <<'PY'
from quant.backtest import Backtester
class OneTrade:
    def __init__(self): self.done = False
    def next(self, c):
        if not self.done:
            self.done = True
            return {"action":"enter", "side":"long", "stop":c["close"]-1, "target":c["close"]+2}
        return "exit"
candles = [
 {"timestamp":"2024-01-01T00:00:00+00:00","open":100,"high":101,"low":99,"close":100},
 {"timestamp":"2024-01-01T00:05:00+00:00","open":100,"high":102,"low":100,"close":101},
]
print(Backtester(OneTrade()).run(candles).metrics)
PY
```

The demo intentionally has one trade and therefore fails the 200-trade gate.
