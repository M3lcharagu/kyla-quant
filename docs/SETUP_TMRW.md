# KYLA: exact 10-minute install order for tomorrow

This is a concise **target order**, not a claim that these commands have been run or that any service is connected. It assumes macOS Catalina, Homebrew, a network connection, and a terminal using zsh or bash. The repository remains research/paper-only; do not use these steps to enable live trading.

## 0:00–1:00 — 1. Install Multipass

```bash
brew install --cask multipass
```

**Optional VM:** only if Linux isolation is needed, launch a VM after installation with `multipass launch --name kyla-quant-vm 20.04`. Otherwise, keep working in the macOS checkout.

## 1:00–2:00 — 2. Install VS Code

```bash
brew install --cask visual-studio-code
```

**Optional alternative:** use the official VS Code `.dmg` installer instead of Homebrew; do not install both.

## 2:00–3:00 — 3. Install a compatible Node.js

The project requests Node 18+ and npm 9+. On Catalina, nvm keeps the Node version explicit:

```bash
brew install nvm
mkdir -p "$HOME/.nvm"
export NVM_DIR="$HOME/.nvm"
. "$(brew --prefix nvm)/nvm.sh"
nvm install 18
nvm use 18
node --version
npm --version
```

**Optional alternative:** if Node 18 is already managed on the Mac, use that instead; `node --version` must be 18 or newer and `npm --version` must be 9 or newer. Add the nvm lines to `~/.zshrc` later if you want them loaded in every terminal; do not append shell configuration blindly.

## 3:00–4:00 — 4. Clone the repository

```bash
cd ~
git clone https://github.com/M3lcharagu/kyla-quant.git
cd kyla-quant
```

**Optional alternative for an existing checkout:** `cd ~/kyla-quant && git pull --ff-only origin main`.

## 4:00–5:00 — 5. Install project dependencies

```bash
npm install
(cd whatsapp && npm install)
```

The second command installs the WhatsApp prototype's nested dependencies; it does not connect the bot or create a public service.

## 5:00–6:00 — 6. Install Claude Code and log in

```bash
npm install -g @anthropic-ai/claude-code
claude
```

Complete the browser login with the applicable Claude/Anthropic account when prompted. Use a ChatGPT account only in a separate ChatGPT workflow where that account applies. Do not put credentials or API keys in chat or GitHub.

## 6:00–7:00 — 7. Test the dashboard

In one terminal:

```bash
cd ~/kyla-quant
npm run dashboard
```

In another terminal or via macOS:

```bash
open http://localhost:8080
```

The expected check is a local static dashboard page. Stop the server with `Ctrl-C` when finished.

## 7:00–8:00 — 8. Test the WhatsApp bot

```bash
cd ~/kyla-quant
npm run whatsapp
```

**QR/auth caveat:** on a first run, scan the QR code only from the intended phone and keep the generated `whatsapp/auth_info_baileys/` session directory private. QR codes and session material are account access; never share, log, commit, or paste them. The prototype is non-production and not a guarantee of WhatsApp compatibility. Stop it with `Ctrl-C` after the local smoke check.

## 8:00–9:00 — 9. Test the paper trading scan

Provide a local JSON file containing an array of candles with numeric `time`, `open`, `high`, `low`, and `close` fields (volume is optional), then run:

```bash
cd ~/kyla-quant
npm run signal -- /absolute/path/to/candles.json
```

This must remain **paper-only**: the result is a proposal/hold decision and must not place live orders. Do not treat it as financial advice or evidence of future performance.

## 9:00–10:00 — 10. Verify `.env` safely

Create `.env` locally only if the API path is needed; copy the committed template, edit it privately, and never commit the result:

```bash
cd ~/kyla-quant
cp .env.example .env
# Edit .env locally; do not paste the real value into chat or GitHub.
test -f .env && grep -q '^ANTHROPIC_API_KEY=.' .env && echo ".env has a value"
git check-ignore -q .env && echo ".env is ignored"
git status --short --ignored .env .env.example
```

The commands above intentionally print status only, not the key. If a real key has been exposed, stop and revoke/rotate it at [console.anthropic.com](https://console.anthropic.com/).

## Before any promotion

Read and complete the **R13 review** in [`docs/R13_QA_GATE.md`](R13_QA_GATE.md). Keep the system in sandbox/paper mode, require human approval, and do not connect live brokerage or exchange execution as part of this install.
