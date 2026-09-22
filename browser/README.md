# Browser starters

These are small, opt-in examples for approved, read-only web work. They are not a stealth scraper, CAPTCHA bypass, login bot, or trading executor.

## Playwright starter

`open.js` accepts only `http`/`https` URLs, rejects embedded credentials, defaults to `https://example.com`, extracts visible body text to `<prefix>.txt`, saves `<prefix>.png`, and closes the browser.

```bash
npm install
npm run browser:open -- --help
npm run browser:open -- --url https://example.com --out browser/output/example
npm run browser:open -- --url https://example.com --headed --chrome
```

The root `package.json` declares Playwright, but dependencies and browser binaries were **not installed or run as part of this commit**. If needed, use the reviewed Playwright command `npx playwright install chromium` after checking official Catalina support.

### Chrome configuration

- `--headed` shows a window; without it the starter is headless.
- `--executable-path "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"` selects a binary.
- `CHROME_PATH=/absolute/path npm run browser:open -- --headed` is an alternative.
- `--chrome` checks common macOS paths and otherwise falls back to Playwright’s browser.

macOS Catalina support depends on installed Node, Playwright, and browser versions; this repository does not claim a Catalina runtime check.

## Optional browser-use example

`browser_use_example.py` is not included in `package.json`. It prints a clear install message when `browser-use` is absent. Use an isolated environment, review provider terms, keep tasks read-only, and stop for approval before risky actions.

## Compliance boundary

Respect robots.txt where applicable, terms, copyright, rate limits, and consent. Never bypass CAPTCHA, bot detection, paywalls, or access controls. Use official APIs for account/social actions, keep secrets outside the repository, and apply R13 review. See `docs/AGENT_WEB.md`.
