# LOOPHOLES.md — control and delivery risk register

**Repository:** `M3lcharagu/kyla-quant`  
**Scope:** research/paper-trading scaffold and the proposed operating model.  
**Snapshot checked:** `main` at `687958eed373a63f196e90d2a2d99b1769fa9255` on 2026-09-19.

## Evidence status

- **Repo-verified:** observed directly in the public repository or GitHub repository metadata at the snapshot above. The repository is public, its default branch is `main`, GitHub Issues is enabled with no open issues at audit time, and no `.github/workflows` path was present in the tree. The tree contains a Dockerfile, `config.example.yaml`, R13 documentation/code, a risk engine, paper-trading adapters, and market-intel modules.
- **External/unverified:** supplied audit observations about operating devices, WhatsApp/Gmail/Vercel/Deriv/exchange accounts, costs, policy, or deployment. These are not claims that those systems are configured in this repository. They require owner verification before live trading.
- **Security note:** this document intentionally contains no credentials, tokens, keys, addresses, or private message content.

## Top five fix-first

1. **P0 — Public-repo and history assurance:** rotate/revoke anything ever exposed, complete a full-history secret scan, and keep push protection plus CI scanning enforced.
2. **P0 — Global kill switch:** implement a durable, account-wide deny gate that every order path must consult, with fail-closed behavior and an independently reachable operator control.
3. **P0 — R13 CI/deploy gate:** turn the R13 checklist into automated tests and a required status check; block deploys and live/paper execution when it fails.
4. **P1 — Least-privilege control plane:** harden exchange/Gmail permissions, define seven-agent authorization, and treat WhatsApp/pasted content as untrusted data rather than instructions.
5. **P1 — Exposure and market-safety locks:** cap correlated yen exposure and block entries on excessive spread, stale/news-risk windows, and central-bank/intervention conditions.

## P0 — must close before any live or funded execution

### P0-1 — Public repository, history, and incomplete scanning

- **Status:** Public repository and enabled secret-scanning/push-protection settings are **repo-verified**. The supplied audit found no current secret alerts. A complete historical scan is **external/unverified/not established**; provider non-pattern scanning and validity checks were not enabled in the verified metadata.
- **Loophole:** A public repository can disclose a credential that was removed from the tip but remains in Git history, forks, caches, artifacts, or ignored local files. A partial scanner can miss non-provider patterns and custom formats.
- **Why it hurts:** A historical key can be replayed even when current files look clean; a false sense of “no alerts” is not proof of clean history or safe accounts.
- **Concrete fix:** Revoke and rotate every credential that may have touched the repo; run a full-history scan over all refs and reachable objects with provider and custom patterns; review GitHub alerts and audit logs; enable non-provider patterns and validity checks where appropriate; add a CI secret scanner and a documented release checklist. Never paste findings into issues or this document.
- **Effort:** M (1–2 days plus credential-owner coordination).
- **Owner:** Mel + Security/DevOps.

### P0-2 — Global kill switch is only in-process

- **Status:** The supplied audit says `risk_engine` kill switch is **repo-verified as in-process only**. No external/deployment control plane was verified.
- **Loophole:** A process restart, second worker, stale container, alternate adapter, or direct exchange call can bypass an in-memory flag.
- **Why it hurts:** Emergency risk shutdown is not global, durable, or auditable; the operator may believe trading is stopped while another path can still submit orders.
- **Concrete fix:** Store a versioned global halt state in a durable, highly available store; require every order-intent and execution adapter to read it immediately before submission; fail closed when the state store is unavailable; add an authenticated operator endpoint/CLI with audit log, expiry/acknowledgement, restart persistence, and a test that proves all adapters stop.
- **Effort:** M–L (2–5 days plus failure-mode tests).
- **Owner:** Trading platform owner + Security.

### P0-3 — R13 is not CI/deploy enforced

- **Status:** R13 documentation and `src/kyla_quant/qa/r13_gate.py` are **repo-verified**; the supplied audit found no `.github/workflows`, so enforcement is not CI/deploy verified.
- **Loophole:** R13 can be documented or run manually while a commit, image, or deploy bypasses it.
- **Why it hurts:** Required safety and quality checks become advisory exactly when a rushed change needs them most.
- **Concrete fix:** Add a GitHub Actions workflow that runs tests, type/lint checks, R13, dependency/security scans, and config validation; require the status check and review protection on `main`; make deployment and any execution launcher consume only a passing commit/image digest; fail closed when checks are missing or inconclusive.
- **Effort:** M (1–3 days).
- **Owner:** DevOps/maintainer.

## P1 — close before unattended paper trading or any external control integration

### P1-1 — iPhone-only control, old Mac single-host dependency, and disaster recovery

