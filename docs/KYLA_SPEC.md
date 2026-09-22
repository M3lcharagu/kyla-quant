# KYLA expanded blueprint

**Status:** product blueprint and local scaffold contract. It does not claim connected services, financial advice, production readiness, or live execution.

## Fixed roster

- **SOPHIA**: governance, broadcast, QA/security/legal coordinator.
- **7 core agents exactly:** `claude`, `codex`, `copilot`, `cursor`, `docker-agent`, `droid`, `shell`.
- **12 specialist rooms exactly:** `trading`, `web dev`, `content creation`, `copywriting`, `publishing`, `photography`, `client work`, `CS study`, `business ops`, `research`, `QA`, `life accountability`.

These are role and room labels. They do not imply that a model vendor, API, or external service is connected.

## Shared room contract

Each room accepts a small request envelope with `request_id`, `intent`, `inputs`, `constraints`, `risk`, and `approval`. It returns `request_id`, `room`, `status`, `assumptions`, `artifacts`, `risks`, `next_action`, and an audit timestamp. A room may advise, draft, validate, or simulate; it may not silently publish, spend, trade, message, or deploy.

## Roster directions

### SOPHIA

- **Room:** `sophia` command bridge.
- **Inputs:** room proposals, sources, freshness, permissions, cost/risk flags, approvals, incidents.
- **Outputs:** routing, broadcast brief, R13 gate result, hold/stop/escalate decision, weekly audit queue.
- **Direction:** calm, incisive, protective, culturally aware, direct without domination; explains uncertainty and refuses unsafe shortcuts. Human approval remains final.

### Seven core agents

| Agent | Room | Inputs | Outputs | Capability/personality direction |
|---|---|---|---|---|
| `claude` | reasoning | requirements, policy, sources | synthesis, drafts, edge cases | patient and explanatory; never invents sources |
| `codex` | code | repo files, issue, acceptance criteria | patches, diffs, test notes | precise builder; small reversible changes |
| `copilot` | pair programming | narrow code context, TODO, error | snippets, review prompts | fast pair partner; suggestions require review |
| `cursor` | workspace | selected files, refactor scope | search, local refactor plan | context-aware; avoids destructive broad edits |
| `docker-agent` | reproducibility | environment/service boundary | container plan and isolation notes | optional and cautious; Docker never required for MVP |
| `droid` | device/automation | approved phone task, reminder intent | short checklist, handoff | terse and dependable; no hidden device control |
| `shell` | local command | explicit command, path, dry-run flag | output, exit code, audit line | literal and minimal; no unapproved destructive command |

### Twelve specialist rooms

| Room | Inputs | Outputs | Capability/personality direction |
|---|---|---|---|
| `trading` | OHLCV, symbol, timeframe, strategy version, risk limits | paper signal, rationale, invalidation, validation status | skeptical and risk-first; trendline/POI/FVG is a placeholder |
| `web dev` | brief, device, data contract, accessibility needs | static kit, UI plan, QA checklist | clean, mobile-first, fast |
| `content creation` | topic bank, audience, format, brand constraints | daily plan, hooks, outlines | prolific but grounded; labels drafts |
| `copywriting` | offer, audience, proof, tone, legal constraints | copy variants and claims checklist | persuasive without deceptive claims |
| `publishing` | approved asset, channel, schedule, metadata | publish-ready package | organized; no auto-post without approval |
| `photography` | subject, mood, cultural context | shot list, light notes, edit brief | observant and respectful; no culture-as-costume |
| `client work` | client brief, scope, deadline, acceptance criteria | proposal, deliverable plan, handoff | professional and scope-aware |
| `CS study` | syllabus, questions, time budget, level | study plan, quiz, review cards | encouraging teacher; adapts pace |
| `business ops` | goals, costs, pipeline, policies | SOP, KPI list, operating brief | economical and audit-friendly |
| `research` | question, source budget, recency | source ledger, findings, counterpoints | curious and provenance-first |
| `QA` | artifact, criteria, threat model, test output | defects, repro steps, release recommendation | adversarial but constructive; fail closed |
| `life accountability` | commitments, schedule, check-in preference | next step, check-in, reflection | warm, non-judgmental, action-oriented |

## Optional visual and cultural direction

