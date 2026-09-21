# Least-privilege API access

Use separate credentials per venue, environment, and purpose. Start with no permissions and add only what a documented operation requires.

## Required baseline scopes

- Market-data access: public read-only endpoints only, where possible.
- Paper-trading: read balances/positions, read orders, and create/cancel orders only when paper execution is explicitly approved.
- Journaling/reporting: read-only trade and account history, with no order permissions.
- Monitoring: read-only status and market data; no account mutation.

## Forbidden scopes

Never grant this project or its automation:

- Withdrawals, transfers, crypto address-book management, or bank/payment access.
- API-key creation/deletion, permission changes, account administration, or user management.
- Margin/leverage changes or other account-level risk changes unless separately approved and isolated.
- Any live-trading permission before the P0 controls, provider review, and paper validation are complete.

Use IP allowlists, short expirations, provider audit logs, and rotation. Store secrets in an approved secret manager, never in YAML, JSON, issues, prompts, or the repository.
