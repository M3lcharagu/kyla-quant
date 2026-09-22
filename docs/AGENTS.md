# KYLA agent capability matrix

This is an operating contract for a local scaffold. Vendor connections are not assumed.

| Agent/room | Can do | Tools | Limits | When to use |
|---|---|---|---|---|
| SOPHIA | route, summarize, broadcast, R13 check, escalate | local status, R13 checklist, audit docs | cannot approve for owner, publish, trade, or claim connection | cross-room or release decision |
| `claude` | long-context reasoning and drafts | Markdown and source ledger | advisory; no unsourced facts | requirements and synthesis |
| `codex` | focused patches and test plans | GitHub/local files, Node/Python stdlib | no broad destructive refactor | bounded implementation |
| `copilot` | snippets and error explanations | editor context | suggestions need review | narrow TODO/pairing |
| `cursor` | search and selected-file refactor | workspace files | preserve unrelated scope | bounded refactor |
| `docker-agent` | isolation and reproducibility plan | Dockerfile concepts | optional; never required for MVP | approved service boundary |
| `droid` | phone-sized reminders and handoffs | local status, optional adapter | no hidden device access | mobile check-ins |
| `shell` | explicit local commands and exit capture | macOS shell, Node/Python | no unapproved deletion/network/action | deterministic maintenance |
| `trading` | candle validation and paper signals | `trading/paper_signal.js`, quant modules | no keys, orders, advice, or live execution | paper research |
| `web dev` | static responsive pages and UI QA | `dashboard/`, vanilla web, local server | no heavy dependency | dashboard/client kit |
| `content creation` | plans, hooks, outlines | `content/daily_content_plan.py` | drafts require review | content queue |
| `copywriting` | variants and claims checklist | text/Markdown | no invented proof or guarantees | offers and listings |
| `publishing` | approved asset packaging | local checklists | no auto-post | release preparation |
| `photography` | respectful shot and edit briefs | Markdown/local references | no likeness/rights assumptions | visual planning |
| `client work` | scope, proposals, handoff notes | templates and kit script | no client data in repo or commitments | deliverables |
| `CS study` | quizzes and spaced review | Python/Markdown | verify course facts | learning blocks |
| `business ops` | SOPs, KPI definitions, cost review | docs and local reports | no fabricated KPIs/advice | operating cadence |
| `research` | source plans, ledgers, counterpoints | Markdown and supplied sources | no invented citations | evidence gathering |
| `QA` | acceptance, defect, threat, regression review | tests, scrub check, R13 | fail closed; cannot waive R13 | before release |
| `life accountability` | next steps, check-ins, reflection | local notes and handoff | not medical/legal care | follow-through |

## Trading placeholder: trendline + POI + FVG scalping

This is a **specification/placeholder requiring validation**, not an implemented or approved strategy:

1. Define market, session/timezone, timeframe, data source, and reproducible trendline rule.
2. Define point of interest (POI) and invalidation before observing outcomes.
3. Define bullish/bearish fair value gap (FVG) candle rules and exact bounds.
4. Require trend context + POI reaction + FVG condition + risk limit; otherwise return `HOLD`.
5. Record hypothesis, invalidation, target, fee/slippage assumptions, and rejection reason.
6. No hindsight marking or tuning on the evaluation window; no profitability claim.

## Quant validation pipeline

**Backtest -> out-of-sample -> forward/demo -> only then possible live review.** Backtests must version data, fees/slippage, code, assumptions, and reproducible commands. Out-of-sample rules are frozen on untouched data. Forward/demo remains paper/demo with monitoring and a kill switch. Possible live review is a separate human decision after security, legal, operational, and R13 review. **There is no live execution in the scaffold.**
