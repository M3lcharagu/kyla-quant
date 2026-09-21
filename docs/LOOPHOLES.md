# LOOPHOLES.md — control and delivery risk register

Repository: `M3lcharagu/kyla-quant`  
Status rule: a loophole is FIXED only when code is present, checked, and the remaining owner action is explicit. Provider/account/compliance actions remain open until the owner verifies them.

## P0 — must close before any live or funded execution

1. **Public repository, history, and incomplete scanning — FIXED (implementation in this commit).** `SECURITY.md`, `.gitignore`, `scripts/scrub_check.py`, and CI scanning are present. **REMAINS:** owner must make the repository private or scrub every reachable history/ref, rotate any exposed credentials, and review provider alerts.
2. **Global kill switch — PARTIAL / REMAINS.** `scripts/kill_switch.py` provides local and configurable remote flags, fail-closed remote errors, logging, and a spread/news guard. **REMAINS:** wire `require_clear()` as the first optional check in every strategy factory, journal, deployment, and execution adapter, then exercise it from a second operator path.
3. **R13 CI/deploy enforcement — FIXED for repository checks (implementation in this commit).** `.github/workflows/ci.yml` compiles all scripts and runs smoke/tests on push and PR. **REMAINS:** require branch protection/status checks and make every real deployment/execution launcher consume a passing status.

## P1 — close before unattended paper trading or external control

4. **iPhone/Mac single-host recovery — REMAINS.** Owner must define a second supported operator path, encrypted durable state/backups, RPO/RTO, and rehearse restore and host-loss procedures.
5. **Least privilege — FIXED for policy (implementation in this commit).** `docs/LEAST_PRIVILEGE.md` lists baseline and forbidden scopes. **REMAINS:** configure and verify each provider key, including no withdrawal/transfer/admin access.
6. **WhatsApp/Gmail/device trigger isolation — REMAINS.** Owner must use signed expiring commands, allowlists, human approval, deduplication, rate limits, audit logs, and a kill switch for each trigger.
7. **Deriv/account compliance — REMAINS.** Owner must obtain written broker/jurisdiction review, confirm KYC/AML, tax, leverage, instruments, API, and paper/live permissions, and enforce the resulting capability matrix.
8. **Exchange key permissions, IP allowlist, withdrawals, and 2FA — FIXED for checklist (implementation in this commit).** `docs/EXCHANGE_SECURITY.md` documents the required controls. **REMAINS:** owner must configure and verify read-only/trade-only keys, IP allowlists, disabled withdrawals/transfers, and 2FA with each provider.
9. **Seven-agent authorization and separation of duties — REMAINS.** Owner must define identities, deny-by-default scopes, approvals/quorum, conflict handling, immutable audit IDs, and limits.
10. **Correlated yen exposure — REMAINS.** Risk owner must implement currency-factor exposure aggregation, JPY limits, stress tests, stale-data rejection, and pre-order portfolio checks.
11. **Spread, news, and intervention locks — PARTIAL / REMAINS.** `scripts/kill_switch.py` and `config/guards.default.json` implement NEWS_GUARD and configurable spread rejection. **REMAINS:** wire the guard into the strategy factory/execution path, add validated event/quote data, and test fail-closed behavior.

## P2 — close before scaling, continuous operation, or paid integrations

12. **$150/week spend and $5,000 target — REMAINS.** Owner must approve a measured risk budget, independent stop conditions, and net-of-all-cost reporting; no return target is guaranteed.
13. **Vercel limits and external service/swap costs — REMAINS.** Owner must verify quotas, rate limits, vendor pricing, data/LLM/swap/funding costs, caps, alerts, and halt behavior.

## Exact owner actions still required

- Make this repository private **or** complete and independently verify a full history scrub; revoke/rotate any possibly exposed credentials.
- Configure the local and remote kill-switch endpoints and call them first from every factory, journal, deployment, and execution adapter; test from a second device/process.
- Enable branch protection/status requirements on `main` for `CI / checks` and prevent deployment when checks are absent or failing.
- Configure exchange and other provider accounts with no withdrawal/transfer/admin rights, fixed IP allowlists, hardware-backed 2FA, short-lived keys, and provider audit review.
- Complete broker/jurisdiction/KYC/AML/tax review and document the account capability matrix.
- Complete recovery, trigger-authentication, multi-agent authorization, yen exposure, market-data validation, budget, and vendor-cost controls described above.