- **Status:** iPhone-only control and old-Mac single-host dependency are **external/unverified**. The repo contains a Dockerfile, but no HA, backup, restore, or DR evidence was verified.
- **Loophole:** Control and execution depend on one aging Mac and one mobile control path; failure, loss, OS update, network outage, or lockout can remove both visibility and intervention.
- **Why it hurts:** A system that cannot be observed or stopped reliably can accumulate risk during an incident; unrehearsed backups do not count as recovery.
- **Concrete fix:** Define a supported runtime and a second operator path; move state/configuration to encrypted durable storage; back up journals, configuration schema, and halt state with retention and encryption; document RPO/RTO; rehearse restore and loss-of-host procedures; require a heartbeat and page on stale control plane.
- **Effort:** M (2–4 days plus a restore drill).
- **Owner:** Mel + Platform/Operations.

### P1-2 — WhatsApp/pasted-content prompt injection, Gmail scopes/watchers, and trigger hygiene

- **Status:** No WhatsApp/Gmail/device trigger configuration was verified in the repo; the proposed channels and Gmail watchers are **external/unverified**.
- **Loophole:** Human-pasted or inbound message text can be mistaken for an authorized command; broad Gmail scopes, duplicate watchers, stale leases, replayed events, or unbounded triggers can invoke tools repeatedly.
- **Why it hurts:** Prompt injection can cause unauthorized orders or data disclosure; overly broad scopes and duplicate triggers amplify blast radius and cost.
- **Concrete fix:** Treat all message/email content as untrusted data; use a separate signed command envelope with nonce, expiry, explicit intent, human confirmation, and allowlisted destinations; request least-privilege Gmail scopes, isolate read-only ingestion from send/modify rights, verify watcher ownership and renewal, deduplicate by event ID, rate-limit, expire leases, log and alert on retries, and provide a kill switch for every trigger.
- **Effort:** M–L (3–7 days).
- **Owner:** Security + Integrations owner; Mel approves command policy.

### P1-3 — Account rules and Deriv compliance

- **Status:** Deriv/account rules, jurisdiction, KYC/AML, leverage, instrument, API, and paper/live status are **external/unverified**; no Deriv integration was verified in the repo.
- **Loophole:** The strategy can act outside account terms, local law, broker restrictions, or the permitted paper/live environment.
- **Why it hurts:** Orders can be rejected, accounts suspended, funds impaired, or activity become non-compliant; software assumptions are not legal or broker approval.
- **Concrete fix:** Obtain written broker and jurisdiction review; maintain a per-account capability matrix (instruments, leverage, order types, hours, rate limits, data rights, paper/live); enforce it before order creation; prohibit live enablement until KYC/AML, tax, disclosure, and terms are confirmed; revalidate after account or policy changes.
- **Effort:** M (1–3 days of engineering plus external review).
- **Owner:** Mel + Compliance/legal adviser.

### P1-4 — Exchange key permissions, IP allowlisting, withdrawals, and 2FA

- **Status:** Exchange accounts and keys are **external/unverified**; no exchange key configuration was found in the repo. The connected GitHub account metadata showed 2FA disabled, which is a verified account-security finding for GitHub, not proof about exchange accounts.
- **Loophole:** A trading key may have withdrawal or account-management rights, no IP restriction, weak storage, or no strong second factor.
- **Why it hurts:** Credential compromise can become irreversible asset loss or unauthorized account changes; a compromised GitHub account can also alter code or releases.
- **Concrete fix:** Create separate paper/live keys with trade-only, no-withdrawal, no-transfer, and no-account-admin permissions; allowlist fixed egress IPs where supported; store secrets in a secret manager; rotate and revoke on incident; require hardware-backed 2FA/security keys for GitHub and exchange control-plane accounts; test that withdrawal/API-admin calls are denied.
- **Effort:** S–M (hours to 2 days plus provider setup).
- **Owner:** Mel + Security.

### P1-5 — Seven-agent authorization and separation of duties

- **Status:** A seven-agent design is **external/unverified**; no agent authorization/configuration was found in the repo.
- **Loophole:** Multiple agents can independently escalate, approve, or execute without a common policy, quorum, identity, or conflict handling.
- **Why it hurts:** One compromised or confused agent can turn a low-confidence suggestion into a funded action; correlated agent errors are hard to attribute.
- **Concrete fix:** Define named agent identities and capabilities; separate research, risk, approval, and execution; use deny-by-default tool scopes, policy-as-code, signed decisions, unique request IDs, spend/notional limits, quorum or human approval for live actions, conflict/timeout handling, and immutable audit logs. No agent may grant itself permission.
- **Effort:** L (1–2 weeks).
- **Owner:** Mel + Security/Platform architect.

### P1-6 — Correlated yen exposure

