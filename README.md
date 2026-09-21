# kyla-quant

**Profit-first, consistency-second**

`kyla-quant` is a deliberately conservative research, backtesting, paper-execution, journaling, and QA scaffold for systematic market work. It is designed to make assumptions visible, put costs and risk before optimization, and keep live integrations behind explicit gates.

> **Disclaimer:** This repository is a scaffold, not a promise of profitability or financial advice. Profitability requires data-quality checks, realistic cost modeling, robust out-of-sample validation, and independent review. Nothing here is investment advice. Use placeholders, paper accounts, and small controlled experiments until evidence supports the next stage.

## Architecture

```text
market adapters → normalized data → feature/regime layer → strategy signal → cost model → risk engine → paper execution → journal → R13 QA gate
```

The arrows are a control flow, not a claim that any adapter is live or production-ready. Safe stubs intentionally fail closed when required data, credentials, or approvals are missing.

## Repository map

- `src/kyla_quant/data/` — venue and research-data adapter boundaries plus normalization and reliability stubs.
- `src/kyla_quant/market_intel/` — state, monthly context, event risk, stance, brief, and typed schemas.
- `src/kyla_quant/setups/` — deterministic SSS/BBB/BBS/SSB sequence detection, probe cycle, and exits.
- `src/kyla_quant/backtest/` — walk-forward and cost-aware reporting interfaces.
- `src/kyla_quant/risk/` — fixed-risk controls and a SQLite journal schema.
- `src/kyla_quant/paper/` — OANDA practice, Freqtrade dry-run, and Hyperliquid shadow boundaries.
- `src/kyla_quant/qa/` — R13 rejection checks.
- `docs/` — specifications and operating notes.
- `products/` — self-contained digital-product sales pages and fulfillment READMEs.

## Quick start later (Mac or Docker)

1. Copy `config.example.yaml` to a local, untracked config file.
2. Install `requirements.txt` in a virtual environment, or build the Docker image.
3. Keep all credentials as environment variables or in a secret manager; never commit them.
4. Run research sequentially, inspect cost assumptions, and archive reports.
5. Do not advance from research to paper or paper to live without documented Mel approval and a passing R13 gate.

This initial scaffold is intentionally runnable-later-on-Mac/Docker rather than connected to a live account. TODOs and placeholders are explicit.

## Roadmap

- [ ] Add real adapter clients behind credential and rate-limit interfaces.
- [ ] Add versioned raw-data snapshots and quality dashboards.
- [ ] Implement a reproducible feature store and regime labels.
- [ ] Validate sequence definitions on a sufficiently large, leakage-free dataset.
- [ ] Run 200+ cycles through walk-forward and out-of-sample tests with realistic costs.
- [ ] Add paper-execution reconciliation and daily journal review.
- [ ] Obtain Mel approval for each research→paper and paper→live promotion.

## Assumptions / TODOs

- Symbols, timeframes, venue credentials, timezone policy, and event calendars are configuration placeholders.
- Adapter payloads are not guaranteed to match vendor schemas until integration tests are written.
- Sequence conditions are deterministic research rules, not a claim of edge.
- Missing, stale, contradictory, or locked data must fail closed.

## KYLA mobile PWA

Open the [installable KYLA dashboard](web/) for the phone-first QUANT, AUTOPILOT, 3D HUB, and PRODUCTS views. It is a no-build static PWA; see [`web/README.md`](web/README.md) for iPhone Safari installation, free hosting, icons, and `dashboard.json` update guidance.

## Scheduled automation

The GitHub Actions workflows run in UTC and use Python 3.11:

- [`nightly-backtest.yml`](.github/workflows/nightly-backtest.yml) — daily at `0 19 * * *`; installs dependencies and runs `python scripts/strategy_factory.py`.
- [`paper-trader.yml`](.github/workflows/paper-trader.yml) — every 15 minutes during `06:00–13:59` UTC on weekdays; it runs only when the repository variable `PAPER_TRADING_ENABLED` is exactly `true`.
- [`weekly-kpi.yml`](.github/workflows/weekly-kpi.yml) — Sundays at `0 15 * * 0`; it writes KPI stdout to `reports/weekly-kpi.txt` with `tee`.

The paper and KPI workflows commit their generated paper artifacts: `journal/paper_trades.json` and `journal/trades.db`. Because the database and reports are ignored locally, the workflows use explicit `git add -f`. They configure the `github-actions[bot]` identity and push to `main` using `GITHUB_TOKEN`.

The verified local commands are:

```bash
pip install -r requirements.txt
python scripts/strategy_factory.py
python scripts/paper_trader.py --once
python scripts/trade_journal.py report
```

Review the strategy definitions and research caveats in [`docs/STRATEGY_LIBRARY.md`](docs/STRATEGY_LIBRARY.md) before treating any output as evidence.

## License

No license has been selected yet. Treat this repository as all-rights-reserved until the owner adds one.
