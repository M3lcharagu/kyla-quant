# LOOPHOLES.md — initial KYLA control checklist

This is a living audit checklist. A loophole is not closed because a document mentions it; close it with code, configuration, a test, and an owner decision. Until then, mark it **OPEN** and fail closed.

## 1. WhatsApp channel security

- [ ] **OPEN — identity:** restrict commands to an explicit allowlist of verified senders and devices; reject unknown numbers.
- [ ] **OPEN — authentication:** use signed, expiring command envelopes or an equivalent provider-verified webhook; never trust display names.
- [ ] **OPEN — replay/deduplication:** assign a unique command ID, timestamp, nonce, and expiry; reject duplicates and stale messages.
- [ ] **OPEN — approvals:** require a human approval record for consequential actions; separate requester and approver where practical.
- [ ] **OPEN — secrets:** keep provider tokens, webhook secrets, and phone identifiers out of GitHub, logs, screenshots, and browser code.
- [ ] **OPEN — privacy:** minimise message content, define retention, redact sensitive data, and document provider/jurisdiction obligations.
- [ ] **OPEN — fallback:** Discord is backup only; a fallback event must preserve the same audit ID and permission checks.

## 2. Free-tier and static-host limits

- [ ] **OPEN — Vercel:** verify current free-tier bandwidth, build, function, request, and deployment quotas before enabling anything beyond static files.
- [ ] **OPEN — polling:** prefer manual refresh or low-frequency jobs; add caching, backoff, budgets, and alerts before any external polling.
- [ ] **OPEN — storage:** do not assume durable local state on a static host; keep source records in GitHub or an explicitly reviewed store.
- [ ] **OPEN — spend guard:** define a hard monthly budget and an owner for provider billing alerts; no silent upgrade path.
- [ ] **OPEN — dependency drift:** keep the dashboard framework-free and audit any optional CDN asset for availability, licensing, and fallback behavior.

## 3. Multipass versus Docker risks

- [ ] **OPEN — Catalina support:** test the chosen Multipass version and image on the actual Mac Catalina core.
- [ ] **OPEN — unsupported assumptions:** Docker Desktop and Orca require macOS 13+; do not document or script either as a Catalina prerequisite.
- [ ] **OPEN — isolation:** define mounts, network egress, exposed ports, image provenance, and disposal rules for each Multipass VM.
- [ ] **OPEN — recovery:** document VM backup/restore, disk pressure, update rollback, and a host-level kill switch.
- [ ] **OPEN — parity:** record differences between local Multipass, CI, and any future hosted runtime before relying on behavior.

## 4. API rate limits and data quality

- [ ] **OPEN — inventory:** record each provider's authentication method, quota, burst limit, reset window, terms, and owner.
- [ ] **OPEN — backoff:** implement bounded retries with jitter, `Retry-After` handling, circuit breaking, and a visible degraded state.
- [ ] **OPEN — freshness:** attach source timestamps and timezone to market/context data; reject stale, partial, contradictory, or out-of-order inputs.
- [ ] **OPEN — cost:** estimate request volume before enabling a workflow; cache immutable responses and avoid duplicate fetches across agents.
- [ ] **OPEN — no claims:** do not publish backtest or performance metrics without reproducible inputs, cost/slippage assumptions, and an independent review.

## 5. R13 QA/security/legal gate

- [ ] **OPEN — QA:** tests, smoke checks, accessibility checks, and rollback path are attached to the commit/release.
- [ ] **OPEN — security:** secrets scan, least-privilege review, dependency review, channel review, and logging/redaction check are complete.
- [ ] **OPEN — legal:** financial-advice boundary, disclaimers, provider terms, data licenses, privacy, jurisdiction, and promotion status are reviewed.
- [ ] **OPEN — paper first:** paper/sandbox behavior is evidenced; no live execution path is present in this scaffold.
- [ ] **OPEN — approval:** named human owner, date, commit SHA, decision, and unresolved risks are recorded.
- [ ] **OPEN — enforcement:** CI/deploy tooling blocks release when R13 is missing, stale, or failed; no workflow may bypass it.

## Release rule

Until the relevant boxes are closed and R13 is approved, KYLA remains a local/static, read-only or paper-only scaffold. Do not interpret a green dashboard card, signal proposal, or successful script run as permission to trade or deploy.