- **Status:** The yen concentration and portfolio are **external/unverified**; repo modules document strategies but no live portfolio-wide exposure governor was verified.
- **Loophole:** USD/JPY, EUR/JPY, GBP/JPY, futures, options, or proxies can create one hidden JPY factor even when trades look diversified.
- **Why it hurts:** A single yen shock, intervention, gap, or funding event can breach aggregate risk limits across strategies.
- **Concrete fix:** Normalize positions into currency-factor exposures; set gross/net JPY limits, per-instrument and strategy limits, stress scenarios for gaps/intervention, and a portfolio-level reservation before order submission; reject trades when data is stale or correlation/hedge mapping is unknown; monitor realized and potential exposure.
- **Effort:** M–L (3–7 days).
- **Owner:** Risk owner.

### P1-7 — Spread, news, and intervention locks

- **Status:** Market-intel and upcoming-event modules exist in the repo, but enforceable spread/news/intervention execution locks were not verified. Event sources and thresholds are **external/unverified**.
- **Loophole:** A signal can pass while spreads are abnormal, data is stale, high-impact news is imminent, or official intervention risk is elevated.
- **Why it hurts:** Slippage and gap risk invalidate backtests and can turn a nominally small stop into a large loss.
- **Concrete fix:** Add pre-trade and in-trade gates for spread percentile, liquidity, quote age, venue health, scheduled news blackout, unscheduled-news circuit breaker, and central-bank/intervention risk; use conservative fail-closed defaults; log the reason for every block and test boundary conditions.
- **Effort:** M (2–5 days plus data-source validation).
- **Owner:** Market-data + Risk owners.

## P2 — close before scaling, continuous operation, or paid integrations

### P2-1 — $150/week on a $5,000 target

- **Status:** The target and weekly budget are **external/unverified** and are not a repo performance guarantee.
- **Loophole:** A fixed $150/week spend against a $5,000 target can be treated as a required return or acceptable loss without a measured risk budget.
- **Why it hurts:** It encourages spend chasing, hides total cost of ownership, and can confuse research progress with a financial outcome.
- **Concrete fix:** Separate capital, operating budget, and loss limit; define a maximum weekly spend and stop condition independent of profit target; track net return after fees, slippage, data, LLM, hosting, and swap/funding; require a written go/no-go review after a statistically meaningful paper sample.
- **Effort:** S (half day to 1 day).
- **Owner:** Mel + Finance/risk owner.

### P2-2 — Vercel limits and external service/swap costs

- **Status:** No Vercel/deployment configuration was verified in the repo; Vercel limits and LLM, market-data, exchange, and swap/funding costs are **external/unverified**.
- **Loophole:** Serverless/runtime quotas, cold starts, execution duration, websocket limitations, rate limits, token usage, vendor pricing, and funding/swap costs may be omitted from the design.
- **Why it hurts:** A control or data path can time out or become unexpectedly expensive; a profitable paper result can be negative net of all fees.
- **Concrete fix:** Keep time-sensitive execution off unsuitable edge/serverless paths; document quotas and rate-limit budgets; add cost meters, daily/monthly caps, alerts, caching, backoff, and vendor fallbacks; record exchange fees, spread, slippage, funding/swap, and LLM/data costs in reports; halt nonessential calls at budget cap.
- **Effort:** M (1–3 days plus vendor verification).
- **Owner:** Platform + Finance.

### P2-3 — Docker runtime isolation

- **Status:** A Dockerfile is **repo-verified**; hardened runtime isolation is not verified.
- **Loophole:** A container may run as root, have broad filesystem/network access, mutable dependencies, or access to credentials beyond its role.
- **Why it hurts:** A dependency or prompt-injected tool can pivot from research to host, secret, or order-control access.
- **Concrete fix:** Use a pinned minimal image and lockfile; run as non-root with read-only filesystem, dropped capabilities, seccomp/AppArmor, resource limits, no host socket, restricted egress, separate research/data/execution networks, short-lived credentials, image scanning/signing, and a reproducible build. Verify the effective runtime, not just the Dockerfile.
- **Effort:** M (1–3 days).
- **Owner:** Platform/Security.

## Mel-personal-actions

1. Do not place live credentials, recovery codes, API keys, personal email content, or private message text in the repository, issues, prompts, or screenshots.
2. Rotate/revoke any credential that may have appeared in repository history or copied into an untrusted channel; confirm results with the provider rather than relying only on a scanner.
3. Enable hardware-backed 2FA/security keys on GitHub, exchange, email, and deployment accounts; remove unused sessions and tokens.
4. Keep all trading connections paper-only until the P0 gates pass and broker/jurisdiction review is documented.
5. Approve a written allowlist of agents, tools, destinations, notional limits, and human-confirmation points before enabling any WhatsApp/Gmail/device control.
6. Nominate an emergency operator and test the global halt from a second device; rehearse host loss, restore, and account-lockout procedures.
7. Review weekly spend, all fees, exposure by currency factor (especially JPY), and paper/live status; stop on budget, data-quality, compliance, or control-plane failure.

## Definition of done

A loophole is closed only when the fix is implemented, covered by an automated or repeatable test, observable in logs/alerts, documented with an owner and expiry/review date, and verified in the actual runtime/account—not merely present as a code comment or paper checklist.
