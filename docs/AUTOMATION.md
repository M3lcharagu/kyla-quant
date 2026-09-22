# Automation map

Kyla is intentionally local-first and paper-only. This document is the inventory of hands-free workflows that are present in the repository or explicitly planned. **DONE means code or a workflow file exists; it does not mean an external account, service, feed, QR session, deployment, or paid API is connected.** A `scaffolded` note means a human still has to install, configure, provide inputs, or review output.

## Operating rules

- Default to local, read-only, sandbox, or paper mode. No workflow in this repository places a live order.
- Keep credentials, QR/session files, API keys, cookies, and personal contact data outside Git. The WhatsApp auth directory is ignored locally.
- Every trading output is a proposal/alert for review, never an execution instruction. R13 QA/security/legal review and a human approval remain mandatory before any higher-risk release.
- Workflows fail closed when required data is missing, stale, malformed, or ambiguous. Static/local output is not evidence that a provider is connected.
- Cadences below describe intended triggers. A GitHub Actions schedule still depends on repository Actions being enabled; a local schedule still depends on the Mac being awake and launchd being installed by a human.

## Workflow inventory

| Workflow | Trigger | Action | Cadence | Inputs → outputs | Safety / manual checkpoint | Status |
|---|---|---|---|---|---|---|
| Daily content-plan generation | `npm run content` or local scheduler | Build a deterministic 3–5 clip plan from supplied topics; no external API call | Daily handoff, or on demand | topics/date/count → JSON plan on stdout | Review claims, links, publishing copy, and consent before use; generator does not publish | **DONE** — runnable local generator |
| Paper-module trading signal scan/alert | `npm run signal -- path/to/candles.json`; optional n8n/GitHub wrapper | Validate OHLC candles and return a paper HOLD/placeholder result | On demand; watcher workflow can poll on its configured schedule | candle JSON → paper signal JSON | Paper only, no broker calls, no live execution, strategy placeholder remains HOLD; human/R13 review required | **DONE** — local validator; alert transport scaffolded |
| WhatsApp command handlers | `npm run whatsapp` after installing `whatsapp/package.json` and explicitly authenticating | Allow-list `/status`, `/trade`, `/content`, `/help`; echo other text | Event driven while local process runs | inbound message → local reply | Local QR/auth is opt-in; no production claim, no order route, review sender/session and message policy | **DONE** — non-production Baileys scaffold; not connected here |
| Client website kit one-command duplication | `npm run webkit:copy -- --client demo` | Copy the dependency-free `webkit/` starter into `clients/<client>` | On demand per client | client name/output/force → copied local files | Validate visible placeholders, links, pricing, hours, consent, and contacts; no hosting/deploy step | **DONE** — local copy utility |
| Weekly loophole audit | Human checklist from `docs/LOOPHOLES.md`; future scheduler hook | Review stale data, unsafe defaults, secret exposure, execution paths, and authority gaps | Weekly | repo state, logs, open questions → review record/issues | Stop on unresolved blockers; R13/security/legal checkpoint | **PLANNED** — checklist exists, no autonomous auditor |
| Email triage | Future official Gmail API worker | Label/summarize low-risk mail and prepare drafts; never send/delete automatically | Planned daily or event trigger | Gmail metadata/body with least privilege → labels and draft suggestions | Official Gmail API/OAuth only; human approval before send/archive/delete; no Gmail connection claimed | **PLANNED** |
| Research runs | Existing local research scripts plus nightly backtest/strategy-factory workflow files | Run bounded backtests or strategy research and save reviewable reports | On demand; nightly workflow files present | local/configured datasets → reports/logs | No fabricated data or performance promise; inspect provenance, assumptions, costs, and R13 gate | **DONE** — scaffolds/workflow files present; data availability varies |
| Dashboard boot | `npm run dashboard` or `npm run scheduler` | Serve static `dashboard/` on localhost:8080 | On demand or launchd at login | local files → local read-only UI | Capability labels are not proof of connected services; stop process when finished | **DONE** — dependency-free local server |
| Daily scheduler on Mel’s Mac | `npm run scheduler`; optional launchd template in `scheduler/` | Start dashboard, schedule daily local agents, optionally start WhatsApp, optionally run an explicit browser job | Run-at-load plus configured local daily time | repo path, opt-in flags, optional candle path → child-process logs | Lock prevents duplicates; WhatsApp/browser require explicit flags; child cleanup on exit; trading stays paper-only; not installed | **DONE** — skeleton, not installed |
| Nightly strategy-factory/backtest | GitHub Actions workflow trigger | Run bounded strategy/backtest job defined in workflow | Nightly when Actions schedule enabled | repository code and workflow inputs → artifacts/logs | Review permissions, data provenance, and output before relying on it | **DONE** — workflow file; execution not verified here |
| Paper-trading signal watcher | GitHub Actions or n8n workflow trigger | Invoke paper signal path and expose an alert-shaped result | Configured by workflow, not guaranteed active | configured candles/inputs → paper alert/log | Never add broker credentials or live execution; operator reviews every result | **DONE** — workflow/scaffold files; connection not claimed |
| Weekly KPI journal report | GitHub Actions workflow | Generate repository weekly KPI/journal artifact | Weekly when Actions enabled | local reports/journal inputs → report/artifact | Treat metrics as local records, not verified returns; review timestamps | **DONE** — workflow file and local report shape present |
| Multi-market scanner / sandbox / repo digest / Pages | GitHub Actions workflow triggers | Run bounded scanner, sandbox, digest, or static publishing job | Workflow-defined | repository/configured inputs → logs, digest, or static artifact | Check permissions, stale data, and publication content; no connected market feed asserted | **DONE** — workflow files present; runtime not verified |
| Social/web research ingestion | Planned browser/search/scraping integrations | Search, fetch, extract, normalize, and cite public research | On demand or bounded cadence | approved URLs/queries → cited notes | Respect robots.txt, terms, rate limits, official APIs, and human review; never bypass CAPTCHA | **PLANNED** — see `docs/AGENT_WEB.md` |

## Local entry points

```bash
npm run dashboard
npm run content -- --topic "build log" --count 4
npm run signal -- path/to/candles.json
npm run webkit:copy -- --client demo
npm run scheduler -- --help
```

The scheduler does not install launchd, npm packages, Chrome, WhatsApp auth, or an external connector. See `scheduler/README.md`, `docs/DAILY_RUN.md`, and `docs/AGENT_WEB.md` for human-controlled setup paths.
