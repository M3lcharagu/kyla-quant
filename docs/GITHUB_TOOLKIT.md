# GitHub Toolkit for KYLA

This guide records the supplied research scope for five GitHub projects that may help with KYLA (`M3lcharagu/kyla-quant`). It is deliberately scoped: licensing, price, stars, activity, and capability statements below are research notes rather than a fresh audit. Star/activity figures are time-sensitive **research snapshots** and are not presented as independently verified current counts.

## Vercel boundary

Vercel Hobby is suitable for a light KYLA frontend, but not for heavy processing. Keep large repository ingestion, diagram generation, model work, and other long-running or resource-intensive jobs out of the Hobby request path; use an appropriate local or external worker/job boundary instead. Do not add secrets or dependencies to use any of the tools below.

## Gitingest

- **Source:** <https://github.com/cyclotruc/gitingest>
- **Supplied scope:** MIT; free; creates repository-to-LLM digests.
- **KYLA use:** **USEFUL for KYLA context generation.** A digest can give an agent a bounded view of the trading, dashboard, automation, and documentation layout before it proposes a change.
- **Caveat:** Large ingestion may exceed Vercel Hobby limits. Prefer bounded paths, smaller inputs, or an execution environment intended for heavier processing rather than putting a full-repository ingest in a frontend request.

## GitDiagram

- **Source:** <https://github.com/ahmedkhaleel2004/gitdiagram>
- **Supplied scope:** MIT; free; interactive architecture diagrams.
- **KYLA use:** **USEFUL for phone-first codebase orientation.** An architecture view can help locate the web, quant, trading, automation, and data boundaries when reviewing KYLA from a phone.
- **Research snapshot:** 17k stars and active in Sep 2026, as supplied research facts. These figures are time-sensitive and are not independently verified current counts here.
- **Caveat:** Treat the diagram as an orientation aid, not as the source of truth for runtime behavior; confirm important changes in the repository files and tests.

## github1s

- **Source:** <https://github.com/conwnet/github1s>
- **Supplied scope:** MIT; free; read-only VS Code browser explorer.
- **KYLA use:** **USEFUL for mobile/old-Mac browsing.** It provides a low-friction way to inspect KYLA documentation and source when a full local IDE is inconvenient.
- **Research snapshot:** 23.3k stars and active, as supplied research facts. These figures are time-sensitive and are not independently verified current counts here.
- **Caveat:** Private repositories need an auth token. Use least privilege, do not paste tokens into documentation, and remember that this is a read-only browsing aid rather than a write/validation workflow.

## ECC (Everything Claude Code)

- **Source:** <https://github.com/affaan-m/ECC>
- **Supplied scope:** “Everything Claude Code”; MIT; 266k stars; active. It standardizes reusable agent skills, memory, security, and workflows.
- **KYLA use:** **USEFUL as a shared template with limits.** KYLA can borrow the structure for repeatable research, review, security, and context-management practices instead of inventing each agent workflow from scratch.
- **Compatibility boundary:** The supplied evidence covers Claude, Codex, and Cursor. It does **not** verify support for Copilot, docker-agent, droid, or shell. Do not imply those integrations are supported without checking the upstream project and testing the specific workflow.
- **Research snapshot:** The 266k-star and active labels are time-sensitive supplied research facts, not independently verified current counts here.

## Higgsfield

- **Sources:** <https://github.com/higgsfield-ai/cli> and <https://github.com/higgsfield-ai/skills>
- **Supplied scope:** Only the CLI plus agent skills that call authenticated hosted services were open-sourced. The $5.4B platform, weights, and pipelines were **not** open-sourced.
- **KYLA decision:** **SKIP as a free local platform.** The open-source pieces should not be treated as a locally runnable copy of the hosted Higgsfield platform or as a source of its weights/pipelines. Any use would be an authenticated hosted-service integration and should be evaluated separately.
- **Company-reported context:** The supplied research attributes $700M ARR and a $5.4B valuation to the company via PRNewswire. Those figures are clearly attributed and are **not independently asserted** here. The specific PRNewswire article URL was not included in the supplied brief, so no unverified article link is fabricated.

## Adoption checklist

1. Keep KYLA source-of-truth behavior in the repository, tests, and reviewed configuration; use these tools for context, orientation, or workflow scaffolding.
2. Keep heavy processing away from a Vercel Hobby frontend path.
3. Treat star counts and activity labels as research snapshots, not guarantees of maintenance or compatibility.
4. Never commit secrets, auth tokens, generated private-repository content, or new dependencies solely because a tool can access them.
5. Re-check upstream licenses, support, limits, and security before production adoption.