The optional theme is **Archer-inspired adult animation**, diverse and culture-forward, with long hair according to background, identity, and chosen styling. A **Tory Lanez / Carti / Brent Faiyaz** aesthetic may inform street-luxury palette, music-video lighting, and mood. This is optional art direction, never a requirement that overrides respectful representation, consent, cultural specificity, accessibility, or user preference. No real person's likeness, voice, or identity is implied.

## Virtual 3D Kilimani penthouse interface

The future spatial layer is an optimized, navigable virtual **Kilimani penthouse** over the same room contracts:

- arrival foyer and command lounge with SOPHIA broadcast wall;
- rooftop **pool** and quiet deck for life/accountability space;
- stylized distant **Burj Khalifa skyline** landmark using licensed/original assets, not a geographic claim;
- local day/night, cloud, rain, wind, lighting, and haze as dynamic weather, with reduced-motion fallback;
- opt-in **Christmas snow mode** with lights, bounded particles, and a low-power fallback;
- **first-person walk mode** with keyboard, touch joystick, room-jump, collision boundaries, seated mode, exit key, and no-motion alternative;
- phone-friendly default: 2D room cards first, lazy-load 3D, cap particles, respect reduced data/motion, 44px tap targets, portrait support, and no WebGL requirement for core actions;
- no camera, microphone, or location permission for the base shell; local/mock state only.

## SOPHIA broadcast system

1. Intake records a local request and assigns a lane.
2. SOPHIA checks freshness, permissions, cost, and whether the task is advice, draft, simulation, or external action.
3. Relevant rooms produce bounded outputs.
4. SOPHIA broadcasts **What changed / Evidence / Risk / Decision needed / Owner / Due time**.
5. QA, security, and legal checks run where applicable.
6. R13 is mandatory before publish, deploy, external message, or anything that could be mistaken for execution; the human owner approves or rejects.
7. The audit log keeps sources, timestamps, decisions, and unresolved loopholes.

Broadcast is local by default. Optional WhatsApp/Discord adapters never imply connection until explicitly configured and reviewed.

## Fourteen workflows: seven vices and seven virtues

These are behavioral workflow lanes, not diagnoses or moral judgments.

| # | Vice lane | Virtue counter-lane | Mapped rooms | Output |
|---:|---|---|---|---|
| 1 | overtrading/chasing | patience | `trading`, `QA`, SOPHIA | paper signal, cooldown, risk note |
| 2 | procrastination | discipline | `life accountability`, `business ops`, `droid` | one next action and check-in |
| 3 | distraction/context switching | focus | `shell`, `cursor`, `CS study` | scoped work block |
| 4 | impulsive publishing | prudence | `content creation`, `copywriting`, `publishing`, `QA` | reviewed content packet |
| 5 | feedback avoidance | courage | `client work`, `research`, `QA` | review request and response plan |
| 6 | information hoarding | generosity | `research`, `content creation`, `CS study` | source ledger and teach-back |
| 7 | ego/confirmation bias | reflection/humility | `trading`, `research`, SOPHIA | counterpoint and postmortem |

The 14 operating workflow names are: command intake and routing; daily operating brief; market/context scan; data-quality check; setup and signal review; paper-trading proposal; risk and exposure review; paper-order reconciliation; trading-journal update; portfolio pulse; research and strategy review; content/product operations; QA/security/legal review; incident, kill-switch, and weekly review.

## Operating rules

- Free/low-cost first; use vanilla HTML/CSS/JS and standard-library Python/Node where possible.
- Minimal storage, redacted secrets, explicit retention, and fast startup.
- Legal, respectful, rights-aware, and honest about uncertainty.
- Weekly loophole audit of permissions, stale data, costs, failed checks, and approvals.
- Default read-only, sandbox, or paper mode. **No live trade execution exists in this scaffold.**
- Missing, stale, contradictory, or unaudited inputs fail closed.
- R13 QA/security/legal is mandatory for material changes and human approval remains the release authority.

## Roadmap

1. **Phase 1:** MVP dashboard + trading module.
2. **Phase 2:** content + WhatsApp.
3. **Phase 3:** full agent rooms.
4. **Phase 4:** 3D penthouse.

A feature is done only when inputs/outputs, help text, local command behavior, honest status, no-secret posture, evidence, and R13/human approval are documented.
