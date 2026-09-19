# R13 QA gate

Research must be rejected unless all required checks are evidenced:

- costs included (spread + slippage + commission);
- no look-ahead or leakage;
- at least 200 cycles/trades as defined by the report;
- positive out-of-sample expectancy in R;
- drawdown fits the declared risk budget;
- kill switch tested;
- a documented no-trade condition;
- Mel approval required for research→paper and paper→live.

The result is `PASS`, `FAIL`, or `INCONCLUSIVE`; missing evidence is not a pass. A passing backtest does not authorize live trading. The gate is a rejection checklist and should be rerun after data, code, costs, or risk changes.
