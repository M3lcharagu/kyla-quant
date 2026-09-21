# Security policy

## Public repository and history risk

This repository is public. Removing a credential from the current tree does **not** remove it from Git history, forks, caches, releases, logs, or local clones. Treat every credential that may have touched this repository as compromised: revoke it at the provider, rotate it, and verify audit logs.

Before connecting a funded account:

1. Make the repository private, or complete a documented history scrub (all refs and reachable objects), then verify the scrub from a fresh clone.
2. Run `python scripts/scrub_check.py` locally and in CI. This is a pattern check, not proof of a clean history.
3. Enable provider secret scanning, validity checks, and push protection where available.
4. Keep real configuration, databases, logs, screenshots, exports, and recovery codes outside the repository.
5. Use separate paper/live credentials and revoke unused tokens.

## Reporting

Do not open a public issue with a secret or private account data. Revoke the credential first, preserve only non-sensitive incident metadata, and contact the repository owner through a private channel.

## Scope

The project is a research/paper-trading scaffold. The kill switch and CI checks are defense-in-depth and do not establish exchange, legal, tax, compliance, or operational readiness.
