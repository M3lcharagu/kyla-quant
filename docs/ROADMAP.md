# Day-1 roadmap

Keep the first day small, observable, and reversible. Follow this sequence:

1. **Multipass install** — install Multipass and create the smallest free-tier-friendly local VM needed for the sandbox.
2. **VS Code** — install VS Code and open the cloned repository as the working folder.
3. **Node** — install a supported Node.js LTS release; verify `node --version` and `npm --version`.
4. **Clone repo** — clone `M3lcharagu/kyla-quant` and confirm the current branch before editing.
5. **npm install** — install only the dependencies needed for the starter being exercised, beginning with `whatsapp/`.
6. **Run dashboard locally** — serve the existing dashboard locally and verify it without adding paid services or secrets.
7. **Vercel deploy** — deploy the static/dashboard surface on a free tier only after checking that no credentials or private data are included.
8. **WhatsApp bot test** — test the non-production skeleton locally with a disposable/reviewed account and the simple commands; do not expose it publicly.
9. **First lane go-live** — launch one reviewed lane with a human owner, a rollback path, and a written success check before expanding.

## Guardrails for the day

- Prefer free tiers, local files, and dependency-minimal paths. Do not add live trading, fake API keys, or unreviewed automation.
- Apply minimal security: least privilege, ignored auth/session files, no secrets in Git, limited logs, sender allowlists, and explicit privacy/rate-limit review before any integration is reachable.
- Run the repository's R13 review/QA gate before the first lane goes live, and record what was checked and what remains a paper/sandbox placeholder.
- The WhatsApp starter is not production-ready and has not been claimed as tested against WhatsApp; Meta/Baileys terms, compatibility, privacy, and account-risk review remain required.
