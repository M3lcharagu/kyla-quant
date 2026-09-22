# KYLA architecture

KYLA is intentionally a thin control plane around research, paper trading, and review. The design goal is a reliable small loop, not a heavy platform.

## System shape

```text
 iPhone 11 / WhatsApp (primary control)
              |
        command + approval
              v
      KYLA command center
       |       |        |
   agents   workflows  R13 gate
       |       |        |
       +--- GitHub ---+
             |
   paper/research modules -> static dashboard -> Vercel

 Discord is the backup control channel.
```

## Core constraints

### Devices and container layer

- The core operating surface is **phone-first**, with an **iPhone 11** as the primary mobile device and a **Mac running Catalina** as the local computer core.
- **Multipass** is the preferred container layer for Catalina-compatible Linux workloads. Keep images small and workloads disposable.
- **Docker Desktop and Orca require macOS 13+**; they are not assumed available on the Catalina core. Do not make either a hidden prerequisite.
- Local development must remain possible with plain Python, Node, and static files where practical.

### Control channels

- **WhatsApp is the primary control channel** for commands, approvals, alerts, and short operational summaries.
- **Discord is the backup channel**, not a second source of truth. A fallback message must still point to the same GitHub/audit record.
- Channel adapters must authenticate requests, restrict senders, expire approvals, deduplicate events, log correlation IDs, and fail closed on ambiguity.
- No channel should directly bypass risk controls or the R13 gate.

### Code and delivery

- **GitHub is the code home and audit trail.** Changes should be small, reviewable commits with no secrets and readable documentation.
- `dashboard/` is a dependency-free static site. It is designed for a **Vercel free-tier static deployment** with no server, database, build step, or framework required. Set the Vercel project root to `dashboard/` (or serve that directory as the static output).
- Avoid background polling, large bundles, paid APIs, and vendor lock-in. Prefer explicit refreshes and cached, timestamped inputs.
- The dashboard is a view and command-shell prototype; it is not an execution terminal.

## Agent topology

The seven core rooms are Orin (command), Sable (risk), Chroma (signals), Maven (macro), Vale (execution planning), Echo (journal), and Lumen (portfolio). Specialist rooms are on-demand and include Sophia for QA/security/legal plus data, research, content, and product-operations specialists.

Agents may propose, classify, summarize, or request approval. They do not silently broaden permissions. A specialist result is evidence for the core loop, not an approval by itself.

## Workflow topology

The 14 named workflows are command intake, daily brief, market scan, data-quality check, setup review, paper-signal proposal, risk review, paper-order reconciliation, journal update, portfolio pulse, research review, content/product operations, R13 review, and incident/weekly review. Each workflow should declare:

- input source and timestamp;
- owner and allowed action;
- read-only/paper/live mode (live is not implemented here);
- rate-limit and retry behavior;
- audit record and rollback/kill-switch behavior;
- R13 status before any external side effect.

## Mandatory R13 gate

**Nothing ships or advances to a new operational capability without the R13 QA/security/legal gate.** The gate must cover at least:

1. functional and regression QA;
2. secrets, permissions, channel, dependency, and data-security review;
3. legal/compliance, financial-disclaimer, provider-terms, and jurisdiction review;
4. paper/sandbox evidence and explicit unresolved-risk disposition;
5. human approval recorded against the commit or release.

A missing, stale, contradictory, or unauthorised input is a rejection, not an invitation to guess. See `docs/R13_QA_GATE.md` and `docs/LOOPHOLES.md`.

## Deployment posture

1. Review the commit in GitHub.
2. Run lightweight checks locally or in existing CI.
3. Complete and record R13.
4. Deploy only the static `dashboard/` directory to Vercel free tier.
5. Keep WhatsApp/Discord integrations outside this static site and behind least-privilege server-side controls.
6. Re-check limits, ownership, and rollback instructions after every material change.

## Explicit non-goals

- no live brokerage or exchange execution;
- no secret storage in GitHub or browser code;
- no fabricated backtests, prices, KPIs, or uptime claims;
- no requirement for Docker Desktop, Orca, a framework, or a paid service;
- no bypass around human approval and R13.
