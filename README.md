# KYLA Quant

KYLA is a small, phone-first command center for disciplined research, paper trading, and product operations. It favors explicit state, low-cost infrastructure, and a human-approved release path over automation for its own sake.

> **Boundary:** This repository is a research and paper-trading scaffold, not financial advice and not production or live execution. It contains no secrets, live order path, fabricated metrics, or promised returns.

## Blueprint

### Command center

- **Primary control:** WhatsApp for concise commands, approvals, alerts, and daily briefs.
- **Backup control:** Discord when WhatsApp is unavailable or unsuitable.
- **Code home:** GitHub is the source of truth for code, documentation, reviews, and audit history.
- **Dashboard:** `dashboard/` is a no-build static KYLA room view deployable on Vercel's free tier.
- **Runtime posture:** keep the core light enough for an iPhone 11 plus a Mac running Catalina; use Multipass for Catalina-compatible Linux containers when a container boundary is needed.

### Seven core agents

1. **Orin** — command center and market context.
2. **Sable** — risk, permissions, and kill-switch discipline.
3. **Chroma** — signal curation and setup quality.
4. **Maven** — macro, calendar, and regime context.
5. **Vale** — execution planning and paper-order hygiene.
6. **Echo** — journal, evidence, and review memory.
7. **Lumen** — portfolio pulse and consistency checks.

Specialists sit behind the core rooms when needed: **Sophia** (R13 QA/security/legal), data reliability, research, content, and product-operations specialists. Specialists advise; the gate and the human owner retain release authority.

### Fourteen workflows

1. Command intake and routing
2. Daily operating brief
3. Market/context scan
4. Data-quality check
5. Setup and signal review
6. Paper-trading signal proposal
7. Risk and exposure review
8. Paper-order reconciliation
9. Trading journal update
10. Portfolio pulse
11. Research and strategy review
12. Content/product operations
13. QA, security, and legal review
14. Incident, kill-switch, and weekly review

These are workflow names, not claims that every integration is enabled. Missing data, stale data, failed checks, and unclear authority must fail closed.

## Operating rules

- **R13 is mandatory:** nothing ships, deploys, or advances toward execution without the QA/security/legal gate in `docs/R13_QA_GATE.md` and a human approval record.
- Default to read-only, sandbox, or paper mode. There is no live execution in this scaffold.
- Never commit secrets. Use environment variables or a secret manager outside the repository.
- Prefer small, reversible changes, explicit logs, least privilege, rate-limit awareness, and a kill switch.
- Do not treat a signal, backtest, dashboard state, or model output as financial advice or evidence of future performance.
- Keep the free-tier budget visible: avoid unnecessary polling, heavy builds, paid APIs, and dependencies.
- Record assumptions, source timestamps, approvals, and unresolved loopholes before promotion.

## Layout

- `docs/ARCHITECTURE.md` — platform choices and constraints.
- `docs/LOOPHOLES.md` — initial risk and control checklist.
- `docs/R13_QA_GATE.md` — existing gate reference.
- `dashboard/` — dependency-free static command-center shell.
- `trading/` — paper-signal starter with an intentionally unimplemented strategy placeholder.
- `src/`, `quant/`, and `scripts/` — existing research and quant modules; extend them only behind the same controls.

## Local preview

```bash
python3 -m http.server 8080 --directory dashboard
# open http://localhost:8080
node trading/paper_signal.js path/to/candles.json
```

The trading command accepts a JSON array of candles and emits a paper-only decision. It does not place orders or invent performance data.
