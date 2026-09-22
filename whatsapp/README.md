# WhatsApp control-channel skeleton

This folder is a minimal, **non-production** Node.js skeleton using the community Baileys library. It connects with a local multi-file auth state, prints a QR code when supported, listens for `/status`, `/trade`, `/content`, and `/help`, and echoes other simple text messages.

It does not place trades, publish content, or provide an access-control system. This repository has **not been tested against WhatsApp**; treat the code as a starting point only.

## Local run

```bash
cd whatsapp
npm install
npm start
```

The first run may create `auth_info_baileys/`. Keep that directory private and local. It is ignored by Git and must never be committed or copied into an issue, log, artifact, or public deployment.

## Meta/Baileys caveats

- Baileys is an unofficial community library, not the official Meta WhatsApp Business Platform. WhatsApp/Meta terms, policies, protocol behavior, and account enforcement can change; review the current applicable terms and choose the official API when the use case requires it.
- The pinned dependency is only a reproducible starter choice, not a guarantee of compatibility or support. Review release notes and security advisories before upgrading or operating it.
- Authentication/session material is equivalent to account access. Protect the local files, restrict filesystem permissions, do not share QR codes, and provide a deliberate logout/revocation procedure.
- Add sender allowlists, group handling rules, input validation, rate limits, retries, backoff, monitoring, and safe failure behavior before accepting commands. Do not expose this process directly to the public internet.
- Messages and phone numbers are sensitive personal data. Minimize logs, avoid storing message bodies by default, document retention, and apply least-privilege access and secure backups.
- Review dependency risk, privacy obligations, abuse/spam risk, account rate limits, and operational security with a human reviewer. This is not a production-ready bot and must not be deployed to production without review.
