#!/bin/sh
# Install the local Kyla Quant schedule. Run from any directory.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-$(command -v python3 || true)}
if [ -z "$PYTHON" ]; then
  echo "python3 is required" >&2
  exit 1
fi
mkdir -p "$ROOT/logs" "$ROOT/journal"

# Prefer an existing n8n installation; its workflows are the authoritative scheduler.
N8N=$(command -v n8n || true)
if [ -n "$N8N" ]; then
  echo "n8n found: $N8N"
  "$N8N" --version 2>/dev/null || true
  if command -v pgrep >/dev/null 2>&1 && pgrep -f '[n]8n' >/dev/null 2>&1; then
    echo "n8n already running"
  else
    (cd "$ROOT" && nohup "$N8N" start >>"$ROOT/logs/n8n.log" 2>&1 & echo "started n8n pid=$!")
  fi
  echo "schedules: n8n workflows (nightly backtest, 15-minute paper trader, Sunday report)"
  exit 0
fi

echo "n8n not found; installing a local scheduler fallback"

install_launchd() {
  AGENTS="$HOME/Library/LaunchAgents"
  mkdir -p "$AGENTS"
  cat >"$AGENTS/com.kyla.quant.backtest.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.kyla.quant.backtest</string>
<key>WorkingDirectory</key><string>$ROOT</string>
<key>ProgramArguments</key><array><string>/bin/sh</string><string>-lc</string><string>cd "$ROOT" &amp;&amp; "$PYTHON" scripts/run_sol_backtest.py &gt;&gt;"$ROOT/logs/backtest.log" 2&gt;&amp;1</string></array>
<key>StartCalendarInterval</key><dict><key>Hour</key><integer>22</integer><key>Minute</key><integer>0</integer></dict>
<key>StandardOutPath</key><string>$ROOT/logs/backtest.launchd.log</string>
<key>StandardErrorPath</key><string>$ROOT/logs/backtest.launchd.err</string>
</dict></plist>
EOF
  cat >"$AGENTS/com.kyla.quant.paper.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.kyla.quant.paper</string>
<key>WorkingDirectory</key><string>$ROOT</string>
<key>ProgramArguments</key><array><string>/bin/sh</string><string>-lc</string><string>cd "$ROOT" &amp;&amp; "$PYTHON" scripts/paper_trader.py --once --killcheck &gt;&gt;"$ROOT/logs/paper.log" 2&gt;&amp;1</string></array>
<key>StartCalendarInterval</key><dict>
<key>Minute</key><array><integer>0</integer><integer>15</integer><integer>30</integer><integer>45</integer></array>
<key>Hour</key><array><integer>9</integer><integer>10</integer><integer>11</integer><integer>12</integer><integer>13</integer><integer>14</integer><integer>15</integer><integer>16</integer></array>
</dict>
<key>StandardOutPath</key><string>$ROOT/logs/paper.launchd.log</string>
<key>StandardErrorPath</key><string>$ROOT/logs/paper.launchd.err</string>
</dict></plist>
EOF
  cat >"$AGENTS/com.kyla.quant.report.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.kyla.quant.report</string>
<key>WorkingDirectory</key><string>$ROOT</string>
<key>ProgramArguments</key><array><string>/bin/sh</string><string>-lc</string><string>cd "$ROOT" &amp;&amp; "$PYTHON" scripts/trade_journal.py --db journal/trades.db report &gt;&gt;"$ROOT/logs/report.log" 2&gt;&amp;1</string></array>
<key>StartCalendarInterval</key><dict><key>Weekday</key><integer>0</integer><key>Hour</key><integer>18</integer><key>Minute</key><integer>0</integer></dict>
<key>StandardOutPath</key><string>$ROOT/logs/report.launchd.log</string>
<key>StandardErrorPath</key><string>$ROOT/logs/report.launchd.err</string>
</dict></plist>
EOF
  for plist in "$AGENTS"/com.kyla.quant.backtest.plist "$AGENTS"/com.kyla.quant.paper.plist "$AGENTS"/com.kyla.quant.report.plist; do
    launchctl unload "$plist" >/dev/null 2>&1 || true
    launchctl load "$plist"
  done
  echo "scheduler=launchd"
  echo "22:00 daily  backtest"
  echo "09:00-16:00 every 15 minutes  paper trader (--killcheck)"
  echo "Sunday 18:00  journal report"
}

install_cron() {
  MARK="# kyla-quant autopilot"
  EXISTING=$(crontab -l 2>/dev/null || true)
  CLEAN=$(printf '%s\n' "$EXISTING" | grep -v 'kyla-quant autopilot' || true)
  {
    printf '%s\n' "$CLEAN"
    printf '0 22 * * * cd "%s" && "%s" scripts/run_sol_backtest.py >>"%s/logs/backtest.log" 2>&1 %s\n' "$ROOT" "$PYTHON" "$ROOT" "$MARK"
    printf '*/15 9-16 * * * cd "%s" && "%s" scripts/paper_trader.py --once --killcheck >>"%s/logs/paper.log" 2>&1 %s\n' "$ROOT" "$PYTHON" "$ROOT" "$MARK"
    printf '0 18 * * 0 cd "%s" && "%s" scripts/trade_journal.py --db journal/trades.db report >>"%s/logs/report.log" 2>&1 %s\n' "$ROOT" "$PYTHON" "$ROOT" "$MARK"
  } | crontab -
  echo "scheduler=cron"
  echo "22:00 daily  backtest"
  echo "09:00-16:00 every 15 minutes  paper trader (--killcheck)"
  echo "Sunday 18:00  journal report"
}

if [ "$(uname -s)" = "Darwin" ] && command -v launchctl >/dev/null 2>&1; then
  install_launchd
elif command -v crontab >/dev/null 2>&1; then
  install_cron
else
  echo "No launchd or crontab available; print-only schedule:" >&2
  echo "0 22 * * * backtest" >&2
  echo "*/15 9-16 * * * paper trader" >&2
  echo "0 18 * * 0 journal report" >&2
  exit 1
fi
