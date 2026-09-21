# Scheduled workflows

These GitHub Actions workflows run in UTC with Python 3.11:

- `nightly-backtest.yml` runs daily at `0 19 * * *`, runs the strategy factory backtest, and commits changed `docs/STRATEGY_LIBRARY.md` and/or `results` artifacts.
- `paper-trader.yml` runs every 15 minutes during `06:00–13:59` UTC on weekdays, only when the `PAPER_TRADING_ENABLED` repository variable is exactly `true`. It commits `journal/paper_trades.json` and `journal/trades.db`.
- `weekly-kpi.yml` runs Sundays at `0 15 * * 0` and writes `python scripts/trade_journal.py report` output through `tee` to `reports/weekly-kpi.txt`, which it commits.

Each artifact workflow uses `GITHUB_TOKEN` for checkout and push. Its final commit step runs with `if: always()` and configures:

```text
git config user.name "kyla-bot"
git config user.email "kyla-bot@users.noreply.github.com"
```

The paper trader has a second in-script guard in addition to the job-level repository-variable guard.
