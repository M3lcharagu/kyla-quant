# Catalina automation for Kyla Quant

This guide targets Mel's 13-inch Mid-2012 MacBook Pro running macOS Catalina with 2 GB RAM. The workflows are deliberately small: they run one command, retain stdout, and send that text to a user-supplied webhook. They never contain credentials.

## One-time setup

Use Node 18, the last practical Node line for this Catalina machine:

```sh
nvm install 18
nvm use 18
node --version
npm --version
npm install -g n8n@0.229.0
n8n --version
```

`n8n@0.229.0` is intentionally pinned to the 0.x line and is compatible with Node 18. If npm reports an issue on a particular Node 18 patch release, use the nearest maintained 0.x release in the same series, not n8n latest.

Clone this repository at `~/kyla-quant` (or change the `cd "$HOME/kyla-quant"` prefix in each workflow after importing):

```sh
cd "$HOME/kyla-quant"
mkdir -p logs journal
python3 -m py_compile scripts/paper_trader.py
```

## Start n8n on Catalina

Keep n8n lightweight: use its default local process, not a database or queue worker:

```sh
export N8N_USER_FOLDER="$HOME/.n8n-kyla"
mkdir -p "$N8N_USER_FOLDER"
caffeinate -dimsu n8n start
```

`caffeinate` prevents idle sleep while n8n is in the foreground. Keep that Terminal window open, or run the command inside `tmux`/`screen`. Do not expose n8n publicly. `YOUR_WEBHOOK_URL` is only a placeholder until Mel supplies a private Discord or Telegram webhook.

## Import and configure workflows

1. Open `http://localhost:5678` while `n8n start` is running.
2. Import each JSON in `automation/n8n/workflows/` with **Workflows → Import from File**.
3. In each imported workflow, replace the HTTP Request URL `YOUR_WEBHOOK_URL` with Mel's webhook. Never commit that URL.
4. Confirm Execute Command runs from `~/kyla-quant`; change only the `cd "$HOME/kyla-quant"` prefix if needed.
5. Use **Execute Workflow** once for a dry run, then activate it. Cron uses the Mac's local timezone.

Schedules are: nightly strategy-factory backtest at 22:00, paper signal watcher every 15 minutes from 09:00 through 16:00, and journal report Sunday at 18:00. n8n must remain running for Cron triggers.

## Lightweight fallback: plain cron

If n8n is too heavy, run the repository-root helper once. It installs the same schedules and prints what it started:

```sh
cd "$HOME/kyla-quant"
./scripts/autopilot.sh
```

It uses only `python3`, `crontab`, and the standard library. Output goes to `logs/`. Inspect or remove entries with `crontab -l` and `crontab -e`. The paper watcher includes `--killcheck`; an armed local or remote kill switch causes a safe exit without a simulated trade.

## launchd fallback

If `crontab` is unavailable, `scripts/autopilot.sh` writes three LaunchAgents under `~/Library/LaunchAgents/` and loads them with `launchctl`. The paper agent wakes every 900 seconds but gates execution to local hours 09:00–16:00. Nightly and Sunday jobs use `StartCalendarInterval`.

Stop those agents with:

```sh
for p in "$HOME"/Library/LaunchAgents/com.mel.kyla-quant.*.plist; do launchctl unload -w "$p" 2>/dev/null || true; done
```

Keep the Mac on power, disable automatic sleep while plugged in, and use `pmset -g assertions` to verify `caffeinate`. These workflows never place live orders and need no Binance API keys.
