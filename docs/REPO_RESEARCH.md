# Repository Research

This ledger captures the supplied research scope for tools relevant to KYLA. It is not an independent verification of current stars, activity, compatibility, licensing, or hosted-service claims. Time-sensitive figures are marked as **research snapshots**.

## TOOLS

### Lane: Context generation and architecture orientation

- **Gitingest** — [upstream](https://github.com/cyclotruc/gitingest). MIT and free, for repository-to-LLM digests. **Useful for KYLA context generation**; bound ingestion size because large ingestion may exceed Vercel Hobby limits.
- **GitDiagram** — [upstream](https://github.com/ahmedkhaleel2004/gitdiagram). MIT and free, for interactive architecture diagrams. **Useful for phone-first codebase orientation**. The supplied research snapshot says 17k stars and active in Sep 2026; do not treat that as an independently verified current count.

### Lane: Read-only browsing and reusable agent workflows

- **github1s** — [upstream](https://github.com/conwnet/github1s). MIT and free, a read-only VS Code browser explorer. **Useful for mobile/old-Mac browsing**; private repositories need an auth token. The supplied research snapshot says 23.3k stars and active; do not treat that as an independently verified current count.
- **ECC (Everything Claude Code)** — [upstream](https://github.com/affaan-m/ECC). MIT, 266k stars, active; standardizes reusable agent skills, memory, security, and workflows. **Useful as a shared template with limits.** Evidence was supplied for Claude/Codex/Cursor, not verified for Copilot/docker-agent/droid/shell. The star/activity labels are research snapshots.

### Lane: Hosted-service integrations — not a free local platform

- **Higgsfield CLI** — [upstream](https://github.com/higgsfield-ai/cli).
- **Higgsfield skills** — [upstream](https://github.com/higgsfield-ai/skills).
- Scope: only the CLI plus agent skills that call authenticated hosted services were open-sourced; the $5.4B platform, weights, and pipelines were not. **Skip as a free local platform.** The supplied research attributes $700M ARR/$5.4B to the company via PRNewswire; those figures are not independently asserted. The specific PRNewswire article URL was not included in the supplied brief.

## Vercel guidance

Vercel Hobby is suitable for a light frontend, not heavy processing. Keep full-repository ingestion, diagram generation, and other expensive or long-running work out of the Hobby request path. See the detailed handling notes in [`GITHUB_TOOLKIT.md`](GITHUB_TOOLKIT.md).
