# 7am handoff on macOS Catalina

This is an exact, human-led sequence for a minimal/free-tier setup. It does not claim that any service, QR session, package manager, launchd job, or browser is already installed. Keep the Mac awake for local jobs, and use separate Terminal windows where a long-running process blocks the next command.

## Sequence

1. **Install Multipass.** Use the official Multipass macOS installer from Canonical, then verify:

   ```bash
   multipass version
   ```

   If Homebrew is already installed and its Catalina-compatible formula is available, `brew install --cask multipass` is an alternative; do not install Homebrew solely for this run without reviewing compatibility.

2. **Install VS Code.** Download the macOS build from the official Visual Studio Code site, open it, optionally install the `code` shell command, then verify:

   ```bash
   code --version
   ```

   If `code` is not on PATH, open the repository from the VS Code application instead; do not invent a download URL.

3. **Install Node.** Use the official Node.js macOS installer for a Node version satisfying this repository’s `package.json` (`>=18`), then verify:

   ```bash
   node --version
   npm --version
   ```

   On Catalina, prefer a Node release that still supports Catalina and the machine’s CPU. If the official installer does not offer one, stop and choose a documented compatible release rather than silently using an unverified package manager.

4. **Clone the repo.**

   ```bash
   git clone https://github.com/M3lcharagu/kyla-quant.git
   cd kyla-quant
   git checkout main
   ```

5. **Install Node dependencies.**

   ```bash
   npm install
   ```

   This installs the minimal declared Playwright dependency. Browser binaries are a separate download and are not required for dashboard/content/paper-signal work. Install only after reviewing Playwright’s official Catalina support:

   ```bash
   npx playwright install chromium
   ```

6. **Boot the dashboard** in Terminal window A:

   ```bash
   npm run dashboard
   ```

   Review `http://localhost:8080` locally. Stop with `Ctrl-C`; this server is static and local.

7. **Boot the WhatsApp bot** in Terminal window B only after explicit human opt-in:

   ```bash
   npm run whatsapp
   ```

   Baileys may display a QR code and create local auth state under `whatsapp/auth_info_baileys/`. Scan only with the intended account, do not commit that directory, and stop if the device/session or message allow-list is not understood. This is a non-production skeleton, not a connected service or order router.

8. **Run the first content plan** in Terminal window C:

   ```bash
   npm run content -- --topic "build log" --topic "one practical trading lesson" --count 4
   ```

   Save or review the JSON output manually. It does not publish, call an API, or prove audience facts.

9. **Run the first paper trading scan** with a real, reviewed local candle file:

   ```bash
   npm run signal -- path/to/reviewed-candles.json
   ```

   The file must be a JSON array with numeric `time`, `open`, `high`, `low`, and `close` fields. The command validates and emits a paper-only decision; it does not place an order. Do not fabricate candles, returns, or backtest results.

## 7am checkpoint

Record local date/time, input source timestamps, command output locations, and failures. Run the R13 QA/security/legal review in `docs/R13_QA_GATE.md` before release, publication, account action, deployment, or any change toward live trading. Keep browser work and WhatsApp disabled unless separately approved. Trading stays paper-only.
