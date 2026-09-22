# Local automation

Kyla is intentionally a local, paper-only research workspace. These commands make useful paths discoverable without implying that a connector, market feed, broker, WhatsApp session, or production deployment is active.

## Safety boundary

- **Paper only:** `trading/paper_signal.js` validates candle data and returns a HOLD decision from a deliberately unimplemented strategy placeholder. It never places an order.
- **No secrets:** do not commit credentials, QR/session files, API keys, tokens, or personal contact data. The WhatsApp auth directory is ignored locally.
- **No fabricated data:** the dashboard reports static/local capability labels, not live balances, prices, delivery receipts, uptime, or returns.
- **Human gate:** R13 QA, security/legal review, and explicit human approval remain required before any future release decision.

## First run

```bash
./setup.sh --help
./setup.sh
npm run check
```

`setup.sh` is a check-only bootstrap. It does not download dependencies, create credentials, or connect to an external service. On macOS Catalina it explicitly verifies that `node` and `npm` are available and reports their versions.

## One-command entry points

| Command | Purpose | Honest status |
| --- | --- | --- |
| `npm run dashboard` | Serve the static dashboard at `http://localhost:8080` | Local static UI only |
| `npm run content -- --topic "..."` | Generate a deterministic, no-API content plan | Local generator |
| `npm run signal -- path/to/candles.json` | Validate candles and emit a paper HOLD decision | Paper-only; strategy is a placeholder |
| `npm run whatsapp` | Start the reviewed WhatsApp control-channel skeleton | Requires optional local dependency and auth review |
| `npm run webkit:copy -- --client demo` | Copy the webkit starter into `clients/demo` | Local file operation; placeholders remain |
| `npm run check` | Run syntax and help smoke checks | No network calls |

Use `--help` on every CLI before using it:

```bash
python3 content/daily_content_plan.py --help
node trading/paper_signal.js --help
node whatsapp/index.js --help
python3 scripts/copy_webkit.py --help
```

## Dashboard

The dashboard is a dependency-free static page:

```bash
npm run dashboard
# then visit http://localhost:8080
```

Its seven core cards and specialist cards describe roles and local controls. `LOCAL ONLY`, `PAPER`, `MANUAL REVIEW`, and `PLACEHOLDER` are capability labels, not evidence that a service is connected. The command bar records a local response in the page only; it does not execute shell commands.

## WhatsApp skeleton

`whatsapp/index.js` is a non-production control-channel outline. `--help` works without installing Baileys. Starting it requires the optional package in `whatsapp/package.json`, a deliberate local QR login, and a review of the message allow-list. It is not an order router.

## Webkit client copies

The webkit utility copies starter assets without inventing client details:

```bash
python3 scripts/copy_webkit.py --client demo
python3 scripts/copy_webkit.py --client acme --output-dir ./clients --force
```

Replace visible placeholders and verify links, prices, hours, consent, and contact details before publishing.

## What this does not do

This repository does not provide live trading, broker execution, financial advice, a market-data entitlement, a production WhatsApp bot, or verified business information. Treat missing, stale, or failed checks as blockers rather than filling the gap with assumptions.
