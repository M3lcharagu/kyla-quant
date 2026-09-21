# Exchange security checklist

Complete and record this checklist for each exchange account before any connection:

- [ ] Create a dedicated key for this project; never reuse a personal or withdrawal key.
- [ ] Enable read-only permissions for research and monitoring.
- [ ] If paper execution is approved, allow only the minimum trade/order operations.
- [ ] Explicitly disable withdrawals, transfers, address-book changes, account administration, and API-key management.
- [ ] Configure a fixed IP whitelist where the provider supports it; verify the runtime egress IPs.
- [ ] Enable hardware-backed 2FA/security keys on the exchange account and its email/admin control plane.
- [ ] Store the secret only in a secret manager; do not put it in config files, logs, screenshots, or CI output.
- [ ] Set an expiry/rotation date, test revocation, and review provider audit logs.
- [ ] Confirm the account is paper/testnet and that jurisdiction, KYC/AML, tax, and product restrictions are understood.

A green checklist is not evidence that a provider granted the intended permissions; verify the effective permission screen and perform a harmless denied-withdrawal/API-admin test where the provider supports it.
