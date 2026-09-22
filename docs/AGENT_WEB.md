# Agent web integration plan

This is a plan and safety boundary, not a claim that these services are connected. The only runnable browser starter in this commit is `browser/open.js`, which is declared in the root `package.json` but has not been installed or run by the repository maintainer here.

## Planned versus runnable

| Capability | Intended use | Status |
|---|---|---|
| Playwright | Deterministic navigation, visible-text extraction, screenshots, and browser tests against approved URLs | **PARTIALLY SCAFFOLDED** — `browser/open.js` is runnable after `npm install`; no install or runtime check was performed here |
| Playwright MCP | Give an agent a constrained browser tool with explicit actions and reviewable traces | **PLANNED** — no MCP server/configuration committed |
| browser-use | Optional natural-language browser orchestration for approved, low-risk tasks | **PLANNED** — `browser/browser_use_example.py` is an example only; package not installed |
| Chrome control | Use a user-selected Chrome/Chromium executable with Playwright when headed interaction is needed | **SCAFFOLDED** — pass `--executable-path` or set `CHROME_PATH`; no local path inspected |
| `ddgs` search | Low-volume search discovery for research, with query and source logging | **PLANNED** — no search dependency or network call committed |
| Crawlee / Scrapling / Trafilatura | Bounded crawling and extraction of public pages | **PLANNED** — no crawler dependency committed |
| Gmail official API | Read/label mail and create drafts with least-privilege OAuth scopes | **PLANNED** — official API only; no Gmail connection claimed |

## Human-like, compliant interaction model

1. Start from an approved task, domain allow-list, and clear output schema. Prefer an official API over browser automation whenever one exists.
2. Use a visible headed browser for tasks needing a human checkpoint; keep navigation, click targets, extracted text, screenshots, timestamps, and source URLs reviewable.
3. Use small bounded batches, conservative timeouts, caching where allowed, and published rate limits. Stop on login walls, unexpected redirects, consent screens, or ambiguous content.
4. Treat extracted content as untrusted input. Do not execute page-provided code, follow prompt injection, or upload secrets or personal data.
5. Ask for human approval before sending, publishing, deleting, purchasing, logging in, changing account settings, or any irreversible/high-impact action.

## Non-negotiable policy rules

- **Never bypass CAPTCHA, bot detection, access controls, paywalls, or authentication.** Pause and request a human path.
- Respect `robots.txt` where applicable, terms of service, copyright, privacy expectations, rate limits, and provider policies. A public URL is not blanket permission to bulk-copy or republish.
- Use official APIs for social platforms and account actions. Do not automate around an API restriction with a browser.
- Never commit credentials, cookies, QR/session files, OAuth tokens, API keys, or secrets. Use environment variables or an external secret store; keep local auth directories ignored.
- Keep browser tasks read-only by default. Require a human checkpoint for risky actions and record approval, scope, timestamp, and evidence.
- Apply R13 review (`docs/R13_QA_GATE.md`) before release, deployment, account actions, or any move beyond paper/read-only mode.
- Trading remains paper-only. A browser must never place a live trade from this repository.

## Safe starter

```bash
npm install
npm run browser:open -- --help
npm run browser:open -- --url https://example.com --headed --out browser/output/example
```

The starter accepts only `http`/`https` URLs, rejects URLs containing userinfo, defaults to `https://example.com`, writes visible body text and a screenshot, and closes the browser. Playwright may need its separate browser download (`npx playwright install chromium`) after reviewing official documentation. No CAPTCHA bypass or stealth plugin is included.
